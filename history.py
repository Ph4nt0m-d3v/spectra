

import os
import sqlite3
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox
)


DB_PATH = os.path.join(os.path.expanduser("~"), ".novabrowser", "history.db")


class HistoryManager(QObject):

    history_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._conn = sqlite3.connect(DB_PATH)
        self._init_schema()

    def _init_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT NOT NULL,
                visited_at TEXT NOT NULL
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_url ON history(url)"
        )
        self._conn.commit()

    def add_entry(self, title: str, url: str):
        if not url or url.startswith("data:") or url == "about:blank":
            return
        self._conn.execute(
            "INSERT INTO history (title, url, visited_at) VALUES (?, ?, ?)",
            (title or url, url, datetime.now().isoformat(timespec="seconds")),
        )
        self._conn.commit()
        self.history_changed.emit()

    def search(self, query: str = "", limit: int = 200):
        if query:
            cur = self._conn.execute(
                "SELECT title, url, visited_at FROM history "
                "WHERE title LIKE ? OR url LIKE ? "
                "ORDER BY id DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            )
        else:
            cur = self._conn.execute(
                "SELECT title, url, visited_at FROM history ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        return cur.fetchall()

    def clear(self):
        self._conn.execute("DELETE FROM history")
        self._conn.commit()
        self.history_changed.emit()

    def close(self):
        self._conn.close()


class HistoryPanel(QWidget):

    navigate_requested = pyqtSignal(str)

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.manager = history_manager
        self._build_ui()
        self.manager.history_changed.connect(self.refresh)
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("History")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search history...")
        self.search_box.textChanged.connect(self.refresh)
        layout.addWidget(self.search_box)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_activated)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.clear_btn = QPushButton("Clear All History")
        self.clear_btn.setObjectName("DangerButton")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        btn_row.addWidget(self.clear_btn)
        layout.addLayout(btn_row)

    def refresh(self):
        query = self.search_box.text().strip()
        self.list_widget.clear()
        for title, url, visited_at in self.manager.search(query):
            ts = visited_at.replace("T", " ")
            item = QListWidgetItem(f"{title}\n{url}  ·  {ts}")
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.list_widget.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.navigate_requested.emit(url)

    def _on_clear_clicked(self):
        reply = QMessageBox.question(
            self, "Clear History",
            "This will permanently delete all browsing history. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.clear()
