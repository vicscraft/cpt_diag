import mysql.connector
from mysql.connector import Error

def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

def create_tables(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS box_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            box_id INT,
            barcode VARCHAR(16),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            box_id INT,
            value1 FLOAT,
            value2 FLOAT,
            value3 FLOAT,
            value4 FLOAT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Tables created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")
