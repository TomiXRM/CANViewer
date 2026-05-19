from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget


class BitrateSelector(QWidget):
    def __init__(
        self,
        parent=None,
        default_bitrate: str = "1000k",
        label: str = "Bitrate:",
        bitrate_options: list[str] | None = None,
        allow_custom: bool = True,
    ):
        super().__init__(parent)
        self._default_bitrate = default_bitrate

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._layout.addWidget(QLabel(label))
        self._bitrate_combobox = QComboBox()
        self._bitrate_combobox.setEditable(True)
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
        self._bitrate_combobox.addItems(bitrate_options)
        self._bitrate_combobox.setCurrentText(default_bitrate)
        self._bitrate_combobox.setEditable(allow_custom)
        if allow_custom:
            self._bitrate_combobox.setValidator(QIntValidator())
        self._layout.addWidget(self._bitrate_combobox)

    def set_bitrate_text(self, bitrate: str) -> None:
        if (
            not self._bitrate_combobox.isEditable()
            and bitrate not in self._bitrate_options
        ):
            bitrate = self._default_bitrate
        self._bitrate_combobox.setCurrentText(bitrate)

    def get_bitrate_text(self) -> str:
        return self._bitrate_combobox.currentText()

    def get_bitrate(self) -> int:
        return self._parse_bitrate(self._bitrate_combobox.currentText())

    def set_enable(self) -> None:
        self._bitrate_combobox.setEnabled(True)

    def set_disable(self) -> None:
        self._bitrate_combobox.setDisabled(True)

    def _parse_bitrate(self, bitrate_text: str) -> int:
        bitrate_text = bitrate_text.strip()
        if bitrate_text.endswith("M") or bitrate_text.endswith("m"):
            return int(int(bitrate_text[:-1]) * 1_000_000)
        elif bitrate_text.endswith("K") or bitrate_text.endswith("k"):
            return int(int(bitrate_text[:-1]) * 1_000)
        else:
            return int(bitrate_text)
