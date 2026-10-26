import os
import sys
import asyncio

# Ensure project root directory is on sys.path for local module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from Jarvis_UI import JarvisMainWindow
from utils import setup_logging


def main():
    setup_logging()

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    main_window = JarvisMainWindow()
    main_window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
