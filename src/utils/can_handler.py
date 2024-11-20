from datetime import datetime

import can
from PySide6.QtCore import QThread, QTimer, Signal


class CANHandler(QThread):
    send_can_signal = Signal(can.Message)
    can_bus = None
    can_notifier = None

    def __init__(self):
        super().__init__()
        self.ignore_ids = []
        self.pro_interface = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ignore_ids)

    def connect_device(self, port, bps, interface):  # Connect and start receiving
        try:
            self.can_bus = can.interface.Bus(
                channel=port,
                bitrate=bps,
                receive_own_messages=False,
                interface=interface,
            )
            self.can_notifier = can.Notifier(self.can_bus, [self.can_on_recieve])
        except Exception as e:
            print(e)
            self.can_bus = None

    def disconnect_devive(self):  # Disconnect and stop receiving
        self.can_notifier.stop()
        self.can_bus.shutdown()
        self.can_bus = None

    def get_connect_status(self):
        if self.can_bus is None:
            return False
        else:
            return True

    def can_send(self, msg: can.Message):
        msg.timestamp = datetime.now()
        msg.is_rx = False
        self.can_bus.send(msg)

    def can_on_recieve(self, msg: can.Message):
        msg.is_rx = True
        if msg.arbitration_id in self.ignore_ids:
            return
        msg.timestamp = datetime.now()
        self.send_can_signal.emit(msg)

    def update_ignore_ids(self):
        if self.pro_interface:
            self.ignore_ids = self.pro_interface.ignore_ids

    def clear_ignore_ids(self):
        self.ignore_ids = []

    def set_pro_interface(self, pro_interface):
        self.pro_interface = pro_interface
        self.timer.start(250)
