# main.py
import sys
from PyQt5.QtWidgets import QApplication
from overlay import Overlay

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())