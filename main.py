import argparse
import os
import sys
from datetime import datetime

import can
import serial.tools.list_ports
from PySide6.QtCore import QMutex, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont, QIntValidator, QTextCursor
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QPushButton, QTextEdit,
                               QVBoxLayout, QWidget)

parser = argparse.ArgumentParser(
    prog="CAN Send and Receive App",
    usage="python main.py [options]",
    epilog="end",  # ヘルプの後に表示
    add_help=True,  # -h/–-helpオプションの追加
)

# -cオプションでCANのtypeを指定
parser.add_argument("-c", "--can", type=str, default="slcan", help="CAN type (socketcan, slcan)")

args = parser.parse_args()


class CANHandler(QThread):
    send_can_signal = Signal(can.Message)
    can_bus = None

    def init(self):
        super().__init__()

    def connect_device(self, port, bps, bus_type):  # Connect and start receiving
        self.can_bus = can.interface.Bus(channel=port, bitrate=bps, receive_own_messages=False, bustype=bus_type)
        self.can_notifier = can.Notifier(self.can_bus, [self.can_on_recieve])

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
        msg.timestamp = datetime.now()
        self.send_can_signal.emit(msg)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.can_type = args.can  # "socketcan" or "slcan"
        self.setWindowTitle(f"CAN Sender App | {args.can}")
        self.setGeometry(100, 100, 800, 300)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # ポートの選択
        port_layout = QHBoxLayout()

        self.portlist_layout = QHBoxLayout()
        self.port_label = QLabel("Port")
        self.portlist_layout.addWidget(self.port_label)
        self.port_combobox = QComboBox()
        self.portlist_layout.addWidget(self.port_combobox)
        self.refresh_ports()
        port_layout.addLayout(self.portlist_layout)
        port_layout.setContentsMargins(0, 0, 0, 0)  # 余白を削除

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        port_layout.addWidget(self.connect_button)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.search_button)
        self.layout.addLayout(port_layout)

        # データ入力
        data_layout = QHBoxLayout()
        self.id_button = QPushButton("StdID")
        # ボタンをクリックしたら、StdIdからExtIdにトグル
        self.id_button.setMinimumWidth(50)
        self.id_button.clicked.connect(self.toggle_stdid_extid)
        data_layout.addWidget(self.id_button)
        self.stdid_edit = QLineEdit("0")
        self.stdid_edit.setValidator(QIntValidator())
        data_layout.addWidget(self.stdid_edit)
        self.dataframe_label = QLabel("DataFrame")
        data_layout.addWidget(self.dataframe_label)
        self.dataframe_edits = []
        for i in range(8):
            edit = QLineEdit("0")
            edit.setValidator(QIntValidator())
            data_layout.addWidget(edit)

            self.dataframe_edits.append(edit)
        self.layout.addLayout(data_layout)

        # ログの表示
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        font = QFont("Menlo", 14)
        self.log_edit.setFont(font)  # ログエディットのフォントを設定
        self.layout.addWidget(self.log_edit)

        self.can_config_layout = QHBoxLayout()
        # 通信速度の設定
        bps_layout = QHBoxLayout()
        self.bps_label = QLabel("baudrate [bps]")
        bps_layout.addWidget(self.bps_label)
        self.bps_edit = QLineEdit()
        self.bps_edit.setText("100000")
        self.bps_edit.setValidator(QIntValidator())
        bps_layout.addWidget(self.bps_edit)
        self.can_config_layout.addLayout(bps_layout)

        # 送信周期・送信に関する入力
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("Interval [ms]")
        interval_layout.addWidget(self.interval_label)
        self.interval_edit = QLineEdit()
        self.interval_edit.setValidator(QIntValidator())
        interval_layout.addWidget(self.interval_edit)
        self.can_config_layout.addLayout(interval_layout)

        buttons_layout = QHBoxLayout()

        # ログのリセット
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(lambda: self.log_edit.clear())
        buttons_layout.addWidget(self.clear_button)

        # 送信開始・停止
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.toggle_interval_send)
        buttons_layout.addWidget(self.start_button)

        self.can_config_layout.addLayout(buttons_layout)
        self.layout.addLayout(self.can_config_layout)

        self.timer = None
        self.sending = False
        self.is_extended_id = False

        # CAN Hanlder Setup
        self.can_handler = CANHandler()
        self.can_handler.send_can_signal.connect(self.print_msg)

    def refresh_ports(self):
        if self.can_type == "slcan":
            self.port_combobox.clear()
            for n, (port, desc, devid) in enumerate(sorted(serial.tools.list_ports.comports()), 1):
                print(f" {n}: {port:20} {desc} {devid}")
                self.port_combobox.addItem(port)
                if "CANable" in desc:
                    self.port_combobox.setCurrentText(port)
        elif self.can_type == "socketcan":
            self.port_combobox.clear()
            for interface in self.get_socketcan_interfaces():
                self.port_combobox.addItem(interface)

    def get_socketcan_interfaces(self):
        output = os.popen('ip link show').read()

        can_interfaces = []
        lines = output.splitlines()

        for i, line in enumerate(lines):
            if 'link/can' in line:
                previous_line = lines[i - 1]
                interface_name = previous_line.split(':')[1].strip()
                can_interfaces.append(interface_name)

        return can_interfaces

    def toggle_connection(self):
        if self.can_handler.get_connect_status() == False:
            port = self.port_combobox.currentText()
            try:
                bps = int(self.bps_edit.text())
                self.can_handler.connect_device(port, bps, self.can_type)
                self.bps_edit.setEnabled(False)
                self.log("Connected to {}".format(port), color="green")
                self.connect_button.setText("Disconnect")
            except Exception as e:
                self.log("Failed to connect: {}".format(e), color="red")
        else:
            self.can_handler.disconnect_device()
            self.log("Disconnected", color="green")
            self.connect_button.setText("Connect")
            self.bps_edit.setEnabled(True)

    def toggle_interval_send(self):
        if self.sending:
            self.timer.stop()
            self.start_button.setText("Start")
            self.interval_edit.setEnabled(True)
            self.sending = False
            self.log("Stopped sending data")
        else:
            interval_text = self.interval_edit.text()
            if interval_text == "" or int(interval_text) == 0:
                self.send_data()  # 一時的な送信
            else:
                interval = int(interval_text)
                self.timer = QTimer()
                self.timer.timeout.connect(self.send_data)
                self.timer.start(interval)
                self.start_button.setText("Stop")

                self.bps_edit.setEnabled(False)
                self.sending = True
                self.log("Sending data at {} ms intervals".format(interval))

    def toggle_stdid_extid(self):
        self.is_extended_id = not self.is_extended_id  # モードを切り替え
        if self.is_extended_id:
            self.id_button.setText("ExtID")
        else:
            self.id_button.setText("StdID")

    def send_data(self):
        sendable = True
        if self.can_handler.get_connect_status() == False:
            self.log("Not connected to a port. ", color="red")
            sendable = False
        if self.stdid_edit.text() == "":
            self.log("Id is empty. ", color="red")
            sendable = False
        if any([edit.text() == "" for edit in self.dataframe_edits]):
            self.log("DataFrame is empty. ", color="red")
            sendable = False

        if sendable:
            stdid = int(self.stdid_edit.text())
            data = [int(edit.text()) for edit in self.dataframe_edits]
            # check if the data is in the correct range and change it if necessary
            for i in range(len(data)):
                if data[i] > 255:
                    data[i] = 255
                elif data[i] < 0:
                    data[i] = 0

            msg = can.Message(arbitration_id=stdid, data=data, is_extended_id=self.is_extended_id, is_rx=False)

            try:
                self.can_handler.can_send(msg)
                self.print_msg(msg)
            except can.CanError as e:
                self.log("Failed to send: {}".format(e), color="red")

    def print_msg(self, msg: can.Message):
        dir = ''
        if msg is not None:
            if msg.is_rx:
                if msg.is_extended_id:
                    color: str = '#FFA22B'  # orange
                else:
                    color: str = '#EC4954'  # red
                dir = 'RX'
            else:
                if msg.is_extended_id:
                    color: str = '#33C0FF'  # light blue
                else:
                    color: str = '#2C4AFF'  # blue
                dir = 'TX'
            if msg.is_extended_id:
                id_str = f"{msg.arbitration_id:08x}"
            else:
                id_str = "_____" + f"{msg.arbitration_id:03x}"
            ms_timestamp = datetime.now().strftime("%M:%S:%f")[:-3]
            data_str = ' '.join(f"{byte:02x}" for byte in msg.data)
            text = f"time:{ms_timestamp}\t{dir}:{'E' if msg.is_error_frame else ' '} {'EXT' if msg.is_extended_id else 'STD'}ID:{id_str} data:{data_str}"
            print(text)
            self.log(text, color=color)

    def log(self, message: can.Message, color: str = None):
        if color is None:
            self.log_edit.append(message)
        else:
            self.log_edit.append(f"<font color='{color}'>{message}</font>")


def start_gui():
    print("CAN Type:", args.can)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    start_gui()
