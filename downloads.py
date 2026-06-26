

import os

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QProgressBar
)

try:
    from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
except ImportError:
    QWebEngineDownloadRequest = None

DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


class DownloadItem(QObject):

    progress_changed = pyqtSignal(int)  
    state_changed = pyqtSignal(str)     

    def __init__(self, request):
        super().__init__()
        self.request = request
        self.filename = os.path.basename(request.downloadFileName())
        self.path = os.path.join(request.downloadDirectory(), request.downloadFileName())
        self.total_bytes = request.totalBytes()
        self.received_bytes = 0
        self.state = "downloading"

        request.receivedBytesChanged.connect(self._on_progress)
        request.isFinishedChanged.connect(self._on_finished)
        request.stateChanged.connect(self._on_state_changed)

    def _on_progress(self):
        self.received_bytes = self.request.receivedBytes()
        if self.total_bytes > 0:
            pct = int((self.received_bytes / self.total_bytes) * 100)
        else:
            pct = 0
        self.progress_changed.emit(pct)

    def _on_finished(self):
        if self.request.isFinished():
            self.state = "completed"
            self.state_changed.emit(self.state)

    def _on_state_changed(self):
        if QWebEngineDownloadRequest is None:
            return
        state = self.request.state()
        mapping = {
            QWebEngineDownloadRequest.DownloadState.DownloadCancelled: "cancelled",
            QWebEngineDownloadRequest.DownloadState.DownloadInterrupted: "failed",
            QWebEngineDownloadRequest.DownloadState.DownloadCompleted: "completed",
        }
        new_state = mapping.get(state)
        if new_state:
            self.state = new_state
            self.state_changed.emit(new_state)

    def cancel(self):
        self.request.cancel()

    def open_folder(self):
        folder = os.path.dirname(self.path)
        if os.path.exists(folder):
            if hasattr(os, "startfile"):
                os.startfile(folder)
            else:
                os.system(f'xdg-open "{folder}"')


class DownloadManager(QObject):


    download_added = pyqtSignal(object)     
    download_updated = pyqtSignal(object)   

    def __init__(self):
        super().__init__()
        self.items = []
        os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)

    def attach_to_profile(self, profile):
        profile.downloadRequested.connect(self._on_download_requested)

    def _on_download_requested(self, request):

        if not request.downloadDirectory():
            request.setDownloadDirectory(DEFAULT_DOWNLOAD_DIR)
        request.accept()

        item = DownloadItem(request)
        self.items.append(item)
        item.progress_changed.connect(lambda *_: self.download_updated.emit(item))
        item.state_changed.connect(lambda *_: self.download_updated.emit(item))
        self.download_added.emit(item)


class DownloadRow(QWidget):

    def __init__(self, item: DownloadItem, parent=None):
        super().__init__(parent)
        self.item = item

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        self.name_label = QLabel(item.filename)
        self.name_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.name_label)

        self.progress = QProgressBar()
        self.progress.setObjectName("LoadProgress")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        bottom_row = QHBoxLayout()
        self.status_label = QLabel("Downloading...")
        self.status_label.setObjectName("MutedLabel")
        bottom_row.addWidget(self.status_label)
        bottom_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.item.cancel)
        bottom_row.addWidget(self.cancel_btn)
        layout.addLayout(bottom_row)

        item.progress_changed.connect(self._update_progress)
        item.state_changed.connect(self._update_state)

    def _update_progress(self, pct: int):
        self.progress.setValue(pct)

    def _update_state(self, state: str):
        labels = {
            "completed": "Completed",
            "cancelled": "Cancelled",
            "failed": "Failed",
            "downloading": "Downloading...",
        }
        self.status_label.setText(labels.get(state, state))
        if state in ("completed", "cancelled", "failed"):
            self.cancel_btn.setEnabled(False)
        if state == "completed":
            self.progress.setValue(100)


class DownloadPanel(QWidget):

    def __init__(self, download_manager: DownloadManager, parent=None):
        super().__init__(parent)
        self.manager = download_manager
        self._build_ui()
        self.manager.download_added.connect(self._add_row)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Downloads")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.empty_label = QLabel("No downloads yet.")
        self.empty_label.setObjectName("MutedLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

    def _add_row(self, item: DownloadItem):
        self.empty_label.hide()
        list_item = QListWidgetItem(self.list_widget)
        row = DownloadRow(item)
        list_item.setSizeHint(row.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, row)
        self.list_widget.scrollToBottom()
