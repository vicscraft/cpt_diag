from mysql.connector import Error

def log_box_data(connection, box_id, barcode):
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO box_log (box_id, barcode) VALUES (%s, %s)", (box_id, barcode))
        connection.commit()
        print(f"Logged box data: {box_id}, {barcode}")
    except Error as e:
        print(f"The error '{e}' occurred")

def log_float_data(connection, box_id, values):
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO data_log (box_id, power, voltage, temperature1, temperature2) VALUES (%s, %s, %s, %s, %s)", (box_id, values[0], values[1], values[2], values[3]))
        connection.commit()
        print(f"Logged float data for box {box_id}")
    except Error as e:
        print(f"The error '{e}' occurred")
