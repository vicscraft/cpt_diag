import snap7
from snap7.util import *

class PLCMonitor:
    def __init__(self, ip_address, rack, slot):
        self.client = snap7.client.Client()
        self.ip_address = ip_address
        self.rack = rack
        self.slot = slot

    def connect(self):
        try:
            self.client.connect(self.ip_address, self.rack, self.slot)
            print("Connected to PLC")
            return True
        except Exception as e:
            print(f"Error connecting to PLC: {e}")
            return False

    def disconnect(self):
        self.client.disconnect()
        print("Disconnected from PLC")

    def is_connected(self):
        return self.client.get_connected()

    def read_trigger_bit(self, db_number, offset, bit):
        try:
            data = self.client.db_read(db_number, offset, 1)
            return get_bool(data, 0, bit)
        except Exception as e:
            print(f"Error reading trigger bit: {e}")
            return None

    def read_box_id(self, db_number, offset):
        try:
            data = self.client.db_read(db_number, offset, 2)
            return get_int(data, 0)
        except Exception as e:
            print(f"Error reading box id: {e}")
            return None

    def read_barcode(self, db_number, offset):
        try:
            data = self.client.db_read(db_number, offset, 16)
            return data.decode('UTF-8').strip('\x00')
        except Exception as e:
            print(f"Error reading barcode: {e}")
            return None

    def read_data_trigger_bits(self, db_number, offset):
        try:
            data = self.client.db_read(db_number, offset, 4)
            return unpack_word(data)
        except Exception as e:
            print(f"Error reading data trigger bits: {e}")
            return None

    def read_float_data(self, db_number, offset):
        try:
            data = self.client.db_read(db_number, offset, 16)
            values = []
            for i in range(4):
                values.append(get_real(data, i * 4))
            return values
        except Exception as e:
            print(f"Error reading float data: {e}")
            return None
    def write_bit(self, db_number, offset, bit, value):
        try:
            data = self.client.db_read(db_number, offset, 1)
            set_bool(data, 0, bit, value)
            self.client.db_write(db_number, offset, data)
            print(f"Wrote {value} to DB{db_number}, byte {offset}, bit {bit}")
        except Exception as e:
            print(f"Error writing bit: {e}")


def unpack_word(byte_array):
    bits = []
    for byte in byte_array:
        for i in range(8):
            bits.append((byte >> i) & 1)
    return bits
