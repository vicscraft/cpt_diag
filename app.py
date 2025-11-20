from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from io import StringIO
import mysql.connector
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/", response_class=HTMLResponse)
async def index_get(request: Request):
    barcodes = []
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    end_date_inclusive = end_date + ' 23:59:59'
    query = "SELECT * FROM box_log WHERE timestamp >= %s AND timestamp <= %s"
    cursor.execute(query, (start_date, end_date_inclusive))
    barcodes = cursor.fetchall()
    cursor.close()
    conn.close()

    return templates.TemplateResponse("index.html", {"request": request, "barcodes": barcodes, "barcode_pattern": "", "box_id": "", "start_date": start_date, "end_date": end_date})

@app.post("/", response_class=HTMLResponse)
async def index_post(request: Request, barcode_pattern: str = Form(""), box_id: str = Form(""), start_date: str = Form(""), end_date: str = Form("")):
    barcodes = []

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
        end_date_inclusive = end_date + ' 23:59:59'
        query += " AND timestamp <= %s"
        params.append(end_date_inclusive)

    cursor.execute(query, tuple(params))
    barcodes = cursor.fetchall()
    cursor.close()
    conn.close()

    return templates.TemplateResponse("index.html", {"request": request, "barcodes": barcodes, "barcode_pattern": barcode_pattern, "box_id": box_id, "start_date": start_date, "end_date": end_date})

@app.get("/plot/{box_id}/{timestamp_str}", response_class=HTMLResponse)
async def plot(request: Request, box_id: int, timestamp_str: str):
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        timestamp = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')

    config = read_config()
    log_start = int(config['LOGGING']['START_QUERY'])
    log_end = int(config['LOGGING']['END_QUERY'])

    start_time = timestamp + timedelta(seconds=log_start)
    end_time = timestamp + timedelta(seconds=log_end)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch barcode for the title
    barcode_query = "SELECT barcode FROM box_log WHERE box_id = %s AND timestamp = %s"
    cursor.execute(barcode_query, (box_id, timestamp))
    barcode_result = cursor.fetchone()
    barcode_value = barcode_result['barcode'] if barcode_result else f"Box ID {box_id}"

    query = "SELECT * FROM data_log WHERE box_id = %s AND timestamp BETWEEN %s AND %s"
    cursor.execute(query, (box_id, start_time, end_time))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        return "No data found for this selection."

    df = pd.DataFrame(data)

    fig = px.line(df, x='timestamp', y=['power', 'voltage', 'temperature1', 'temperature2'], title=f'Barcode: [{barcode_value}]')

    custom_labels = {
        'power': 'Power (W)',
        'voltage': 'Voltage (V)',
        'temperature1': 'Temp 1 (°C)',
        'temperature2': 'Temp 2 (°C)'
    }

    fig.for_each_trace(lambda t: t.update(name=custom_labels.get(t.name, t.name)))

    plot_html = fig.to_html(full_html=False)

    return templates.TemplateResponse("plot.html", {"request": request, "plot_html": plot_html, "box_id": box_id, "timestamp_str": timestamp_str})

@app.get("/export_csv/{box_id}/{timestamp_str}")
async def export_csv(box_id: int, timestamp_str: str):
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        timestamp = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')

    config = read_config()
    log_start = int(config['LOGGING']['START_QUERY'])
    log_end = int(config['LOGGING']['END_QUERY'])

    start_time = timestamp + timedelta(seconds=log_start)
    end_time = timestamp + timedelta(seconds=log_end)

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
    
    return FileResponse(
        content=si.getvalue().encode(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=box_{box_id}_data.csv"}
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)