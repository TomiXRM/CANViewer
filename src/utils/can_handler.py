import gc
import logging
import traceback

import can
import usb.core  # type: ignore[import-untyped]
from gs_usb.gs_usb import GsUsb  # type: ignore[import-untyped]
from PySide6.QtCore import QThread, Signal, Slot
from returns.result import Failure, Result, Success

# CAN error bit definitions based on Linux SocketCAN error frames
# source : https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/include/uapi/linux/can/error.h
CAN_ERR_TX_TIMEOUT = 0x00000001
CAN_ERR_LOSTARB = 0x00000002
CAN_ERR_CRTL = 0x00000004
CAN_ERR_PROT = 0x00000008
CAN_ERR_TRX = 0x00000010
CAN_ERR_ACK = 0x00000020
CAN_ERR_BUSOFF = 0x00000040
CAN_ERR_BUSERROR = 0x00000080
CAN_ERR_RESTARTED = 0x00000100

CAN_ERROR_CLASSES = (
    (CAN_ERR_TX_TIMEOUT, "TX timeout"),
    (CAN_ERR_LOSTARB, "lost arbitration"),
    (CAN_ERR_CRTL, "controller problem"),
    (CAN_ERR_PROT, "protocol violation"),
    (CAN_ERR_TRX, "transceiver status"),
    (CAN_ERR_ACK, "ACK error"),
    (CAN_ERR_BUSOFF, "bus off"),
    (CAN_ERR_BUSERROR, "bus error"),
    (CAN_ERR_RESTARTED, "controller restarted"),
)


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
        raise ValueError(
            f"Cannot find gs_usb device {index}. Devices found: {len(devs)}"
        )
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
        if can_fd and interface == "gs_usb":
            raise ValueError("CAN-FD is not supported for gs_usb channels yet")
        if can_fd and interface == "slcan" and data_bitrate is not None:
            timing = can.BitTimingFd.from_sample_point(
                f_clock=80_000_000,
                nom_bitrate=bitrate,
                nom_sample_point=75.0,
                data_bitrate=data_bitrate,
                data_sample_point=75.0,
            )
            return can.interface.Bus(
                channel=channel,
                receive_own_messages=False,
                interface=interface,
                timing=timing,
            )
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


def _format_can_error_frame(msg: can.Message) -> str:
    error_classes = [
        label
        for error_bit, label in CAN_ERROR_CLASSES
        if msg.arbitration_id & error_bit
    ]
    error_text = ", ".join(error_classes) if error_classes else "unknown CAN error"
    details = [f"CAN error frame: {error_text}"]

    data = list(msg.data) if msg.data is not None else []
    if msg.arbitration_id & CAN_ERR_ACK:
        details.append(
            "no other CAN node acknowledged the transmitted frame; "
            "check bus wiring, termination, bitrate, peer power, and listen-only peers"
        )
    if msg.arbitration_id & CAN_ERR_BUSOFF:
        details.append("controller entered bus-off state")
    if len(data) >= 8 and (msg.arbitration_id & CAN_ERR_CRTL):
        details.append(f"tx error counter={data[6]}, rx error counter={data[7]}")

    return ". ".join(details)


class CANHandler(QThread):
    send_can_signal = Signal(can.Message)
    error_log_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.ignore_ids = []
        self._reported_error_frames: set[tuple[int, tuple[int, ...]]] = set()
        self.can_bus: can.BusABC | None = None
        self.can_notifier: can.Notifier | None = None

    def connect_device(
        self,
        channel: str,
        bitrate: int,
        interface: str,
        can_fd: bool = False,
        data_bitrate: int | None = None,
    ) -> Result[bool, Exception]:
        try:
            if channel == "":
                raise ValueError("No CAN channel is selected")
            if can_fd and interface == "gs_usb":
                raise ValueError("CAN-FD is not supported for gs_usb channels yet")

            bus_channel: str | int = channel
            if interface == "gs_usb":
                bus_channel = int(channel)
                _check_gs_usb_access(bus_channel)

            self.can_bus = _create_can_bus(
                bus_channel, bitrate, interface, can_fd, data_bitrate
            )
            self._reported_error_frames.clear()
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
        self._reported_error_frames.clear()

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
        if msg.is_error_frame:
            data = list(msg.data) if msg.data is not None else []
            detail_without_counters = tuple(data[:6])
            error_key = (msg.arbitration_id, detail_without_counters)
            if error_key not in self._reported_error_frames:
                self._reported_error_frames.add(error_key)
                self.error_log_signal.emit(_format_can_error_frame(msg), "red")
            return
        if msg.arbitration_id in self.ignore_ids:
            return
        self.send_can_signal.emit(msg)

    @Slot()
    def update_ignore_ids(self, ignore_ids: list[int]) -> None:
        self.ignore_ids = ignore_ids
