from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget
from serial.tools.list_ports import comports

GsUsb: Any = None
try:
    from gs_usb.gs_usb import GsUsb as _GsUsb  # type: ignore[import-untyped]
except ImportError:
    pass
else:
    GsUsb = _GsUsb


@dataclass(frozen=True)
class CanChannel:
    interface: str
    channel: str | int
    label: str


SLCAN_EXCLUDED_KEYWORDS = (
    "BLUETOOTH",
    "DEBUG-CONSOLE",
)

SLCAN_INCLUDED_KEYWORDS = (
    "CAN",
    "USB2CAN",
    "CANABLE",
    "CANDLELIGHT",
)


def _get_gs_usb_device_label(index: int, device: Any) -> str:
    usb_device = getattr(device, "usb_device", None) or getattr(device, "gs_usb", None)
    manufacturer = getattr(usb_device, "manufacturer", None)
    product = getattr(usb_device, "product", None)
    serial_number = getattr(device, "serial_number", None)
    description = " ".join(
        str(value) for value in [manufacturer, product, serial_number] if value
    )
    return f"{index}: {description}" if description else str(index)


def _is_slcan_candidate(port_info: Any) -> bool:
    text = f"{port_info.device} {port_info.description} {port_info.hwid}".upper()
    if any(keyword in text for keyword in SLCAN_EXCLUDED_KEYWORDS):
        return False
    return any(keyword in text for keyword in SLCAN_INCLUDED_KEYWORDS)


def _discover_slcan_channels() -> list[CanChannel]:
    channels: list[CanChannel] = []
    port_infos = sorted(
        (port_info for port_info in comports() if _is_slcan_candidate(port_info)),
        key=lambda port_info: (
            "CAN" not in f"{port_info.description} {port_info.hwid}".upper(),
            port_info.device,
        ),
    )
    for port_info in port_infos:
        port = port_info.device
        desc = port_info.description
        label = f"SLCAN - {port}"
        if desc:
            label = f"{label} ({desc})"
        channels.append(CanChannel(interface="slcan", channel=port, label=label))
    return channels


def _discover_gs_usb_channels() -> list[CanChannel]:
    if GsUsb is None:
        print("gs_usb is not installed")
        return []

    channels: list[CanChannel] = []
    try:
        devices = GsUsb.scan()
    except Exception as error:
        print(f"gs_usb scan failed: {error}")
        return []

    for index, device in enumerate(devices):
        device_label = _get_gs_usb_device_label(index, device)
        channels.append(
            CanChannel(
                interface="gs_usb",
                channel=index,
                label=f"gs_usb - {device_label}",
            )
        )
    return channels


def _discover_socketcan_channels() -> list[CanChannel]:
    net_dir = Path("/sys/class/net")
    if not net_dir.exists():
        return []

    channels: list[CanChannel] = []
    for net_device in sorted(net_dir.iterdir()):
        name = net_device.name
        if name.startswith(("can", "vcan")):
            channels.append(
                CanChannel(
                    interface="socketcan",
                    channel=name,
                    label=f"SocketCAN - {name}",
                )
            )
    return channels


class ChannelSelector(QWidget):
    channel_signal = Signal(str, str, bool)
    mode_signal = Signal(bool)

    def __init__(self, parent=None, preferred_interface="slcan"):
        super().__init__(parent)

        self._preferred_interface = preferred_interface

        # main layout
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # Channel selection list layout
        self._list_layout = QHBoxLayout()
        self._list_layout.addWidget(QLabel("Port"))
        self._channel_combobox = QComboBox()
        self._channel_combobox.currentIndexChanged.connect(
            self._on_channel_selection_changed
        )
        self._list_layout.addWidget(self._channel_combobox)
        self._list_layout.addWidget(QLabel("Mode"))
        self._mode_combobox = QComboBox()
        self._mode_combobox.addItems(["CAN", "CAN-FD"])
        self._mode_combobox.currentIndexChanged.connect(self._emit_mode_changed)
        self._list_layout.addWidget(self._mode_combobox)
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
        self._emit_mode_changed()

    @Slot(bool)
    def can_connection_change_callback(self, connected: bool) -> None:
        if connected:
            self.connection_complete()
        else:
            self.disconnection_complete()

    def connection_complete(self) -> None:
        self._connect_button.setText("Disconnect")
        self._channel_combobox.setEnabled(False)
        self._mode_combobox.setEnabled(False)
        self._refresh_button.setEnabled(False)

    def disconnection_complete(self) -> None:
        self._connect_button.setText("Connect")
        self._channel_combobox.setEnabled(True)
        self._mode_combobox.setEnabled(True)
        self._refresh_button.setEnabled(True)
        self._update_connect_button_enabled()
        self._update_mode_availability()

    @Slot()
    def _refresh(self) -> None:
        self._channel_combobox.clear()
        channels = [
            *_discover_slcan_channels(),
            *_discover_gs_usb_channels(),
            *_discover_socketcan_channels(),
        ]
        preferred_index = -1
        for index, channel in enumerate(channels):
            print(f" {index}: {channel.label}")
            self._channel_combobox.addItem(channel.label, channel)
            if (
                preferred_index < 0
                and channel.interface == self._preferred_interface
            ):
                preferred_index = index

        if preferred_index >= 0:
            self._channel_combobox.setCurrentIndex(preferred_index)

        self._update_connect_button_enabled()

    def _update_connect_button_enabled(self) -> None:
        if self._connect_button.text() == "Disconnect":
            self._connect_button.setEnabled(True)
            return

        self._connect_button.setEnabled(self._channel_combobox.count() > 0)

    @Slot()
    def _on_connect_button_clicked(self) -> None:
        selected = self._channel_combobox.currentData()
        if not isinstance(selected, CanChannel):
            return
        self.channel_signal.emit(
            str(selected.channel), selected.interface, self._is_can_fd()
        )

    def _is_can_fd(self) -> bool:
        return self._mode_combobox.currentText() == "CAN-FD"

    @Slot()
    def _emit_mode_changed(self) -> None:
        self.mode_signal.emit(self._is_can_fd())

    @Slot()
    def _on_channel_selection_changed(self) -> None:
        self._update_mode_availability()

    def _update_mode_availability(self) -> None:
        selected = self._channel_combobox.currentData()
        can_fd_available = not (
            isinstance(selected, CanChannel) and selected.interface == "gs_usb"
        )
        if not can_fd_available:
            self._mode_combobox.setCurrentText("CAN")
        self._mode_combobox.setEnabled(can_fd_available)
        self._emit_mode_changed()
