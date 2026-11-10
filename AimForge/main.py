import sys
from PySide6.QtWidgets import QApplication
from aimforge.ui import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AimForge")
    app.setOrganizationName("AimForge")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
