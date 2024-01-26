import tkinter as tk
from tkinter import ttk
import serial
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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

        self.figure, self.ax = plt.subplots(3, 1, figsize=(8, 6))

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
        self.stop_record_button["state"] = "disabled"  

        self.connection_manager = ConnectionManager(root, self)

        self.gesture_var = tk.StringVar()
        self.gesture_dropdown = ttk.Combobox(root, textvariable=self.gesture_var, state="readonly", values=gestures)
        self.gesture_dropdown.set("Select Gesture")
        self.gesture_dropdown.pack(side=tk.LEFT, padx=10)

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
        self.record_count += 1

    def record_to_csv(self):
        if self.gesture_var.get() != "Select Gesture" and self.is_recording:
            filename = f"{self.gesture_var.get()}_data_{self.record_count}.csv"
            with open(filename, mode='a', newline='') as file:  
                writer = csv.writer(file)

                if file.tell() == 0:
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

                rolls = [entry.get('roll', 0) for entry in latest_data]
                pitches = [entry.get('pitch', 0) for entry in latest_data]
                yaws = [entry.get('yaw', 0) for entry in latest_data]

                self.ax[0].cla()
                self.ax[1].cla()
                self.ax[2].cla()

                self.ax[0].plot(rolls, label='Roll')
                self.ax[1].plot(pitches, label='Pitch')
                self.ax[2].plot(yaws, label='Yaw')

                self.ax[0].set_ylabel('Roll')
                self.ax[1].set_ylabel('Pitch')
                self.ax[2].set_ylabel('Yaw')

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
    datas = ["acx", "acy", "acz", "gx", "gy", "gz", "roll", "pitch", "yaw", "label"]
    gestures = ['pitch_down', 'pitch_up', 'roll_right', 'roll_left', 'yaw_right', 'yaw_left', 'stop']

    root = tk.Tk()
    app = App(root)
    root.mainloop()


#datas = ["acx1", "acy1", "acz1", "gx1", "gy1", "gz1", "roll1", "pitch1", "yaw1", "acx2", "acy2", "acz2", "gx2", "gy2", "gz2", "roll2", "pitch2", "yaw2", "label"]
    
'''

acx1:7.1  acy1:49.1  acz1:23.1  gx1:0.8  gy1:0.0  gz1:0.2  roll1:-156  pitch1:8  yaw1:143 acx2:7.1  acy2:49.1  acz2:23.1  gx2:0.8  gy2:0.0  gz2:0.2  roll2:-156  pitch2:8  yaw2:143
acx1:7.1  acy1:49.1  acz1:23.1  gx1:0.8  gy1:0.0  gz1:0.2  roll1:-156  pitch1:8  yaw1:143 acx2:7.1  acy2:49.1  acz2:23.1  gx2:0.8  gy2:0.0  gz2:0.2  roll2:-156  pitch2:8  yaw2:143
acx1:7.1  acy1:49.1  acz1:23.1  gx1:0.8  gy1:0.0  gz1:0.2  roll1:-156  pitch1:8  yaw1:143 acx2:7.1  acy2:49.1  acz2:23.1  gx2:0.8  gy2:0.0  gz2:0.2  roll2:-156  pitch2:8  yaw2:143
acx1:7.1  acy1:49.1  acz1:23.1  gx1:0.8  gy1:0.0  gz1:0.2  roll1:-156  pitch1:8  yaw1:143 acx2:7.1  acy2:49.1  acz2:23.1  gx2:0.8  gy2:0.0  gz2:0.2  roll2:-156  pitch2:8  yaw2:143
acx1:7.1  acy1:49.1  acz1:23.1  gx1:0.8  gy1:0.0  gz1:0.2  roll1:-156  pitch1:8  yaw1:143 acx2:7.1  acy2:49.1  acz2:23.1  gx2:0.8  gy2:0.0  gz2:0.2  roll2:-156  pitch2:8  yaw2:143

'''