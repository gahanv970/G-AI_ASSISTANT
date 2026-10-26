
import sys
import asyncio

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from jarvis_ui import JarvisMainWindow
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
