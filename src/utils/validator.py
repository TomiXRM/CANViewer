from PiSide6.QtGui import QIntValidator, QRegularExpressionValidator
from PySide6.QtCore import (QRegularExpression,Qt)

hex_validator = QRegularExpressionValidator(QRegularExpression("^[0-9A-Fa-f]+$"))  # HEX
dec_validator = QIntValidator()  # DEC
