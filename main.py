import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from browser import BrowserWindow

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("assets/spectra_icon.png"))

window = BrowserWindow()
window.show()

sys.exit(app.exec())
