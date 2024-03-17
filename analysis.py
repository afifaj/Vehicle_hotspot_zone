# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 17:08:16 2024

@author: zzajaferi
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
import logging
from Preprocess_data import prep_main
logging.basicConfig(filename='vehicle_analytics.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
df= prep_main()
df=df.drop_duplicates(subset=['Device ID','IST'])
correlation = df['FuelLevel'].corr(df['EngineCoolantTemp'])
df=df[(df['EngineCoolantTemp'] > 80) & (df['EngineSpeed'] > 0)]

def categorize_temp(temp):
    if temp <= 85:
        return 'Normal'
    elif temp <= 95:
        return 'Heated'
    else:
        return 'Overheated'

df['TemperatureStatus'] = df['EngineCoolantTemp'].apply(categorize_temp)
def check_unhealthy_engine(engine_speed, coolant_temp):
    if engine_speed > 1200 and coolant_temp > 95:
        return 'Unhealthy Engine'
    else:
        return 'Healthy Engine'

df['EngineHealth'] = df.apply(lambda row: check_unhealthy_engine(row['EngineSpeed'], row['EngineCoolantTemp']), axis=1)

logging.info(f"Categorizing data :{ df.shape}")

#df.to_csv("D:/vehicle_hot/category.csv")
#%%

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

def detect_anomalies(df, ambient_temp_col='AmbientTemp', coolant_temp_col='EngineCoolantTemp', timestamp_col='IST', split_ratio=0.8):
    
    X = df[[ambient_temp_col]]
    y = df[coolant_temp_col]
    
    split_idx = int(len(df) * split_ratio)
    X_train, X_test, y_train, y_test = X[:split_idx], X[split_idx:], y[:split_idx], y[split_idx:]
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    residuals = y_test - y_pred
    
    threshold = np.percentile(abs(residuals), 95)
    
    
    anomalies = X_test[abs(residuals) > threshold]
    
    anomaly_timestamps = df.loc[anomalies.index, timestamp_col]
    print("Anomaly Timestamps:")
    logging.info(f"Anomaly Timestamps : {anomaly_timestamps}")

    print(anomaly_timestamps)
    
    return anomaly_timestamps.reset_index()


anomaly_times = detect_anomalies(df)

#%%
#Accury and prediction of Healthy and Unhealthy convert FP to TP
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

def update_engine_health_with_false_negatives(df):
    X = df[['EngineSpeed', 'EngineCoolantTemp', 'VehicleSpeed']]
    y = df['EngineHealth'].apply(lambda x: 1 if x == 'Unhealthy Engine' else 0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LogisticRegression(max_iter=1000)  # Increased max_iter for convergence
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred)
    
    logging.info(f"Accuracy: {accuracy}")
    logging.info(f"Confusion Matrix:\n{conf_matrix}")
    
    y_pred_series = pd.Series(y_pred, index=X_test.index, name='PredictedHealth')
    y_test_series = y_test.rename('TrueHealth')
    combined = pd.concat([y_test_series, y_pred_series], axis=1)
    false_negatives = combined[(combined['TrueHealth'] == 1) & (combined['PredictedHealth'] == 0)].index
    df.loc[false_negatives, 'EngineHealth'] = 'Unhealthy Engine'
    
    return df
updated_df = update_engine_health_with_false_negatives(df)

#%%
def peak_heating_hours(df, temperature_status_col='TemperatureStatus', device_id_col='Device ID', timestamp_col='IST', engine_coolant_temp_col='EngineCoolantTemp'):
    
    df_heated = df[df[temperature_status_col] == 'Normal']
    df_heated[timestamp_col] = pd.to_datetime(df_heated[timestamp_col])

    grouped = df_heated.groupby([device_id_col, df_heated[timestamp_col].dt.hour]).agg(
        Min_EngineCoolantTemp=(engine_coolant_temp_col, 'min'),
        Count=(engine_coolant_temp_col, 'count')
    ).reset_index()
    
   
    peak_hours_heated = grouped.loc[grouped.groupby(device_id_col)['Count'].idxmax()]
    
    peak_hours_heated['Hour_Range'] = peak_hours_heated[timestamp_col].apply(lambda x: f"{x:02d}-{x+1:02d}")
    df_peak_heating_hours = peak_hours_heated[[device_id_col, 'Hour_Range']].drop_duplicates()
    df_merged = pd.merge(df, df_peak_heating_hours, on=device_id_col, how='left')
    
    df_merged['Peak_Driving_Hours'] = df_merged['Hour_Range']
    df_merged.drop('Hour_Range', axis=1, inplace=True)
    
    return df_merged
df_updated = peak_heating_hours(df)
logging.info(f"Peak Maps")
#%%
result = df.groupby(['Device ID', 'TemperatureStatus']).size().unstack(fill_value=0)
result['Total'] = result.sum(axis=1)
res = result.divide(result['Total'], axis=0) * 100
res.drop(columns=['Total'], inplace=True)