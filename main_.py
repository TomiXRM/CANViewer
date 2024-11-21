import argparse
import sys

import can
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QAction, QKeySequence, Qt
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                               QVBoxLayout, QWidget)

from src.component.baudrate_selector import BaudrateSelector
from src.component.can_message_editor import CanMessageEditor
from src.component.channel_selector import ChannelSelector
from src.component.communication_controller import CommunicationController
from src.component.logbox import LogBox
from src.utils.can_handler import CANHandler


class MainWindow(QMainWindow):
    radix_status_signal = Signal(str)
    log_signal = Signal(str, str)
    can_log_signal = Signal(can.Message)
    can_connection_status_signal = Signal(bool)

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

        # Set Key-Board Shortcuts
        # Ctrl + D : Change Radix to DEC
        change_radix_to_dec_aciton = QAction("Change Radix to Dec", self)
        change_radix_to_dec_aciton.setShortcuts(
            [QKeySequence(Qt.CTRL | Qt.Key_D), QKeySequence(Qt.CTRL | Qt.Key_F)]
        )
        change_radix_to_dec_aciton.triggered.connect(self._change_radix_to_dec)
        self.addAction(change_radix_to_dec_aciton)

        # Ctrl + H :  Change Radix to HEX
        change_radix_to_hex_aciton = QAction("Change Radix to Hex", self)
        change_radix_to_hex_aciton.setShortcuts(
            [QKeySequence(Qt.CTRL | Qt.Key_H), QKeySequence(Qt.CTRL | Qt.Key_J)]
        )
        change_radix_to_hex_aciton.triggered.connect(self._change_radix_to_hex)
        self.addAction(change_radix_to_hex_aciton)

        # Ctrl + P : Extend Pro Mode
        # TODO: Implement Pro Mode

        # Signal Connection

        # When the Radix changes, notify new radix
        self.radix_status_signal.connect(self.can_message_editor.update_radix)
        self.log_signal.connect(self.log_box.log)  # Send log data to logbox
        # Send CAN-BUS Message to logbox
        self.can_log_signal.connect(self.log_box.can_msg_log)
        # Notify the CAN-BUS connection status to the 'channel_selector'
        self.can_connection_status_signal.connect(self.channel_selector.can_connection_change_callback)
        # Notify the CAN-BUS connection status to the 'communication_controller'
        self.can_connection_status_signal.connect(self.communication_controller.can_connection_change_callback)

        ###############################################
        # Send a Trigger when the 'communication_controller' order to send a message
        self.communication_controller.send_can_msg_trigger_signal.connect(self.send_can_msg)
        # Handle Log data from 'communication_controller'
        self.communication_controller.log_signal.connect(self.log)
        # Clear Log data from 'communication_controller'
        self.communication_controller.log_clear_signal.connect(self.log_box.clear)

        ###############################################
        # Connect/Disconnect CAN-BUS Interface(with receiving 'channel name')
        self.channel_selector.channel_signal.connect(self._toggle_can_interface_connection)

        ###############################################
        # Handle Log data from 'can_message_editor'
        self.can_message_editor.log_signal.connect(self.log)

    @Slot()
    def send_can_msg(self) -> None:
        # Get CAN Message from 'can_message_editor'
        msg: can.Message | None  # msg: can.Message | None
        usable: bool  # message is usable or not
        msg, usable = self.can_message_editor.get_message()

        if usable == False:
            return
        if msg is None:
            return

        try:
            self.can_handler.can_send(msg)  # Send CAN Message
            self.can_log_signal.emit(msg)  # Log CAN Message to logbox
        except can.CanError as e:
            self.log("Failed to send: {}".format(e), color="red")

    # This method handles the logbox. If you want to show log-data on the logbox, you can use this method.
    @Slot(str, str)
    def log(self, text: str, color: str = None) -> None:
        self.log_signal.emit(text, color)

    @Slot(str)
    def _toggle_can_interface_connection(self, channel: str) -> None:
        # check CAN-BUS-Interface connection status
        if self.can_handler.get_connect_status() == False:
            # Get Baudrate from 'baudrate_selector'
            bps: int = self.baudrate_selector.get_baudrate()
            # Make a connection
            self.can_handler.connect_device(channel, bps, self.can_type)

            # set statuses
            self.baudrate_selector.set_disable()  # Make baudrate_selector uneditable
            # Notify the CAN-BUS connection is established to the 'channel_selector'
            self.can_connection_status_signal.emit(True)
            self.log(f"Connected to {channel} : {bps} bps", color="green")
        else:
            self.can_handler.disconnect_devive()
            # set statuses
            self.baudrate_selector.set_enable()  # Make baudrate_selector editable
            # Notify the CAN-BUS connection is disconnected to the 'channel_selector'
            self.can_connection_status_signal.emit(False)
            self.log("Disconnected", color="green")

    @Slot()
    def _change_radix_to_dec(self) -> None:
        self.radix_type = "dec"
        self.setWindowTitle(f"CANViewer | {self.can_type} | {self.radix_type}")
        self.radix_status_signal.emit(self.radix_type)

    @Slot()
    def _change_radix_to_hex(self) -> None:
        self.radix_type = "hex"
        self.setWindowTitle(f"CANViewer | {self.can_type} | {self.radix_type}")
        self.radix_status_signal.emit(self.radix_type)


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
