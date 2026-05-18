import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.db import init_db
from app.main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    app = QApplication(sys.argv)
    app.setApplicationName("KeenPie")
    app.setOrganizationName("KeenPie")

    init_db()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
