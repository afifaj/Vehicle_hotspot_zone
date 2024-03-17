# -*- coding: utf-8 -*-
"""
Created on Sun Mar 17 08:50:49 2024

@author: zzbchoudhary
"""

import pandas as pd
from flask import Flask, render_template, request, jsonify
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

app = Flask(__name__)

# Set up logging
log_file_path = os.path.join('D:\\', 'Bhavya_data', 'hackhive', 'dashboard', 'app.log')
logging.basicConfig(filename=log_file_path, level=logging.INFO)

try:
   
    csv_file_path = os.path.join('D:\\', 'Bhavya_data', 'hackhive', 'dashboard', 'preprocessed.csv')
    # Read CSV file using pandas
    category_data = pd.read_csv(csv_file_path)
    
  
    category_data['Device ID'] = pd.to_numeric(category_data['Device ID'], errors='coerce')

 
    unique_device_ids = category_data.dropna(subset=['Device ID'])

  
    unique_device_ids = sorted(set(category_data['Device ID']))
except Exception as e:
    logging.error("Error reading CSV file: %s", e)
    category_data = pd.DataFrame()  
    unique_device_ids = [] 


logging.info("Head of the data:\n%s", category_data.head())

def summarize_data(filtered_data):

    total_distance_start = filtered_data.iloc[0]['TotalDistance']
    total_distance_end = filtered_data.iloc[-1]['TotalDistance']
    total_distance_diff = total_distance_start - total_distance_end
    
    avg_engine_coolant_temp = filtered_data['EngineCoolantTemp'].mean()
    
    temperature_status_counts = filtered_data['TemperatureStatus'].value_counts().to_dict()
    engine_health_counts = filtered_data['EngineHealth'].value_counts().to_dict()
    
    peak_heating_hours = filtered_data['Peak_Heating_Hours'].unique()[:5].tolist()
    peak_driving_hours = filtered_data['Peak_Driving_Hours'].unique()[:5].tolist()  

    summary = {
        'TotalDistance Travelled': total_distance_diff,
        'AverageEngineCoolantTemp': avg_engine_coolant_temp,
        'TemperatureStatusCounts': temperature_status_counts,
        'EngineHealthCounts': engine_health_counts,
        'PeakHeatingHours': peak_heating_hours,
        'PeakDrivingHours': peak_driving_hours
    }
    
    return summary


@app.route('/map')
def map():
   
    html_file_path = os.path.join('D:\\', 'Bhavya_data', 'hackhive', 'dashboard', 'static', 'State_choropleth.html')
    try:
        with open(html_file_path, 'r') as file:
            map_content = file.read()
    except Exception as e:
        logging.error("Error reading State_choropleth.html: %s", e)
        map_content = ''  

    return render_template('dashboard.html', title='Vehicle Hotspot Zone', map_content=map_content)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    title = 'Vehicle Hotspot Zone'
    selected_device_id = None
    filtered_data_head = None
    summary = None  
    map_content = None  

   
    html_file_path = os.path.join('D:\\', 'Bhavya_data', 'hackhive', 'dashboard', 'static', 'State_choropleth.html')
    try:
        with open(html_file_path, 'r') as file:
            map_content = file.read()
    except Exception as e:
        logging.error("Error reading State_choropleth.html: %s", e)

    if request.method == 'POST':
        try:
            selected_device_id = int(request.form['device_id'])
            logging.info("Selected Device ID: %s", selected_device_id)

            
            filtered_data = category_data[category_data['Device ID'] == selected_device_id]
            logging.info("Filtered data %s", filtered_data.columns)
            
           
            filtered_data_head = filtered_data.head().to_dict('records')
            
            logging.info("Head of the filtered data for Device ID '%s':\n%s", selected_device_id, filtered_data.head())
            
            output_folder = os.path.join('D:\\', 'Bhavya_data', 'hackhive', 'dashboard', 'outputfolder')
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            output_csv_path = os.path.join(output_folder, f'output.csv')
            filtered_data.to_csv(output_csv_path, index=False)
            logging.info("Filtered data saved to CSV file: %s", output_csv_path)
            
            
            summary = summarize_data(filtered_data)
        except Exception as e:
            logging.error("Error filtering data or saving to CSV file: %s", e)

    return render_template('dashboard.html', title=title, unique_device_ids=unique_device_ids,
                           selected_device_id=selected_device_id, filtered_data_head=filtered_data_head,
                           summary=summary, map_content=map_content)

# =============================================================================
# # Route for the dashboard
# @app.route('/dashboard', methods=['GET', 'POST'])
# def dashboard():
#     title = 'Vehicle Hotspot Zone'
#     selected_device_id = None
#     filtered_data_head = None
#     summary = None  # Initialize summary variable
# 
#     if request.method == 'POST':
#         try:
#             selected_device_id = int(request.form['device_id'])
#             logging.info("Selected Device ID: %s", selected_device_id)
# 
#             # Filter the data for the selected Device ID
#             filtered_data = category_data[category_data['Device ID'] == selected_device_id]
#             logging.info("Filtered data %s", filtered_data.columns)
#             
#             # Get the head of the filtered data
#             filtered_data_head = filtered_data.head().to_dict('records')
#             # Log the head of the filtered data
#             logging.info("Head of the filtered data for Device ID '%s':\n%s", selected_device_id, filtered_data.head())
#             
#             # Save the filtered data to a CSV file
#             output_folder = os.path.join('D:\\', 'Bhavya_data', 'hackhive', 'dashboard', 'outputfolder')
#             if not os.path.exists(output_folder):
#                 os.makedirs(output_folder)
#             output_csv_path = os.path.join(output_folder, f'output.csv')
#             filtered_data.to_csv(output_csv_path, index=False)
#             logging.info("Filtered data saved to CSV file: %s", output_csv_path)
#             
#             # Summarize the filtered data
#             summary = summarize_data(filtered_data)
#         except Exception as e:
#             logging.error("Error filtering data or saving to CSV file: %s", e)
# 
#     return render_template('dashboard.html', title=title, unique_device_ids=unique_device_ids,
#                            selected_device_id=selected_device_id, filtered_data_head=filtered_data_head,
#                            summary=summary)
# =============================================================================

# Route to log the filtered data head
@app.route('/log_filtered_data_head', methods=['POST'])
def log_filtered_data_head():
    try:
        filtered_data_head = request.json['filtered_data_head']
        logging.info("Filtered Data Head:\n%s", filtered_data_head)
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error("Error logging filtered data head: %s", e)
        return jsonify({'status': 'error'})

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    filtered_data = pd.DataFrame(data['filtered_data'])  
    
    if filtered_data.empty:
        return jsonify({'error': 'Filtered data is empty'}), 400
    
    # Calculate summary statistics based on the filtered data
    summary = summarize_data(filtered_data)
    
    return jsonify(summary)

def send_email(subject="VehicleHotSpotZoneAlert", text="", attachments=None):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    if attachments is not None:
        if not isinstance(attachments, list):
            attachments = [attachments]

        for attachment in attachments:
            try:
                with open(attachment, 'rb') as f:
                    file_data = f.read()
                    print("File read successfully")
                file = MIMEApplication(file_data, name=os.path.basename(attachment))
                file['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                msg.attach(file)
            except FileNotFoundError:
                print(f"Warning: File '{attachment}' not found. Skipping attachment.")

    
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()

    
    smtp.login('himani101406@gmail.com', 'unhj jugk mcdb gsys')

    
    to = ["cbhavya103@gmail.com",
          "himani101406@gmail.com", "jafariafifa@gmail.com"]

    
    smtp.sendmail(from_addr="himani101406@gmail.com",
                  to_addrs=to, msg=msg.as_string())

   
    smtp.quit()

if __name__ == '__main__':
    app.run(debug=True)
