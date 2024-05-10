import sys
from PySide6.QtWidgets import QApplication
from src.controllers.main_window import MainWindow
import logging
from src.core.constants import DEFAULT_DATA_FOLDER
import os


def init(args):
    logging.basicConfig(format="[%(asctime)s->%(levelname)s->%(module)s" +
                               "->%(funcName)s]: %(message)s",
                        datefmt="%H:%M:%S",
                        level=logging.INFO)

    if not os.path.exists(DEFAULT_DATA_FOLDER):
        os.mkdir(DEFAULT_DATA_FOLDER)


def main(args):
    init(args)
    app = QApplication(args)
    window = MainWindow(app)
    window.show()
    return app.exec()


if __name__ == "__main__":
    main(sys.argv)
