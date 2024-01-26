import threading
from serial.tools import list_ports

class DataHandler:
    def __init__(self):
        self.data = []
        self.lock = threading.Lock()

    def add_data(self, data):
        entry = self.parse_data(data)
        with self.lock:
            self.data.append(entry)

    def get_data(self):
        with self.lock:
            return self.data[-50:] 

    def parse_data(self, data):
        try:
            entries = data.split()
            entry_dict = {}
            for entry in entries:
                key, value = entry.split(":")
                entry_dict[key] = float(value)
            return entry_dict
        except ValueError as e:
            print(f"Error parsing data: {e}")
            return {}

    def reset_data(self):
        with self.lock:
            self.data = []