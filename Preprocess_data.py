# -*- coding: utf-8 -*-
"""
Created on Sun Mar 17 06:51:39 2024

@author: zzajaferi
"""

import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(filename='vehicle_data_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data(filepath):
    try:
        df = pd.read_csv(filepath)
        logging.info(f"Data loaded successfully from {filepath}")
        return df
    except Exception as e:n
        logging.error(f"Failed to load data from {filepath}: {e}")
        raise

def convert_utc_to_ist(utc_timestamp):
    try:
        god_time = "2000-01-01 00:00:00"
        god_time_datetime = datetime.strptime(god_time, '%Y-%m-%d %H:%M:%S')
        ist_datetime = god_time_datetime + pd.to_timedelta(utc_timestamp, unit='s') + timedelta(hours=5, minutes=30)
        return ist_datetime
    except Exception as e:
        logging.error(f"Failed to convert UTC to IST: {e}")
        raise

def preprocess_data(df):
    try:
        df['IST'] = df['UTC'].apply(convert_utc_to_ist)
        df['EngineCoolantTemp'] = pd.to_numeric(df['EngineCoolantTemp'])
        df_80 = df[(df['EngineCoolantTemp'] > 80) & (df['EngineSpeed'] > 0)]
        logging.info("Preprocessing completed.")
        return df_80
    except Exception as e:
        logging.error(f"Error during preprocessing: {e}")
        raise

def merge_with_zone_data(df_80, zone_filepath):
    try:
        zone_df = load_data(zone_filepath)
        merged_df = df_80.merge(zone_df, on=['State'], how='left')
        logging.info("Merged with zone data.")
        return merged_df
    except Exception as e:
        logging.error(f"Failed to merge with zone data: {e}")
        raise

def preprocess_dataframe(df):
    df = df[['Device ID', 'Latitude', 'Longitude', 'UTC', 'TotalDistance', 'EngineSpeed', 'VehicleSpeed',
             'FuelLevel', 'EngineCoolantTemp', 'IST', 'State', 'District', 'Region']]

    tmp = pd.read_csv('D:/vehicle_hot/statetemp.csv')
    df = df.merge(tmp, on='State', how='left')

    df['High_temp'] = df['High_temp'].fillna(method='bfill')

    state_temperatures = {
        'West Bengal': 43, 'Uttarakhand': 34, 'Uttar Pradesh': 45, 'Tripura': 32, 'Telangana': 37,
        'Tamil Nadu': 36, 'Sikkim': 29, 'Rajasthan': 50, 'Punjab': 45, 'Puducherry': 39, 'Odisha': 46,
        'Nagaland': 40, 'Mizoram': 36, 'Meghalaya': 33, 'Manipur': 36, 'Maharashtra': 46, 'Madhya Pradesh': 49,
        'Lakshadweep': 33, 'Kerala': 41, 'Karnataka': 45, 'Jharkhand': 46, 'Jammu & Kashmir': 35, 'Himachal Pradesh': 29,
        'Haryana': 44, 'Goa': 39, 'Delhi': 47, 'Chhattisgarh': 49, 'Chandigarh': 45, 'Bihar': 45, 'Assam': 39,
        'Arunanchal Pradesh': 35, 'Andhra Pradesh': 48, 'Andaman & Nicobar Island': 32, 'Gujarat': 49
    }
    df['High_temp'] = df['High_temp'].fillna(df['State'].map(state_temperatures))

    df['IST'] = pd.to_datetime(df['IST'])

    df.sort_values('Timestamp', inplace=True)

    return df

df_processed = preprocess_dataframe(df_80)

def prep_main():
    logging.info("Starting data processing...")
    data_filepath = 'D:/vehicle_hot/data.csv'
    zone_filepath = 'D:/vehicle_hot/zone.csv'
    
    df = load_data(data_filepath)
    df.columns = ['Device ID', 'Latitude', 'Longitude', 'UTC', 'TotalDistance', 'EngineSpeed', 'VehicleSpeed', 'FuelLevel', 'EngineCoolantTemp', 'IST', 'State', 'District', 'Region']
    df_80 = preprocess_data(df)
    merged_df = merge_with_zone_data(df_80, zone_filepath)
    df_processed = preprocess_dataframe(merged_df)
    df_processed.to_csv(outpath+"preprocess_data.csv")
    

    logging.info("Data processing completed.")
    return df_processed
