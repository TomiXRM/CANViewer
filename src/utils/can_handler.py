import gc
import logging
import traceback

import can
import usb.core
from gs_usb.gs_usb import GsUsb
from PySide6.QtCore import QThread, Signal, Slot
from returns.result import Result, Success, Failure


def _format_connection_error(error: Exception, interface: str) -> Exception:
    if (
        interface == "gs_usb"
        and isinstance(error, usb.core.USBError)
        and getattr(error, "errno", None) == 13
    ):
        return PermissionError(
            "Access denied opening gs_usb device. On macOS, grant libusb access "
            "by running CANViewer with sufficient USB permissions, for example "
            "`sudo uv run main.py -c gs_usb`, then reconnect the adapter if needed."
        )
    return error


def _check_gs_usb_access(index: int) -> None:
    devs = GsUsb.scan()
    if len(devs) <= index:
        raise ValueError(f"Cannot find gs_usb device {index}. Devices found: {len(devs)}")
    _ = devs[index].device_capability


def _create_can_bus(
    channel: str | int,
    bitrate: int,
    interface: str,
    can_fd: bool = False,
    data_bitrate: int | None = None,
) -> can.BusABC:
    can_bus_logger = logging.getLogger("can.bus")
    previous_disabled = can_bus_logger.disabled
    if interface == "gs_usb":
        can_bus_logger.disabled = True

    try:
        if can_fd and interface == "socketcan":
            if data_bitrate is not None:
                return can.interface.Bus(
                    channel=channel,
                    bitrate=bitrate,
                    receive_own_messages=False,
                    interface=interface,
                    fd=True,
                    data_bitrate=data_bitrate,
                )
            return can.interface.Bus(
                channel=channel,
                bitrate=bitrate,
                receive_own_messages=False,
                interface=interface,
                fd=True,
            )
        return can.interface.Bus(
            channel=channel,
            bitrate=bitrate,
            receive_own_messages=False,
            interface=interface,
        )
    except Exception as error:
        if interface == "gs_usb":
            traceback.clear_frames(error.__traceback__)
            error.__traceback__ = None
            gc.collect()
        raise error from None
    finally:
        can_bus_logger.disabled = previous_disabled


class CANHandler(QThread):
    send_can_signal = Signal(can.Message)

    def __init__(self):
        super().__init__()
        self.ignore_ids = []
        self.can_bus: can.BusABC | None = None
        self.can_notifier: can.Notifier | None = None

    def connect_device(
        self,
        channel: str,
        bps: int,
        interface: str,
        can_fd: bool = False,
        data_bps: int | None = None,
    ) -> Result[bool, Exception]:
        try:
            if channel == "":
                raise ValueError("No CAN channel is selected")

            bus_channel: str | int = channel
            if interface == "gs_usb":
                bus_channel = int(channel)
                _check_gs_usb_access(bus_channel)

            self.can_bus = _create_can_bus(
                bus_channel, bps, interface, can_fd, data_bps
            )
            self.can_notifier = can.Notifier(self.can_bus, [self._on_can_recieve])
            return Success(True)
        except Exception as e:
            e = _format_connection_error(e, interface)
            print(e)
            self.can_bus = None
            return Failure(e)

    def disconnect_devive(self) -> None:
        if self.can_notifier is not None:
            self.can_notifier.stop()
        if self.can_bus is not None:
            self.can_bus.shutdown()
        self.can_notifier = None
        self.can_bus = None

    def get_connect_status(self) -> bool:
        if self.can_bus is None:
            return False
        else:
            return True

    def can_send(self, msg: can.Message) -> None:
        if self.can_bus is None:
            return
        msg.is_rx = False
        self.can_bus.send(msg)

    def _on_can_recieve(self, msg: can.Message) -> None:
        msg.is_rx = True
        if msg.arbitration_id in self.ignore_ids:
            return
        self.send_can_signal.emit(msg)

    @Slot()
    def update_ignore_ids(self, ignore_ids: list[int]) -> None:
        self.ignore_ids = ignore_ids
