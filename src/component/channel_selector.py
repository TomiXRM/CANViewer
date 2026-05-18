from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget
from serial.tools.list_ports import comports

try:
    from gs_usb.gs_usb import GsUsb  # type: ignore[import-untyped]
except ImportError:
    GsUsb = None


class ChannelSelector(QWidget):

    channel_signal = Signal(str)

    def __init__(self, parent=None, can_type="slcan"):
        super().__init__(parent)

        self._can_type = can_type  # "slcan" or "gs_usb"

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
            for n, port_info in enumerate(sorted(comports()), 1):
                port = port_info.device
                desc = port_info.description
                devid = port_info.hwid
                print(f" {n}: {port:20} {desc} {devid}")
                self._channel_combobox.addItem(port)
                # set CANable device as default
                if "CAN" in desc:
                    self._channel_combobox.setCurrentText(port)

        elif self._can_type == "gs_usb":
            if GsUsb is None:
                print("gs_usb is not installed")
                return

            # List available gs_usb devices by index.
            for index, device in enumerate(GsUsb.scan()):
                product = getattr(device.usb_device, "product", None)
                manufacturer = getattr(device.usb_device, "manufacturer", None)
                description = " ".join(
                    value for value in [manufacturer, product] if value
                )
                label = f"{index}: {description}" if description else str(index)
                print(f" {index}: {label}")
                self._channel_combobox.addItem(label, index)
        else:
            print("Invalid CAN type")

    @Slot()
    def _on_connect_button_clicked(self) -> None:
        channel = self._channel_combobox.currentData()
        if channel is None:
            channel = self._channel_combobox.currentText()
        self.channel_signal.emit(str(channel))
