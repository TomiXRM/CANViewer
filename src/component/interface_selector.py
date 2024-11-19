import os

import serial.tools.list_ports
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)


class InterfaceSelector(QWidget):

    bps_signal = Signal(str)

    def __init__(self, parent=None, can_type="slcan", can_handler=None, baudrate_selector=None):
        super().__init__(parent)

        self._can_type = can_type  # "socketcan" or "slcan"
        self._can_handler = can_handler  # CANHandler instance
        self._baudrate_selector = baudrate_selector

        # main layout
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # Interface selection list layout
        self._list_layout = QHBoxLayout()
        self._list_layout.addWidget(QLabel("Port"))
        self._interface_combobox = QComboBox()
        self._list_layout.addWidget(self._interface_combobox)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._list_layout)

        # Connection and Refresh button layout
        # Connect button
        self._connect_button = QPushButton("Connect")
        self._connect_button.clicked.connect(self.connect)
        self._layout.addWidget(self._connect_button)
        # Refresh button
        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self.refresh)
        self._layout.addWidget(self._refresh_button)

        self.refresh()

    def refresh(self):
        self._interface_combobox.clear()
        if self._can_type == "slcan":
            # List available ports
            for n, (port, desc, devid) in enumerate(
                sorted(serial.tools.list_ports.comports()), 1
            ):
                print(f" {n}: {port:20} {desc} {devid}")
                self._interface_combobox.addItem(port)
                # set CANable device as default
                if "CANable" in desc:
                    self._interface_combobox.setCurrentText(port)

        elif self._can_type == "socketcan":
            # List available interfaces
            output: str = os.popen("ip link show").read()  # Get the list of network interfaces(SocketCAN)
            can_interfaces = []
            lines = output.splitlines()

            # Extract the interface name from the output into the list
            for n, line in enumerate(lines):
                if "link/can" in line:
                    previous_line = lines[n - 1]
                    interface_name = previous_line.split(":")[1].strip()
                    can_interfaces.append(interface_name)
                    print(f" {n}: {interface_name}")

            for interface in can_interfaces:
                self._interface_combobox.addItem(interface)
        else:
            print("Invalid CAN type")

    def toggle_connection(self):
        if self._can_handler.get_connect_status() == False:
            port: str = self._interface_combobox.currentText()
            try:
                bps: int = self._baudrate_selector.get_value()
                self._can_handler.connect_device(port, bps, self._can_type)
                self._baudrate_selector.set_enabled(False)
                self.log(f"Connected to {port} : {bps} bps", color="green")
                self.connect_button.setText("Disconnect")
            except Exception as e:
                self.log("Failed to connect: {}".format(e), color="red")
        else:
            self._can_handler.disconnect_devive()
            self.log("Disconnected", color="green")
            self.connect_button.setText("Connect")
            self._baudrate_selector.set_enabled(True)
        pass

    def get_status(self):
        pass

    def set_can_type(self, can_type):
        self.can_type = can_type
