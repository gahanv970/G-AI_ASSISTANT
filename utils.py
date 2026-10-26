import logging
import sys
from PySide6.QtWidgets import QMessageBox


def setup_logging(level=logging.INFO):
    """Configures application-wide logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def show_error_message(title: str, message: str):
    """Displays an error dialog box to the user."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #1A1C23;
            color: #FFFFFF;
        }
        QLabel {
            color: #FFFFFF;
        }
        QPushButton {
            background-color: #3A3D4D;
            color: #FFFFFF;
            border-radius: 6px;
            padding: 6px 12px;
            min-width: 60px;
        }
        QPushButton:hover {
            background-color: #00C8FF;
            color: #000000;
        }
    """)
    msg_box.exec()


def show_info_message(title: str, message: str):
    """Displays an information dialog box to the user."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #1A1C23;
            color: #FFFFFF;
        }
        QLabel {
            color: #FFFFFF;
        }
        QPushButton {
            background-color: #3A3D4D;
            color: #FFFFFF;
            border-radius: 6px;
            padding: 6px 12px;
            min-width: 60px;
        }
        QPushButton:hover {
            background-color: #00C8FF;
            color: #000000;
        }
    """)
    msg_box.exec()
