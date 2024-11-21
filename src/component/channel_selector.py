import os

import serial.tools.list_ports
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton,
                               QWidget)


class ChannelSelector(QWidget):

    channel_signal = Signal(str)

    def __init__(self, parent=None, can_type="slcan"):
        super().__init__(parent)

        self._can_type = can_type  # "socketcan" or "slcan"

        # main layout
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # Channel selection list layout
        self._list_layout = QHBoxLayout()
        self._list_layout.addWidget(QLabel("Port"))
        self._channel_combobox = QComboBox()
        self._list_layout.addWidget(self._channel_combobox)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._list_layout)

        # Connection and Refresh button layout
        # Connect button
        self._connect_button = QPushButton("Connect")
        self._connect_button.clicked.connect(self._on_connect_button_clicked)
        self._layout.addWidget(self._connect_button)
        # Refresh button
        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self._refresh)
        self._layout.addWidget(self._refresh_button)

        self._refresh()

    @Slot(bool)
    def can_connection_change_callback(self, connected: bool) -> None:
        if connected:
            self.connection_complete()
        else:
            self.disconnection_complete()

    def connection_complete(self) -> None:
        self._connect_button.setText("Disconnect")

    def disconnection_complete(self) -> None:
        self._connect_button.setText("Connect")

    @Slot()
    def _refresh(self) -> None:
        self._channel_combobox.clear()
        if self._can_type == "slcan":
            # List available ports
            for n, (port, desc, devid) in enumerate(
                sorted(serial.tools.list_ports.comports()), 1
            ):
                print(f" {n}: {port:20} {desc} {devid}")
                self._channel_combobox.addItem(port)
                # set CANable device as default
                if "CANable" in desc:
                    self._channel_combobox.setCurrentText(port)

        elif self._can_type == "socketcan":
            # List available interfaces
            output: str = os.popen(
                "ip link show"
            ).read()  # Get the list of network interfaces(SocketCAN)
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
                self._channel_combobox.addItem(interface)
        else:
            print("Invalid CAN type")

    @Slot()
    def _on_connect_button_clicked(self) -> None:
        self.channel_signal.emit(self._channel_combobox.currentText())
