import argparse
import sys

import can
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from src.component.baudrate_selector import BaudrateSelector
from src.component.can_message_editor import CanMessageEditor
from src.component.channel_selector import ChannelSelector
from src.component.communication_controller import CommunicationController
from src.component.logbox import LogBox
from src.utils.can_handler import CANHandler


class MainWindow(QMainWindow):
    radix_change_signal = Signal(str)
    log_signal = Signal(str, str)
    can_log_signal = Signal(can.Message)
    can_connect_status_signal = Signal(bool)

    def __init__(self, can_type, initial_radix_type="dec"):
        super().__init__()
        self.radix_type = initial_radix_type
        self.can_type = can_type

        self.setWindowTitle(f"CANViewer | {self.can_type} | {self.radix_type}")
        self.setGeometry(100, 100, 800, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.holizontal_layout = QHBoxLayout()
        self.holizontal_layout.addLayout(self.layout, 800)
        self.central_widget.setLayout(self.holizontal_layout)

        # Components
        self.can_handler = CANHandler()
        self.channel_selector = ChannelSelector(can_type=self.can_type)
        self.can_message_editor = CanMessageEditor()
        self.baudrate_selector = BaudrateSelector()
        self.communication_controller = CommunicationController()
        self.log_box = LogBox()

        self.layout.addWidget(self.channel_selector)
        self.layout.addWidget(self.can_message_editor)
        self.layout.addWidget(self.log_box)

        # Bottom Layout
        self.layout_bottom = QHBoxLayout()
        self.layout_bottom.addWidget(self.baudrate_selector)
        self.layout_bottom.addWidget(self.communication_controller)
        self.layout.addLayout(self.layout_bottom)

        # Signal Connection
        self.log_signal.connect(self.log_box.log)
        self.can_log_signal.connect(self.log_box.can_msg_log)
        self.can_connect_status_signal.connect(
            self.channel_selector.can_connection_change_callback
        )
        ###############################################
        self.communication_controller.send_msg_signal.connect(self.send_msg)
        self.communication_controller.log_signal.connect(self.log)
        self.communication_controller.log_clear_signal.connect(self.log_box.clear)
        ###############################################
        self.channel_selector.channel_signal.connect(
            self.toggle_can_interface_connection
        )

    @Slot()
    def send_msg(self):
        msg: can.Message = self.can_message_editor.get_message()
        self.can_log_signal.emit(msg)

    @Slot(str, str)
    def log(self, text: str, color: str = None):
        self.log_signal.emit(text, color)

    def toggle_can_interface_connection(self, channel: str):
        if self.can_handler.get_connect_status() == False:
            bps: int = self.baudrate_selector.get_baudrate()
            self.can_handler.connect_device(channel, bps, self.can_type)
            # set status
            self.baudrate_selector.set_disable()
            self.can_connect_status_signal.emit(True)
            self.log(f"Connected to {channel} : {bps} bps", color="green")
        else:
            self.can_handler.disconnect_devive()
            # set status
            self.baudrate_selector.set_enable()
            self.can_connect_status_signal.emit(False)
            self.log("Disconnected", color="green")


def main():
    parser = argparse.ArgumentParser(
        prog="CAN Send and Receive App",
        usage="python main.py [options]",
        epilog="end",  # ヘルプの後に表示
        add_help=True,  # -h/–-helpオプションの追加
    )

    parser.add_argument(
        "-c", "--can", type=str, default="slcan", help="CAN type (socketcan, slcan)"
    )
    args = parser.parse_args()

    print("CAN Type:", args.can)
    app = QApplication(sys.argv)
    window = MainWindow(args.can, "dec")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
