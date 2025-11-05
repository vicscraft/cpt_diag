import json
import threading
import time
from database import create_connection, create_tables
from logger import log_box_data, log_float_data
from plc_monitor import PLCMonitor


def read_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

def data_logging_thread(plc_monitor, db_connection, box_id, duration, interval, data_db, data_db_offset):
    print(f"Starting data logging for box {box_id}")
    start_time = time.time()
    while time.time() - start_time < duration:
        values = plc_monitor.read_float_data(data_db, data_db_offset)
        if values:
            log_float_data(db_connection, box_id, values)
        time.sleep(interval)
    print(f"Finished data logging for box {box_id}")

def main():
    config = read_config()

    # PLC settings
    plc_ip = config['PLC']['IP_ADDRESS']
    plc_rack = int(config['PLC']['RACK'])
    plc_slot = int(config['PLC']['SLOT'])
    trigger_db = int(config['PLC']['TRIGGER_DB'])
    trigger_db_offset = int(config['PLC']['TRIGGER_DB_OFFSET'])
    trigger_db_bit = int(config['PLC']['TRIGGER_DB_BIT'])
    box_id_db = int(config['PLC']['BOX_ID_DB'])
    box_id_db_offset = int(config['PLC']['BOX_ID_DB_OFFSET'])
    barcode_db = int(config['PLC']['BARCODE_DB'])
    barcode_db_offset = int(config['PLC']['BARCODE_DB_OFFSET'])
    data_trigger_db = int(config['PLC']['DATA_TRIGGER_DB'])
    data_trigger_db_offset = int(config['PLC']['DATA_TRIGGER_DB_OFFSET'])

    # Database settings
    db_host = config['DATABASE']['HOST']
    db_user = config['DATABASE']['USER']
    db_password = config['DATABASE']['PASSWORD']
    db_name = config['DATABASE']['DATABASE']

    # Logging settings
    log_duration = int(config['LOGGING']['DURATION'])
    log_interval = int(config['LOGGING']['INTERVAL'])

    # Connect to database
    db_connection = create_connection(db_host, db_user, db_password, db_name)
    if db_connection:
        create_tables(db_connection)

    # Connect to PLC
    plc_monitor = PLCMonitor(plc_ip, plc_rack, plc_slot)
    if not plc_monitor.connect():
        return

    active_threads = {}

    try:
        while True:
            # Monitor for box logging trigger
            trigger_bit = plc_monitor.read_trigger_bit(trigger_db, trigger_db_offset, trigger_db_bit)
            if trigger_bit:
                box_id = plc_monitor.read_box_id(box_id_db, box_id_db_offset)
                barcode = plc_monitor.read_barcode(barcode_db, barcode_db_offset)
                if box_id is not None and barcode is not None:
                    log_box_data(db_connection, box_id, barcode)

            # Monitor for data logging triggers
            data_trigger_bits = plc_monitor.read_data_trigger_bits(data_trigger_db, data_trigger_db_offset)
            if data_trigger_bits:
                for i, bit in enumerate(data_trigger_bits):
                    box_id = i + 1
                    if bit and box_id not in active_threads:
                        thread = threading.Thread(target=data_logging_thread, args=(
                            plc_monitor, db_connection, box_id, log_duration, log_interval, data_trigger_db, data_trigger_db_offset + 4 + (i * 16)
                        ))
                        thread.start()
                        active_threads[box_id] = thread
                    elif not bit and box_id in active_threads:
                        active_threads[box_id].join() # Wait for thread to finish
                        del active_threads[box_id]

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        for thread in active_threads.values():
            thread.join()
        if db_connection:
            db_connection.close()
        plc_monitor.disconnect()

if __name__ == "__main__":
    main()
