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

def data_logging_thread(shared_plc_monitor, plc_lock, box_id, duration, interval, plc_db, data_array_db_offset, data_trigger_db_offset, bit_index):
    print(f"Starting data logging for box {box_id}")
    
    # Establish a new database connection for this thread
    config = read_config()
    db_host = config['DATABASE']['HOST']
    db_user = config['DATABASE']['USER']
    db_password = config['DATABASE']['PASSWORD']
    db_name = config['DATABASE']['DATABASE']
    thread_db_connection = create_connection(db_host, db_user, db_password, db_name)
    if not thread_db_connection:
        print(f"Failed to establish DB connection for box {box_id} logging thread.")
        return

    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            with plc_lock:
                values = shared_plc_monitor.read_float_data(plc_db, data_array_db_offset)
            if values:
                log_float_data(thread_db_connection, box_id, values)
            time.sleep(interval)
    finally:
        print(f"Finished data logging for box {box_id}")
        byte_offset = data_trigger_db_offset + (bit_index // 8)
        bit_in_byte = bit_index % 8
        with plc_lock:
            shared_plc_monitor.write_bit(plc_db, byte_offset, bit_in_byte, False)
        if thread_db_connection:
            thread_db_connection.close()

def main():
    config = read_config()

    # PLC settings
    plc_ip = config['PLC']['IP_ADDRESS']
    plc_rack = int(config['PLC']['RACK'])
    plc_slot = int(config['PLC']['SLOT'])
    plc_db = int(config['PLC']['PLC_DB'])
    trigger_db_offset = int(config['PLC']['TRIGGER_DB_OFFSET'])
    trigger_db_bit = int(config['PLC']['TRIGGER_DB_BIT'])
    box_id_db_offset = int(config['PLC']['BOX_ID_DB_OFFSET'])
    barcode_db_offset = int(config['PLC']['BARCODE_DB_OFFSET'])
    data_trigger_db_offset = int(config['PLC']['DATA_TRIGGER_DB_OFFSET'])
    data_array_db_offset = int(config['PLC']['DATA_ARRAY_DB_OFFSET'])

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

    # Initialize shared PLC monitor and lock
    shared_plc_monitor = PLCMonitor(plc_ip, plc_rack, plc_slot)
    plc_lock = threading.Lock()

    # Connect to PLC (initial connection)
    def connect_plc():
        with plc_lock:
            if not shared_plc_monitor.is_connected():
                print("Attempting to connect to PLC...")
                if shared_plc_monitor.connect():
                    print("PLC connected.")
                    return True
                else:
                    print("Failed to connect to PLC.")
                    return False
            return True # Already connected

    if not connect_plc():
        print("Initial PLC connection failed. Exiting.")
        if db_connection:
            db_connection.close()
        return

    active_threads = {}

    try:
        while True:
            # Monitor PLC connection and reconnect if necessary
            if not shared_plc_monitor.is_connected():
                print("PLC connection lost. Attempting to reconnect...")
                if not connect_plc():
                    print("Reconnection failed. Skipping PLC operations.")
                    time.sleep(5) # Wait before retrying
                    continue

            # Monitor for box logging trigger
            with plc_lock:
                trigger_bit = shared_plc_monitor.read_trigger_bit(plc_db, trigger_db_offset, trigger_db_bit)
            if trigger_bit:
                with plc_lock:
                    box_id = shared_plc_monitor.read_box_id(plc_db, box_id_db_offset)
                    barcode = shared_plc_monitor.read_barcode(plc_db, barcode_db_offset)
                if box_id is not None and barcode is not None:
                    log_box_data(db_connection, box_id, barcode)
                    with plc_lock:
                        shared_plc_monitor.write_bit(plc_db, trigger_db_offset, trigger_db_bit, False)

            # Monitor for data logging triggers
            with plc_lock:
                data_trigger_bits = shared_plc_monitor.read_data_trigger_bits(plc_db, data_trigger_db_offset)
            if data_trigger_bits:
                for i, bit in enumerate(data_trigger_bits):
                    box_id = i + 1
                    if bit and box_id not in active_threads:
                        thread = threading.Thread(target=data_logging_thread, args=(
                            shared_plc_monitor, plc_lock, box_id, log_duration, log_interval, plc_db, data_array_db_offset + (i * 16), data_trigger_db_offset, i
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
        with plc_lock:
            shared_plc_monitor.disconnect()

if __name__ == "__main__":
    main()