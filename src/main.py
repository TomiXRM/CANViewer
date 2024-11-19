
import argparse
import sys

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                               QVBoxLayout, QWidget)

from can_handler import CANHandler
from component.baudrate_selector import BaudrateSelector
from component.can_message_editor import CanMessageEditor
from component.interface_selector import InterfaceSelector
from component.logbox import LogBox


class MainWindow(QMainWindow):
    radix_change_signal = Signal(str)

    def __init__(self, can_type, initial_radix_type='dec'):
        super().__init__()
        self.radix_type = initial_radix_type

        self.setWindowTitle(f"CANViewer | {can_type} | {self.radix_type}")
        self.setGeometry(100, 100, 800, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.holizontal_layout = QHBoxLayout()
        self.holizontal_layout.addLayout(self.layout, 800)
        self.central_widget.setLayout(self.holizontal_layout)

        # components
        can_handler = CANHandler()
        interface_selector = InterfaceSelector()
        can_message_editor = CanMessageEditor()
        baudrate_selector = BaudrateSelector()
        log_box = LogBox()

        self.layout.addWidget(interface_selector)
        self.layout.addWidget(can_message_editor)
        self.layout.addWidget(log_box)
        self.layout.addWidget(baudrate_selector)


def main():
    parser = argparse.ArgumentParser(
        prog="CAN Send and Receive App",
        usage="python main.py [options]",
        epilog="end",  # ヘルプの後に表示
        add_help=True,  # -h/–-helpオプションの追加
    )

    parser.add_argument("-c", "--can", type=str, default="slcan", help="CAN type (socketcan, slcan)")
    args = parser.parse_args()

    print("CAN Type:", args.can)
    app = QApplication(sys.argv)
    window = MainWindow(args.can, 'dec')
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()