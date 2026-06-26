"""
settings.py
------------
Application settings persistence.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QSettings, Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QCheckBox, QPushButton, QFormLayout, QGroupBox, QFileDialog,
    QStackedWidget, QFrame, QButtonGroup, QSizePolicy, QMessageBox
)

from themes import ThemeManager, DEFAULT_THEME


SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q=",
    "DuckDuckGo": "https://duckduckgo.com/?q=",
    "Bing": "https://www.bing.com/search?q=",
}

DEFAULT_HOME_PAGE = "spectra://home"


class SettingsManager(QObject):
    settings_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._qs = QSettings("NovaBrowser", "NovaBrowser")

    def get(self, key, default=None):
        return self._qs.value(key, default)

    def set(self, key, value):
        self._qs.setValue(key, value)
        self.settings_changed.emit(key)

    @property
    def theme(self):
        return self.get("theme", DEFAULT_THEME)

    @theme.setter
    def theme(self, value):
        self.set("theme", value)

    @property
    def home_page(self):
        return self.get("home_page", DEFAULT_HOME_PAGE)

    @home_page.setter
    def home_page(self, value):
        self.set("home_page", value)

    @property
    def search_engine(self):
        return self.get("search_engine", "Google")

    @search_engine.setter
    def search_engine(self, value):
        self.set("search_engine", value)

    def search_engine_url(self):
        return SEARCH_ENGINES.get(self.search_engine, SEARCH_ENGINES["Google"])

    @property
    def adblock_enabled(self):
        val = self.get("adblock_enabled", True)
        return val if isinstance(val, bool) else str(val).lower() == "true"

    @adblock_enabled.setter
    def adblock_enabled(self, value):
        self.set("adblock_enabled", bool(value))

    @property
    def tracker_protection_enabled(self):
        val = self.get("tracker_protection_enabled", True)
        return val if isinstance(val, bool) else str(val).lower() == "true"

    @tracker_protection_enabled.setter
    def tracker_protection_enabled(self, value):
        self.set("tracker_protection_enabled", bool(value))

    @property
    def webrtc_blocking_enabled(self):
        val = self.get("webrtc_blocking_enabled", False)
        return val if isinstance(val, bool) else str(val).lower() == "true"

    @webrtc_blocking_enabled.setter
    def webrtc_blocking_enabled(self, value):
        self.set("webrtc_blocking_enabled", bool(value))

    @property
    def safe_browsing_enabled(self):
        val = self.get("safe_browsing_enabled", True)
        return val if isinstance(val, bool) else str(val).lower() == "true"

    @safe_browsing_enabled.setter
    def safe_browsing_enabled(self, value):
        self.set("safe_browsing_enabled", bool(value))

    @property
    def restore_session(self):
        val = self.get("restore_session", False)
        return val if isinstance(val, bool) else str(val).lower() == "true"

    @restore_session.setter
    def restore_session(self, value):
        self.set("restore_session", bool(value))

    @property
    def download_dir(self):
        from downloads import DEFAULT_DOWNLOAD_DIR
        return self.get("download_dir", DEFAULT_DOWNLOAD_DIR)

    @download_dir.setter
    def download_dir(self, value):
        self.set("download_dir", value)


class SettingsPage(QWidget):
    """
    Redesigned settings UI: a left sidebar (General / Appearance /
    Privacy & Security / Downloads / Advanced) switching pages in a
    QStackedWidget on the right, instead of one long scrolling form.

    vpn_manager and adblocker are optional so this still constructs
    fine if a caller doesn't have them handy; the Privacy dashboard and
    Advanced VPN section simply show neutral/placeholder state in that
    case rather than erroring out.
    """

    PAGES = ["General", "Appearance", "Privacy & Security", "Downloads", "Advanced"]

    def __init__(self, settings_manager, theme_manager, vpn_manager=None, adblocker=None, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.theme_manager = theme_manager
        self.vpn = vpn_manager
        self.adblocker = adblocker
        self._build_ui()
        self._refresh_dashboard()

        if self.vpn is not None:
            self.vpn.state_changed.connect(self._on_vpn_state_changed)


        self._dashboard_timer = QTimer(self)
        self._dashboard_timer.setInterval(2000)
        self._dashboard_timer.timeout.connect(self._refresh_dashboard)
        self._dashboard_timer.start()

    def _build_ui(self):
        self.setObjectName("SettingsRoot")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("SettingsContent")
        self.stack.addWidget(self._build_general_page())
        self.stack.addWidget(self._build_appearance_page())
        self.stack.addWidget(self._build_privacy_page())
        self.stack.addWidget(self._build_downloads_page())
        self.stack.addWidget(self._build_advanced_page())
        root.addWidget(self.stack, stretch=1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("SettingsSidebar")
        sidebar.setFixedWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(2)

        title = QLabel("Settings")
        title.setObjectName("SectionTitle")
        title.setStyleSheet("font-size: 18px; padding: 0 6px 12px 6px;")
        layout.addWidget(title)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for i, name in enumerate(self.PAGES):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(btn, i)
            layout.addWidget(btn)

        self.nav_group.buttons()[0].setChecked(True)
        self.nav_group.idClicked.connect(self._on_nav_clicked)

        layout.addStretch()
        return sidebar

    def _on_nav_clicked(self, index: int):
        self.stack.setCurrentIndex(index)
        if self.PAGES[index] == "Privacy & Security":
            self._refresh_dashboard()

    @staticmethod
    def _page_container() -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(18)
        return page, layout

    @staticmethod
    def _page_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SettingsPageTitle")
        return label

    def _build_general_page(self) -> QWidget:
        page, layout = self._page_container()
        layout.addWidget(self._page_title("General"))

        general_box = QGroupBox("Browsing")
        general_form = QFormLayout()

        self.home_input = QLineEdit(self.settings.home_page)
        self.home_input.editingFinished.connect(
            lambda: setattr(self.settings, "home_page", self.home_input.text())
        )
        general_form.addRow("Home page:", self.home_input)

        self.search_combo = QComboBox()
        self.search_combo.addItems(list(SEARCH_ENGINES.keys()))
        self.search_combo.setCurrentText(self.settings.search_engine)
        self.search_combo.currentTextChanged.connect(
            lambda text: setattr(self.settings, "search_engine", text)
        )
        general_form.addRow("Default search engine:", self.search_combo)

        self.restore_checkbox = QCheckBox("Restore previous session on startup")
        self.restore_checkbox.setChecked(self.settings.restore_session)
        self.restore_checkbox.toggled.connect(
            lambda checked: setattr(self.settings, "restore_session", checked)
        )
        general_form.addRow("", self.restore_checkbox)

        general_box.setLayout(general_form)
        layout.addWidget(general_box)
        layout.addStretch()
        return page


    def _build_appearance_page(self) -> QWidget:
        page, layout = self._page_container()
        layout.addWidget(self._page_title("Appearance"))

        appearance_box = QGroupBox("Theme")
        appearance_form = QFormLayout()
        self.theme_combo = QComboBox()
        for key, label in ThemeManager.available_themes():
            self.theme_combo.addItem(label, key)
        idx = self.theme_combo.findData(self.theme_manager.key)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        appearance_form.addRow("Theme:", self.theme_combo)
        appearance_box.setLayout(appearance_form)
        layout.addWidget(appearance_box)
        layout.addStretch()
        return page

    def _build_privacy_page(self) -> QWidget:
        page, layout = self._page_container()
        layout.addWidget(self._page_title("Privacy & Security"))

        dashboard_label = QLabel("Privacy Dashboard")
        dashboard_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(dashboard_label)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.trackers_card, self.trackers_value_label = self._build_dashboard_card("Trackers blocked")
        self.ads_card, self.ads_value_label = self._build_dashboard_card("Ads blocked")
        self.network_card, self.network_value_label = self._build_dashboard_card(
            "Active network mode", is_pill=True
        )

        cards_row.addWidget(self.trackers_card)
        cards_row.addWidget(self.ads_card)
        cards_row.addWidget(self.network_card)
        layout.addLayout(cards_row)

        clear_row = QHBoxLayout()
        clear_row.addStretch()
        self.clear_data_btn = QPushButton("Clear browsing data")
        self.clear_data_btn.setObjectName("SettingsDangerBtn")
        self.clear_data_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_data_btn.clicked.connect(self._on_clear_browsing_data)
        clear_row.addWidget(self.clear_data_btn)
        layout.addLayout(clear_row)

        security_box = QGroupBox("Security")
        security_form = QFormLayout()

        self.adblock_checkbox = QCheckBox("Block ads and trackers using filter lists")
        self.adblock_checkbox.setChecked(self.settings.adblock_enabled)
        self.adblock_checkbox.toggled.connect(self._on_adblock_toggled)
        security_form.addRow("", self.adblock_checkbox)

        self.tracker_protection_checkbox = QCheckBox("Enable enhanced tracker protection")
        self.tracker_protection_checkbox.setChecked(self.settings.tracker_protection_enabled)
        self.tracker_protection_checkbox.toggled.connect(
            lambda checked: setattr(self.settings, "tracker_protection_enabled", checked)
        )
        security_form.addRow("", self.tracker_protection_checkbox)

        self.webrtc_checkbox = QCheckBox("Block WebRTC IP leaks (placeholder — not yet enforced)")
        self.webrtc_checkbox.setChecked(self.settings.webrtc_blocking_enabled)
        self.webrtc_checkbox.toggled.connect(
            lambda checked: setattr(self.settings, "webrtc_blocking_enabled", checked)
        )
        security_form.addRow("", self.webrtc_checkbox)

        self.safe_browsing_checkbox = QCheckBox("Safe Browsing protection (placeholder — UI only)")
        self.safe_browsing_checkbox.setChecked(self.settings.safe_browsing_enabled)
        self.safe_browsing_checkbox.toggled.connect(
            lambda checked: setattr(self.settings, "safe_browsing_enabled", checked)
        )
        security_form.addRow("", self.safe_browsing_checkbox)

        security_box.setLayout(security_form)
        layout.addWidget(security_box)
        layout.addStretch()
        return page

    def _build_dashboard_card(self, label_text: str, is_pill: bool = False) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("DashboardCard")
        card.setMinimumHeight(86)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(6)

        if is_pill:
            value_label = QLabel("None")
            value_label.setProperty("pill", "true")
            value_label.setProperty("pillState", "idle")
            value_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        else:
            value_label = QLabel("0")
            value_label.setObjectName("DashboardCardValue")

        caption = QLabel(label_text)
        caption.setObjectName("DashboardCardLabel")

        card_layout.addWidget(value_label)
        card_layout.addWidget(caption)
        card_layout.addStretch()
        return card, value_label

    def _refresh_dashboard(self):

        trackers = 0
        ads = 0
        if self.adblocker is not None:
            trackers = getattr(self.adblocker, "trackers_blocked", None)
            if trackers is None:
                trackers = getattr(self.adblocker, "blocked_count", 0)
            ads = getattr(self.adblocker, "ads_blocked", 0)
        self.trackers_value_label.setText(str(trackers))
        self.ads_value_label.setText(str(ads))

        self._update_network_mode_pill()

    def _update_network_mode_pill(self):
        if self.vpn is not None and getattr(self.vpn, "connected", False):
            self.network_value_label.setText("VPN")
            self.network_value_label.setProperty("pillState", "connected")
        elif self.vpn is not None and getattr(self.vpn, "state", "idle") == "connecting":
            self.network_value_label.setText("Connecting…")
            self.network_value_label.setProperty("pillState", "connecting")
        else:
            self.network_value_label.setText("None")
            self.network_value_label.setProperty("pillState", "idle")
        self.network_value_label.style().unpolish(self.network_value_label)
        self.network_value_label.style().polish(self.network_value_label)

    def _on_vpn_state_changed(self, _state: str):
        self._update_network_mode_pill()

    def _on_clear_browsing_data(self):
        confirm = QMessageBox.question(
            self,
            "Clear browsing data",
            "This will clear history entries tracked by this session. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            browser_window = self.window()
            cleared = False
            if hasattr(browser_window, "history_manager"):
                hm = browser_window.history_manager
                if hasattr(hm, "clear"):
                    hm.clear()
                    cleared = True
            QMessageBox.information(
                self,
                "Clear browsing data",
                "Browsing history cleared." if cleared
                else "Nothing to clear, or history storage isn't available here."
            )


    def _build_downloads_page(self) -> QWidget:
        page, layout = self._page_container()
        layout.addWidget(self._page_title("Downloads"))

        downloads_box = QGroupBox("Save location")
        downloads_form = QFormLayout()
        download_row = QHBoxLayout()
        self.download_dir_input = QLineEdit(self.settings.download_dir)
        self.download_dir_input.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("SettingsSecondaryBtn")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse_download_dir)
        download_row.addWidget(self.download_dir_input)
        download_row.addWidget(browse_btn)
        downloads_form.addRow("Save files to:", download_row)
        downloads_box.setLayout(downloads_form)
        layout.addWidget(downloads_box)
        layout.addStretch()
        return page


    def _build_advanced_page(self) -> QWidget:
        page, layout = self._page_container()
        layout.addWidget(self._page_title("Advanced"))

        vpn_box = QGroupBox("VPN / Proxy")
        vpn_layout = QVBoxLayout()
        vpn_layout.setSpacing(10)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self.advanced_vpn_pill = QLabel("Disconnected")
        self.advanced_vpn_pill.setProperty("pill", "true")
        self.advanced_vpn_pill.setProperty("pillState", "idle")
        status_row.addWidget(self.advanced_vpn_pill)
        status_row.addStretch()
        vpn_layout.addLayout(status_row)

        if self.vpn is not None:
 
            fields_form = QFormLayout()
            fields_form.addRow("Proxy type:", self.vpn.proxy_type)
            fields_form.addRow("Host:", self.vpn.ip_input)
            fields_form.addRow("Port:", self.vpn.port_input)
            vpn_layout.addLayout(fields_form)

            btn_row = QHBoxLayout()
            connect_btn = QPushButton("Connect / Disconnect")
            connect_btn.setObjectName("SettingsSecondaryBtn")
            connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            connect_btn.clicked.connect(self.vpn.toggle_vpn)
            btn_row.addWidget(connect_btn)

            reconnect_btn = QPushButton("Reconnect")
            reconnect_btn.setObjectName("SettingsSecondaryBtn")
            reconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            reconnect_btn.clicked.connect(self.vpn.reconnect)
            btn_row.addWidget(reconnect_btn)

            test_btn = QPushButton("Test Connection")
            test_btn.setObjectName("SettingsSecondaryBtn")
            test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            test_btn.clicked.connect(self._on_test_connection)
            btn_row.addWidget(test_btn)
            btn_row.addStretch()
            vpn_layout.addLayout(btn_row)

            self.advanced_vpn_warning = QLabel("")
            self.advanced_vpn_warning.setObjectName("MutedLabel")
            self.advanced_vpn_warning.setWordWrap(True)
            vpn_layout.addWidget(self.advanced_vpn_warning)

            self.vpn.state_changed.connect(self._on_advanced_vpn_state_changed)
            self._on_advanced_vpn_state_changed(self.vpn.state)
        else:
            note = QLabel("VPN manager isn't available in this context.")
            note.setObjectName("MutedLabel")
            vpn_layout.addWidget(note)

        vpn_box.setLayout(vpn_layout)
        layout.addWidget(vpn_box)
        layout.addStretch()
        return page

    def _on_advanced_vpn_state_changed(self, state: str):
        labels = {
            "idle": "Disconnected",
            "connecting": "Connecting…",
            "connected": "Connected",
            "error": "Failed",
        }
        self.advanced_vpn_pill.setText(labels.get(state, state.title()))
        self.advanced_vpn_pill.setProperty("pillState", state)
        self.advanced_vpn_pill.style().unpolish(self.advanced_vpn_pill)
        self.advanced_vpn_pill.style().polish(self.advanced_vpn_pill)

        if state == "error" and hasattr(self, "advanced_vpn_warning"):
            self.advanced_vpn_warning.setText(
                "⚠ Couldn't connect with the current host/port. Double-check the proxy is "
                "actually listening there, then try again or use Test Connection."
            )
        elif hasattr(self, "advanced_vpn_warning"):
            self.advanced_vpn_warning.setText("")

    def _on_test_connection(self):
        if self.vpn is None:
            return
        self.vpn.test_connection()

    def _on_theme_changed(self, index: int):
        key = self.theme_combo.itemData(index)
        self.settings.theme = key
        self.theme_manager.set_theme(key)

    def _on_adblock_toggled(self, checked: bool):
        self.settings.adblock_enabled = checked
        if self.adblocker is not None and hasattr(self.adblocker, "set_enabled"):
            self.adblocker.set_enabled(checked)

    def _on_browse_download_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.settings.download_dir)
        if directory:
            self.settings.download_dir = directory
            self.download_dir_input.setText(directory)
