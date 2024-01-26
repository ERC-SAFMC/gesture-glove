import tkinter as tk
from tkinter import ttk
import serial
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from serial.tools import list_ports
import os

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

class App:
    def __init__(self, root):
        self.root = root
        self.data_handler = DataHandler()
        self.serial_connection = None
        self.is_running = False
        self.is_paused = False
        self.is_recording = False
        self.record_count = 1
        self.thread = None  
        
        self.figure, self.ax = plt.subplots(3, 2, figsize=(12, 6))

        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.start_button = tk.Button(root, text="Start", command=self.start_data_collection)
        self.start_button.pack(side=tk.LEFT, padx=10)
        self.pause_button = tk.Button(root, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=10)
        self.reset_button = tk.Button(root, text="Reset", command=self.reset_data)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        self.stop_button = tk.Button(root, text="Stop", command=self.stop_data_collection)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.record_button = tk.Button(root, text="Record to CSV", command=self.toggle_record)
        self.record_button.pack(side=tk.LEFT, padx=10)

        self.stop_record_button = tk.Button(root, text="Stop Record", command=self.stop_record)
        self.stop_record_button.pack(side=tk.LEFT, padx=10)
        self.stop_record_button["state"] = "disabled"  # Initially disable the Stop Record button

        self.connection_manager = ConnectionManager(root, self)

        self.gesture_var = tk.StringVar()
        self.gesture_dropdown = ttk.Combobox(root, textvariable=self.gesture_var, state="readonly", values=gestures)
        self.gesture_dropdown.set("Select Gesture")
        self.gesture_dropdown.pack(side=tk.LEFT, padx=10)

        self.new_csv_var = tk.IntVar()
        self.new_csv_checkbox = tk.Checkbutton(root, text="New CSV", variable=self.new_csv_var)
        self.new_csv_checkbox.pack(side=tk.LEFT, padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_data_collection(self):
        if not self.is_running:
            if self.connection_manager.selected_port and self.connection_manager.selected_baudrate:
                self.serial_connection = serial.Serial(self.connection_manager.selected_port,
                                                       baudrate=self.connection_manager.selected_baudrate,
                                                       timeout=1)
                self.is_running = True
                self.is_paused = False
                self.thread = threading.Thread(target=self.read_serial_data)
                self.thread.daemon = True
                self.thread.start()

    def stop_data_collection(self):
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.serial_connection.close()
            self.thread.join()

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def reset_data(self):
        self.data_handler.reset_data()

    def toggle_record(self):
        if self.gesture_var.get() != "Select Gesture":
            self.is_recording = not self.is_recording
            if self.is_recording:
                self.stop_record_button["state"] = "normal"
                self.record_button["state"] = "disabled"
            else:
                self.stop_record_button["state"] = "disabled"
                self.record_button["state"] = "normal"

    def stop_record(self):
        self.is_recording = False
        self.stop_record_button["state"] = "disabled"
        self.record_button["state"] = "normal"
        if self.new_csv_var.get() == 1:
            self.record_count += 1

    def record_to_csv(self):
        if self.gesture_var.get() != "Select Gesture" and self.is_recording:
            filename = f"logs/{self.gesture_var.get()}_data_{self.record_count}.csv"
            
            file_exists = os.path.exists(filename) and os.path.getsize(filename) > 0

            with open(filename, mode='a', newline='') as file:
                writer = csv.writer(file)

                if not file_exists or self.new_csv_var.get() == 1:
                    writer.writerow(datas)

                for entry in self.data_handler.get_data():
                    row = [entry.get(data, 0) for data in datas[:-1]]  
                    row.append(self.gesture_var.get())
                    writer.writerow(row)

    def on_close(self):
        if self.is_running:
            self.stop_data_collection()
        self.root.destroy()

    def read_serial_data(self):
        while self.is_running:
            try:
                serial_data = self.serial_connection.readline().decode('utf-8').strip()

                if not self.is_paused:
                    self.data_handler.add_data(serial_data)

                latest_data = self.data_handler.get_data()

                rolls1 = [entry.get('roll1', 0) for entry in latest_data]
                pitches1 = [entry.get('pitch1', 0) for entry in latest_data]
                yaws1 = [entry.get('yaw1', 0) for entry in latest_data]

                rolls2 = [entry.get('roll2', 0) for entry in latest_data]
                pitches2 = [entry.get('pitch2', 0) for entry in latest_data]
                yaws2 = [entry.get('yaw2', 0) for entry in latest_data]

                self.ax[0, 0].cla()
                self.ax[1, 0].cla()
                self.ax[2, 0].cla()
                self.ax[0, 1].cla()
                self.ax[1, 1].cla()
                self.ax[2, 1].cla()

                self.ax[0, 0].plot(rolls1, label='Roll1')
                self.ax[1, 0].plot(pitches1, label='Pitch1')
                self.ax[2, 0].plot(yaws1, label='Yaw1')

                self.ax[0, 1].plot(rolls2, label='Roll2')
                self.ax[1, 1].plot(pitches2, label='Pitch2')
                self.ax[2, 1].plot(yaws2, label='Yaw2')

                self.ax[0, 0].set_ylabel('Roll1')
                self.ax[1, 0].set_ylabel('Pitch1')
                self.ax[2, 0].set_ylabel('Yaw1')

                self.ax[0, 1].set_ylabel('Roll2')
                self.ax[1, 1].set_ylabel('Pitch2')
                self.ax[2, 1].set_ylabel('Yaw2')

                self.canvas.draw()
                self.canvas_widget.update()

                if self.is_recording:
                    self.record_to_csv()

            except Exception as e:
                print(f"Error in thread: {e}")


class ConnectionManager:
    def __init__(self, root, app):
        self.app = app
        self.selected_port = None
        self.selected_baudrate = None

        self.frame = tk.Frame(root)
        self.frame.pack()

        self.port_label = tk.Label(self.frame, text="Select Port:")
        self.port_label.pack(side=tk.LEFT, padx=10)
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(self.frame, textvariable=self.port_var, state="readonly")
        self.port_dropdown['values'] = self.get_serial_ports()
        self.port_dropdown.pack(side=tk.LEFT, padx=10)
        self.port_dropdown.bind("<<ComboboxSelected>>", self.update_selected_port)

        self.baudrate_label = tk.Label(self.frame, text="Select Baudrate:")
        self.baudrate_label.pack(side=tk.LEFT, padx=10)
        self.baudrate_var = tk.StringVar()
        self.baudrate_dropdown = ttk.Combobox(self.frame, textvariable=self.baudrate_var, state="readonly")
        self.baudrate_dropdown['values'] = ["9600", "115200"]  # Add more baud rates if needed
        self.baudrate_dropdown.pack(side=tk.LEFT, padx=10)
        self.baudrate_dropdown.bind("<<ComboboxSelected>>", self.update_selected_baudrate)

    def get_serial_ports(self):
        ports = [port.device for port in list_ports.comports()]
        return ports

    def update_selected_port(self, event):
        self.selected_port = self.port_var.get()

    def update_selected_baudrate(self, event):
        self.selected_baudrate = int(self.baudrate_var.get())


if __name__ == "__main__":
    datas = ["acx1", "acy1", "acz1", "gx1", "gy1", "gz1", "roll1", "pitch1", "yaw1",
             "acx2", "acy2", "acz2", "gx2", "gy2", "gz2", "roll2", "pitch2", "yaw2", "label"]
    gestures = ['pitch_down', 'pitch_up', 'roll_right', 'roll_left', 'yaw_right', 'yaw_left', 'stop']

    root = tk.Tk()
    app = App(root)
    root.mainloop()
