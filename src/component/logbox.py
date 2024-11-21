from datetime import datetime

import can
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTextEdit


class LogBox(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Menlo", 14))
        self.setLineWrapMode(QTextEdit.NoWrap)

    # show log to logbox
    @Slot(str, str)
    def log(self, text: str, color: str = None) -> None:
        if color is None:
            self.append(text)
        else:
            self.append(f"<font color='{color}'>{text}</font>")

    # show can message to logbox
    @Slot(can.Message)
    def can_msg_log(self, msg: can.Message) -> None:
        dir = ""
        if msg is None:
            return

        # color setting with message direction and ID type
        # RX: orange, TX: blue
        # EXT: light blue, STD: blue
        if msg.is_rx:
            if msg.is_extended_id:
                color: str = "#FFA22B"  # orange
            else:
                color: str = "#EC4954"  # red
            dir = "RX"
        else:
            if msg.is_extended_id:
                color: str = "#33C0FF"  # light blue
            else:
                color: str = "#2C4AFF"  # blue
            dir = "TX"

        # make ID string with message ID type(Std/Ext)
        if msg.is_extended_id:
            id_str = f"{msg.arbitration_id:08x}"
        else:
            id_str = "_____" + f"{msg.arbitration_id:03x}"

        ms_timestamp = datetime.now().strftime("%M:%S:%f")[:-3]
        data_str = " ".join(f"{byte:02x}".upper() for byte in msg.data)
        text = f"time:{ms_timestamp}\t{dir}:{'E' if msg.is_error_frame else ' '} {'EXT' if msg.is_extended_id else 'STD'}ID:{id_str.upper()} data:{data_str}"
        self.log(text, color=color)
