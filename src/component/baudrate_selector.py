from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget


class BaudrateSelector(QWidget):
    def __init__(
        self,
        parent=None,
        default_bps: str = "1000k",
        label: str = "Baudrate:",
        bitrate_options: list[str] | None = None,
        allow_custom: bool = True,
    ):
        super().__init__(parent)
        self._default_bps = default_bps

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._layout.addWidget(QLabel(label))
        self._bps_combobox = QComboBox()
        self._bps_combobox.setEditable(True)
        if bitrate_options is None:
            bitrate_options = [
                "10k",
                "20k",
                "50k",
                "100k",
                "125k",
                "250k",
                "500k",
                "800k",
                "1000k",
            ]
        self._bitrate_options = bitrate_options
        self._bps_combobox.addItems(bitrate_options)
        self._bps_combobox.setCurrentText(default_bps)
        self._bps_combobox.setEditable(allow_custom)
        if allow_custom:
            self._bps_combobox.setValidator(QIntValidator())
        self._layout.addWidget(self._bps_combobox)

    def set_baudrate_text(self, bps: str) -> None:
        if not self._bps_combobox.isEditable() and bps not in self._bitrate_options:
            bps = self._default_bps
        self._bps_combobox.setCurrentText(bps)

    def get_baudrate_text(self) -> str:
        return self._bps_combobox.currentText()

    def get_baudrate(self) -> int:
        return self._parse_bps(self._bps_combobox.currentText())

    def set_enable(self) -> None:
        self._bps_combobox.setEnabled(True)

    def set_disable(self) -> None:
        self._bps_combobox.setDisabled(True)

    def _parse_bps(self, bps_str: str) -> int:
        bps_str = bps_str.strip()
        if bps_str.endswith("M") or bps_str.endswith("m"):
            return int(int(bps_str[:-1]) * 1_000_000)
        elif bps_str.endswith("K") or bps_str.endswith("k"):
            return int(int(bps_str[:-1]) * 1_000)
        else:
            return int(bps_str)
