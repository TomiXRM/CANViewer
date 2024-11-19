from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget


class BaudrateSelector(QWidget):
    def __init__(self, parent=None, default_bps: str = '1M'):
        super().__init__(parent)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self._bps_combobox = QComboBox()
        self._bps_combobox.setEditable(True)
        self._bps_combobox.addItems(
            ["10k", "20k", "50k", "100k", "125k", "250k", "500k", "800k", "1000k"]
        )
        self._bps_combobox.setCurrentText(default_bps)
        self._bps_combobox.setValidator(QIntValidator())
        self.layout.addWidget(self._bps_combobox)

    def get_value(self) -> int:
        return self._parse_bps(self._bps_combobox.currentText())

    def set_enabled(self, enable: bool):
        self._bps_combobox.setEnabled(enable)

    def _parse_bps(self, bps_str: str) -> int:
        value = bps_str.upper().strip()
        if bps_str.endswith('M') or bps_str.endswith('m'):
            return int(int(bps_str[:-1]) * 1_000_000)
        elif bps_str.endswith('K') or bps_str.endswith('k'):
            return int(int(bps_str[:-1]) * 1_000)
        else:
            return int(bps_str)