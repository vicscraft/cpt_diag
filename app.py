from flask import Flask, render_template, request, redirect, url_for, make_response
from io import StringIO
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime, timedelta

app = Flask(__name__)

def read_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

def get_db_connection():
    config = read_config()
    db_host = config['DATABASE']['HOST']
    db_user = config['DATABASE']['USER']
    db_password = config['DATABASE']['PASSWORD']
    db_name = config['DATABASE']['DATABASE']
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_password,
        database=db_name
    )
    return connection

@app.route('/', methods=['GET', 'POST'])
def index():
    barcodes = []
    if request.method == 'POST':
        barcode_pattern = request.form.get('barcode_pattern', '')
        box_id = request.form.get('box_id', '')
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM box_log WHERE 1=1"
        params = []

        if barcode_pattern:
            query += " AND barcode LIKE %s"
            params.append(f"%{barcode_pattern}%")
        if box_id:
            query += " AND box_id = %s"
            params.append(box_id)
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)

        cursor.execute(query, tuple(params))
        barcodes = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('index.html', barcodes=barcodes)

@app.route('/plot/<int:box_id>/<string:timestamp_str>')
def plot(box_id, timestamp_str):
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        # Handle cases where the timestamp might have a different format or is invalid
        # For example, if it includes milliseconds
        timestamp = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')


    config = read_config()
    log_duration = int(config['LOGGING']['DURATION'])

    start_time = timestamp - timedelta(seconds=log_duration/2)
    end_time = timestamp + timedelta(seconds=log_duration/2)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM data_log WHERE box_id = %s AND timestamp BETWEEN %s AND %s"
    cursor.execute(query, (box_id, start_time, end_time))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        return "No data found for this selection."

    df = pd.DataFrame(data)

    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['value1'], label='Value 1')
    plt.plot(df['timestamp'], df['value2'], label='Value 2')
    plt.plot(df['timestamp'], df['value3'], label='Value 3')
    plt.plot(df['timestamp'], df['value4'], label='Value 4')
    plt.xlabel('Timestamp')
    plt.ylabel('Value')
    plt.title(f'Data Log for Box ID {box_id}')
    plt.legend()
    plt.grid(True)

    plot_path = f'static/plot_{box_id}_{timestamp.strftime("%Y%m%d%H%M%S")}.png'
    plt.savefig(plot_path)
    plt.close()

    return render_template('plot.html', plot_url=plot_path, box_id=box_id, timestamp_str=timestamp_str)

@app.route('/export_csv/<int:box_id>/<string:timestamp_str>')
def export_csv(box_id, timestamp_str):
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        timestamp = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')

    config = read_config()
    log_duration = int(config['LOGGING']['DURATION'])

    start_time = timestamp - timedelta(seconds=log_duration/2)
    end_time = timestamp + timedelta(seconds=log_duration/2)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM data_log WHERE box_id = %s AND timestamp BETWEEN %s AND %s"
    cursor.execute(query, (box_id, start_time, end_time))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        return "No data found for this selection."

    df = pd.DataFrame(data)
    
    # Create a string buffer for the CSV data
    si = StringIO()
    df.to_csv(si, index=False)
    
    # Create a response with the CSV data
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=box_{box_id}_data.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

if __name__ == '__main__':
    app.run(debug=True)
