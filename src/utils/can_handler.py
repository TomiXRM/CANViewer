import can
from PySide6.QtCore import QThread, Signal, Slot


class CANHandler(QThread):
    send_can_signal = Signal(can.Message)

    def __init__(self):
        super().__init__()
        self.ignore_ids = []
        self.can_bus = None
        self.can_notifier = None

    def connect_device(self, channel: str, bps: int, interface: str) -> None:
        try:
            self.can_bus = can.interface.Bus(
                channel=channel,
                bitrate=bps,
                receive_own_messages=False,
                interface=interface,
            )
            self.can_notifier = can.Notifier(self.can_bus, [self._on_can_recieve])
        except Exception as e:
            print(e)
            self.can_bus = None

    def disconnect_devive(self) -> None:
        self.can_notifier.stop()
        self.can_bus.shutdown()
        self.can_bus = None

    def get_connect_status(self) -> bool:
        if self.can_bus is None:
            return False
        else:
            return True

    def can_send(self, msg: can.Message) -> None:
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
