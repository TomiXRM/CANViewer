import argparse
import sys
from typing import Optional

import can
from PySide6.QtCore import QSettings, Signal, Slot
from PySide6.QtGui import QAction, QKeySequence, Qt
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
from src.component.message_filter import MessageFilter
from src.utils.can_handler import CANHandler

from returns.result import Success, Failure
from returns.pipeline import is_successful


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
        self.setGeometry(500, 200, 800, 300)

        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)

        # Components
        self.can_handler = CANHandler()
        self.channel_selector = ChannelSelector(can_type=self.can_type)
        self.can_message_editor = CanMessageEditor()
        self.baudrate_selector = BaudrateSelector()
        self.communication_controller = CommunicationController()
        self.message_filter = MessageFilter()
        self.log_box = LogBox()

        # Layout
        self._layout_main = QVBoxLayout()
        self._layout_holizontal = QHBoxLayout()
        self._layout_holizontal.addLayout(self._layout_main, 800)
        self._central_widget.setLayout(self._layout_holizontal)

        self._layout_main.addWidget(self.channel_selector)
        self._layout_main.addWidget(self.can_message_editor)
        self._layout_main.addWidget(self.log_box)
        self._layout_holizontal.addWidget(self.message_filter, 300)

        # Bottom Layout
        self._layout_bottom = QHBoxLayout()
        self._layout_bottom.addWidget(self.baudrate_selector)
        self._layout_bottom.addWidget(self.communication_controller)
        self._layout_main.addLayout(self._layout_bottom)

        # Hide Message Filter Default
        self.message_filter.setVisible(False)

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
        _toggle_message_filter = QAction("Show and Hide the Message Filter", self)
        _toggle_message_filter.setShortcuts([QKeySequence(Qt.CTRL | Qt.Key_P)])
        _toggle_message_filter.triggered.connect(self._toggle_message_filter)
        self.addAction(_toggle_message_filter)

        # Ctrl + Enter : Send CAN Message
        send_can_msg_with_keybind_action = QAction("Send CAN Message", self)
        send_can_msg_with_keybind_action.setShortcuts(
            [QKeySequence(Qt.CTRL | Qt.Key_Return)]
        )
        send_can_msg_with_keybind_action.triggered.connect(self.send_can_msg)
        self.addAction(send_can_msg_with_keybind_action)

        # Signal Connection

        # When the Radix changes, notify new radix
        self.radix_status_signal.connect(self.can_message_editor.update_radix)
        self.radix_status_signal.connect(self.message_filter.update_radix)
        self.can_message_editor.radix_toggle_signal.connect(self.toggle_radix)

        # Send log data to logbox
        self.log_signal.connect(self.log_box.log)

        # Send CAN-BUS Message to logbox
        self.can_log_signal.connect(self.log_box.can_msg_log)
        self.can_handler.send_can_signal.connect(self.log_box.can_msg_log)

        # Notify the CAN-BUS connection status
        self.can_connection_status_signal.connect(
            self.channel_selector.can_connection_change_callback
        )
        self.can_connection_status_signal.connect(
            self.communication_controller.can_connection_change_callback
        )

        ###############################################
        # Send a Trigger when the 'communication_controller' order to send a message
        self.communication_controller.send_can_msg_trigger_signal.connect(
            self.send_can_msg
        )

        # Handle Log data from 'communication_controller'
        self.communication_controller.log_signal.connect(self.log)

        # Clear Log data from 'communication_controller'
        self.communication_controller.log_clear_signal.connect(self.log_box.clear)

        ###############################################
        # Connect/Disconnect CAN-BUS Interface(with receiving 'channel name')
        self.channel_selector.channel_signal.connect(
            self._toggle_can_interface_connection
        )

        ###############################################
        # Handle Log data from 'can_message_editor'
        self.can_message_editor.log_signal.connect(self.log)

        ###############################################
        # Update Ignore IDs from 'message_filter'
        self.message_filter.update_filter_id_signal.connect(
            self.can_handler.update_ignore_ids
        )

        # load settings
        self.settings = QSettings("CANViewer", "CANViewer")
        saved_bps = self.settings.value("bps", "1M")
        self.baudrate_selector.set_baudrate_text(saved_bps)

    def closeEvent(self, event) -> None:
        self.settings.setValue("bps", self.baudrate_selector.get_baudrate_text())
        event.accept()

    @Slot()
    def send_can_msg(self) -> None:
        # Check CAN connection status
        if self.can_handler.get_connect_status() == False:
            self.log("No connection!! Please connect to CAN device", color="red")
            return

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
    def log(self, text: str, color: Optional[str] = None) -> None:
        self.log_signal.emit(text, color)

    @Slot(str)
    def _toggle_can_interface_connection(self, channel: str) -> None:
        # check CAN-BUS-Interface connection status
        if self.can_handler.get_connect_status() == False:
            # Get Baudrate from 'baudrate_selector'
            bps: int = self.baudrate_selector.get_baudrate()
            # Make a connection
            rslt = self.can_handler.connect_device(channel, bps, self.can_type)

            if is_successful(rslt):
                # set statuses
                self.baudrate_selector.set_disable()  # Make baudrate_selector uneditable
                # Notify the CAN-BUS connection is established to the 'channel_selector'
                self.can_connection_status_signal.emit(True)
                self.log(f"Connected to {channel} : {bps} bps", color="green")
            else:
                self.log(f"{rslt.failure()}", color="red")
            
        else:
            self.can_handler.disconnect_devive()
            # set statuses
            self.baudrate_selector.set_enable()  # Make baudrate_selector editable
            # Notify the CAN-BUS connection is disconnected to the 'channel_selector'
            self.can_connection_status_signal.emit(False)
            self.log("Disconnected", color="green")

    @Slot()
    def _toggle_message_filter(self) -> None:
        if self.message_filter.isVisible():
            self.message_filter.setHidden(True)
            self.resize(800, 300)
        else:
            self.message_filter.setVisible(True)
            self.resize(1100, 300)

    @Slot()
    def toggle_radix(self) -> None:
        if self.radix_type == "hex":  # hex -> dec
            self._change_radix_to_dec()
        elif self.radix_type == "dec":  # dec -> hex
            self._change_radix_to_hex()

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
