import serial
import threading

class SerialHandler:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.serial = serial.Serial()

    def start_reading(self, callback):
        self.serial.port = self.port
        self.serial.baudrate = self.baudrate
        self.serial.open()

        def read_serial():
            while True:
                data = self.serial.readline().decode().strip()
                callback(data)

        thread = threading.Thread(target=read_serial, daemon=True)
        thread.start()

    def stop_reading(self):
        self.serial.close()
