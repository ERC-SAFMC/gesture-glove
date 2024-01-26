import tkinter as tk
from tkinter import ttk
from serial.tools import list_ports

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