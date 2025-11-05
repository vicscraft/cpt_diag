# PLC Data Logger and Web Visualizer

## Description

This project is a Python application that monitors a Siemens S7 PLC, logs data to a MySQL database, and provides a web interface to visualize the logged data.

## Features

- Monitors a specific bit on a Siemens S7 PLC to trigger logging of a Box ID and Barcode.
- Monitors 32 separate bits to trigger time-series data logging for 32 different boxes.
- Logs 4 float data points (power, voltage, temperature1, temperature2) at a 1-second interval for a configurable duration (default 3 minutes).
- Handles concurrent data logging for multiple boxes using threading.
- Web interface to search and view logged data.
- Plot visualization of time-series data.
- Export plotted data to CSV.

## Project Structure

```
.cpt_diag/
├── venv/                   # Python virtual environment
├── static/
│   └── style.css           # CSS for web application
├── templates/
│   ├── index.html          # Main page of the web application
│   └── plot.html             # Page for displaying the data plot
├── app.py                  # Flask web application
├── config.json             # Configuration file
├── database.py             # Database connection and table creation
├── logger.py               # Data logging functions
├── main.py                 # Main PLC monitoring script
├── plc_monitor.py          # PLC interaction module
├── requirements.txt        # Python dependencies
└── README.md               # This instruction manual
```

## Setup and Installation

1.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```

2.  **Activate the virtual environment:**

    -   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure `config.json`:**

    Open the `config.json` file and edit the following settings to match your environment:

    -   `PLC`: PLC IP address, rack, slot, and DB addresses.
    -   `DATABASE`: MySQL host, user, password, and database name.
    -   `LOGGING`: Duration and interval for data logging.

5.  **Set up MySQL Database:**

    -   Make sure you have a MySQL server running.
    -   Create a new database with the name you specified in `config.json`.
    -   The necessary tables (`box_log` and `data_log`) will be created automatically when you run the `main.py` script for the first time.

## Usage

### PLC Monitoring and Logging

To start the PLC monitoring and data logging script, run the following command:

```bash
python main.py
```

This will connect to the PLC and start monitoring for the trigger bits. When a trigger is detected, it will log the corresponding data to the MySQL database.

### Web Application

To start the web application, run the following command:

```bash
python app.py
```

This will start a local web server. Open your web browser and navigate to `http://127.0.0.1:5000` to access the application.

#### Searching for Barcodes

You can search for barcodes using the following criteria:

-   **Barcode Pattern:** Search for barcodes that contain a specific string.
-   **Box ID:** Filter by a specific Box ID.
-   **Date Range:** Select a start and end date to filter the results.

#### Viewing Data Plots

After searching, a list of matching barcodes will be displayed. Click the "Show Data" link next to a barcode to view a plot of the time-series data associated with that box and time.

#### Exporting Data to CSV

On the plot page, click the "Export to CSV" link to download the plotted data as a CSV file.
