from datetime import datetime
from typing import Optional

import can
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QTextEdit


class LogBox(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Menlo", 14))
        self.setLineWrapMode(QTextEdit.NoWrap)

    # show log to logbox
    @Slot(str, str)
    def log(self, text: str, color: Optional[str] = None) -> None:
        if color is None:
            if "<font" in text or "<span" in text:
                self._append_html(text)
            else:
                self.append(text)
        else:
            self._append_html(f"<font color='{color}'>{text}</font>")

    def _append_html(self, html: str) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html)
        cursor.insertBlock()
        self.setTextCursor(cursor)

    # show can message to logbox
    @Slot(can.Message)
    def can_msg_log(self, msg: can.Message) -> None:
        dir = ""
        if msg is None:
            return

        # color setting with message direction and ID type
        # RX: orange, TX: blue
        # EXT: light blue, STD: blue
        color: str = ""
        if msg.is_rx:
            if msg.is_extended_id:
                color = "#FFA22B"  # orange
            else:
                color = "#EC4954"  # red
            dir = "RX"
        else:
            if msg.is_extended_id:
                color = "#33C0FF"  # light blue
            else:
                color = "#2C4AFF"  # blue
            dir = "TX"

        # make ID string with message ID type(Std/Ext)
        if msg.is_extended_id:
            id_str = f"{msg.arbitration_id:08x}"
        else:
            id_str = "_____" + f"{msg.arbitration_id:03x}"

        ms_timestamp = datetime.now().strftime("%M:%S:%f")[:-3]
        data_bytes = list(msg.data) if msg.data is not None else []
        if msg.is_fd and len(data_bytes) > 8:
            data_html = self._format_fd_data_with_gradient(
                data_bytes, is_tx=not msg.is_rx
            )
            prefix = (
                f"time:{ms_timestamp}\t{dir}:{'E' if msg.is_error_frame else ' '} "
                f"{'EXT' if msg.is_extended_id else 'STD'}ID:{id_str.upper()} data:"
            )
            text = f"<font color='{color}'>{prefix}</font> {data_html}"
            self.log(text)
        else:
            data_str = " ".join(f"{byte:02x}".upper() for byte in data_bytes)
            text = f"time:{ms_timestamp}\t{dir}:{'E' if msg.is_error_frame else ' '} {'EXT' if msg.is_extended_id else 'STD'}ID:{id_str.upper()} data:{data_str}"
            self.log(text, color=color)

    def _format_fd_data_with_gradient(self, data_bytes: list[int], is_tx: bool) -> str:
        if is_tx:
            start_color = "#2C4AFF"
            end_color = "#FF00FF"
        else:
            start_color = "#EC4954"
            end_color = "#FFA22B"
        chunks = [data_bytes[i : i + 8] for i in range(0, len(data_bytes), 8)]
        steps = max(2, min(8, len(chunks)))
        colors = self._interpolate_colors(start_color, end_color, steps)
        segments = []
        for idx, chunk in enumerate(chunks):
            color = colors[min(idx, len(colors) - 1)]
            segment = " ".join(f"{byte:02x}".upper() for byte in chunk)
            segments.append(f"<font color='{color}'>{segment}</font>")
        return " | ".join(segments)

    def _interpolate_colors(
        self, start_hex: str, end_hex: str, steps: int
    ) -> list[str]:
        def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
            return "#{:02X}{:02X}{:02X}".format(*rgb)

        start = hex_to_rgb(start_hex)
        end = hex_to_rgb(end_hex)
        if steps <= 1:
            return [rgb_to_hex(start)]
        colors = []
        for i in range(steps):
            t = i / (steps - 1)
            rgb = (
                round(start[0] + (end[0] - start[0]) * t),
                round(start[1] + (end[1] - start[1]) * t),
                round(start[2] + (end[2] - start[2]) * t),
            )
            colors.append(rgb_to_hex(rgb))
        return colors
