
from PyQt6.QtCore import Qt, QUrl, QPoint, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QToolBar, QToolButton, QProgressBar, QMenu, QStackedWidget,
    QSizePolicy, QApplication, QMessageBox, QFrame, QStyle
)
from PyQt6.QtWebEngineCore import QWebEngineProfile

from tabs import TabWidget, BrowserTab
from bookmarks import BookmarkManager, BookmarkPanel
from history import HistoryManager, HistoryPanel
from downloads import DownloadManager, DownloadPanel
from settings import SettingsManager, SettingsPage, DEFAULT_HOME_PAGE
from themes import ThemeManager
from adblock import AdBlocker
from vpn import VPNManager


class TitleBar(QWidget):

    def __init__(self, window: QMainWindow, parent=None):
        super().__init__(parent)
        self.window = window
        self._drag_pos = None
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)
        self._build_ui()
        

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(QIcon("assets/spectra_icon.png").pixmap(24, 24))
        layout.addWidget(self.icon_label)

        self.title_label = QLabel("Spectra")
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(32, 28)
        self.min_btn.clicked.connect(self.window.showMinimized)
        layout.addWidget(self.min_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setFixedSize(32, 28)
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(32, 28)
        self.close_btn.clicked.connect(self.window.close)
        layout.addWidget(self.close_btn)

    def _toggle_maximize(self):
        if self.window.isMaximized():
            self.window.showNormal()
            self.max_btn.setText("□")
        else:
            self.window.showMaximized()
            self.max_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)


class Sidebar(QWidget):


    def __init__(self, bookmark_panel: BookmarkPanel, history_panel: HistoryPanel,
                 download_panel: DownloadPanel, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self._expanded_width = 300
        self._collapsed = True

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        rail = QWidget()
        rail.setFixedWidth(48)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(4, 8, 4, 8)
        rail_layout.setSpacing(4)

        self.bookmarks_btn = QPushButton("★")
        self.bookmarks_btn.setCheckable(True)
        self.bookmarks_btn.setToolTip("Bookmarks")
        self.history_btn = QPushButton("🕘")
        self.history_btn.setCheckable(True)
        self.history_btn.setToolTip("History")
        self.downloads_btn = QPushButton("⬇")
        self.downloads_btn.setCheckable(True)
        self.downloads_btn.setToolTip("Downloads")

        for btn in (self.bookmarks_btn, self.history_btn, self.downloads_btn):
            btn.setFixedSize(40, 40)
            rail_layout.addWidget(btn)
        rail_layout.addStretch()
        outer.addWidget(rail)

        self.content = QStackedWidget()
        self.content.addWidget(bookmark_panel)
        self.content.addWidget(history_panel)
        self.content.addWidget(download_panel)
        self.content.setFixedWidth(0)
        outer.addWidget(self.content)

        self.bookmarks_btn.clicked.connect(lambda: self._show_panel(0, self.bookmarks_btn))
        self.history_btn.clicked.connect(lambda: self._show_panel(1, self.history_btn))
        self.downloads_btn.clicked.connect(lambda: self._show_panel(2, self.downloads_btn))

        self._animation = QPropertyAnimation(self.content, b"minimumWidth")
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation2 = QPropertyAnimation(self.content, b"maximumWidth")
        self._animation2.setDuration(180)
        self._animation2.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _show_panel(self, index: int, clicked_btn: QPushButton):
        others = [b for b in (self.bookmarks_btn, self.history_btn, self.downloads_btn) if b is not clicked_btn]

        if clicked_btn.isChecked() and self._collapsed:
            for b in others:
                b.setChecked(False)
            self.content.setCurrentIndex(index)
            self._animate_to(self._expanded_width)
            self._collapsed = False
        elif clicked_btn.isChecked() and not self._collapsed:
            for b in others:
                b.setChecked(False)
            self.content.setCurrentIndex(index)
        else:
            self._animate_to(0)
            self._collapsed = True

    def _animate_to(self, width: int):
        for anim in (self._animation, self._animation2):
            anim.stop()
            anim.setStartValue(self.content.width())
            anim.setEndValue(width)
            anim.start()


class BrowserWindow(QMainWindow):

    from PyQt6.QtNetwork import QNetworkProxy

    QNetworkProxy.setApplicationProxy(QNetworkProxy())
    RESIZE_MARGIN = 6 
    def _toggle_vpn(self):
        if self.vpn.isEnabled:
            self.vpn.disconnect_proxy()
        else:
            ok = self.vpn.connect_proxy()
            if not ok:
                QMessageBox.warning(self, "VPN", "Could not connect to that proxy. Check the host and port.")

    def _on_vpn_state_changed(self, connected: bool):
        self.vpn_btn.setProperty("vpnState", "connected" if connected else "idle")
        self.vpn_btn.style().unpolish(self.vpn_btn)
        self.vpn_btn.style().polish(self.vpn_btn)
        self.vpn_btn.setToolTip(
            "VPN connected — click to disconnect (Ctrl+Shift+V)" if connected
            else "VPN (Proxy) — Ctrl+Shift+V"
        )
        self.statusBar().showMessage(
            "VPN connected" if connected else "VPN disconnected", 3000
        )

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1000, 650)
        self.resize(1280, 800)
        self.setMouseTracking(True)

        self.settings = SettingsManager()
        self.theme_manager = ThemeManager(self.settings.theme)
        self.bookmark_manager = BookmarkManager()
        self.history_manager = HistoryManager()
        self.download_manager = DownloadManager()

        self.normal_profile = QWebEngineProfile.defaultProfile()
        self.normal_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        self.incognito_profile = QWebEngineProfile()

        self.download_manager.attach_to_profile(self.normal_profile)
        self.download_manager.attach_to_profile(self.incognito_profile)

        self.adblocker = AdBlocker(enabled=self.settings.adblock_enabled)
        self.normal_profile.setUrlRequestInterceptor(self.adblocker)
        self.vpn = VPNManager(self)
        self.vpn.connection_changed.connect(self._on_vpn_state_changed)
        self.incognito_profile.setUrlRequestInterceptor(self.adblocker)

        self._is_incognito_window = False
        self._resizing = False
        self._resize_edge = None

        self._build_ui()
        self._wire_shortcuts()
        self.apply_theme()
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.settings.settings_changed.connect(self._on_setting_changed)

        self.tabs.add_tab(self.settings.home_page)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.titlebar = TitleBar(self)
        root.addWidget(self.titlebar)

        root.addWidget(self._build_nav_toolbar())

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("LoadProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.bookmark_panel = BookmarkPanel(self.bookmark_manager)
        self.bookmark_panel.navigate_requested.connect(self.navigate_current_tab)
        self.history_panel = HistoryPanel(self.history_manager)
        self.history_panel.navigate_requested.connect(self.navigate_current_tab)
        self.download_panel = DownloadPanel(self.download_manager)

        self.sidebar = Sidebar(self.bookmark_panel, self.history_panel, self.download_panel)
        body.addWidget(self.sidebar)

        self.tabs = TabWidget(self.normal_profile, self.incognito_profile)
        self.tabs.active_tab_changed.connect(self._on_active_tab_changed)
        self.tabs.all_tabs_closed.connect(self.close)
        self.tabs.new_tab_requested_from_tab.connect(
            lambda qurl: self.tabs.add_tab(qurl.toString())
        )
        body.addWidget(self.tabs, stretch=1)

        root.addLayout(body)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(28, 28)
        new_tab_btn.setToolTip("New Tab (Ctrl+T)")
        new_tab_btn.clicked.connect(lambda: self.tabs.add_tab(self.settings.home_page))
        self.tabs.setCornerWidget(new_tab_btn, Qt.Corner.TopRightCorner)

        self.statusBar().setObjectName("StatusBar")
        self.statusBar().setFixedHeight(22)

    def _nav_tool_button(self, icon: QStyle.StandardPixmap, tooltip: str, handler, object_name="NavButton") -> QToolButton:
        btn = QToolButton()
        btn.setObjectName(object_name)
        btn.setIcon(self.style().standardIcon(icon))
        btn.setIconSize(QSize(18, 18))
        btn.setFixedSize(34, 34)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setAutoRaise(True)
        if handler:
            btn.clicked.connect(handler)
        return btn

    @staticmethod
    def _toolbar_separator() -> QFrame:
        sep = QFrame()
        sep.setObjectName("ToolbarSeparator")
        sep.setFixedWidth(1)
        sep.setFixedHeight(20)
        return sep

    def _build_nav_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("NavToolBar")
        bar.setFixedHeight(44)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        nav_cluster = QWidget()
        nav_layout = QHBoxLayout(nav_cluster)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)

        self.back_btn = self._nav_tool_button(
            QStyle.StandardPixmap.SP_ArrowBack, "Back (Alt+Left)", self._go_back
        )
        self.forward_btn = self._nav_tool_button(
            QStyle.StandardPixmap.SP_ArrowForward, "Forward (Alt+Right)", self._go_forward
        )
        self.reload_btn = self._nav_tool_button(
            QStyle.StandardPixmap.SP_BrowserReload, "Reload (Ctrl+R)", self._reload_current
        )
        self.home_btn = self._nav_tool_button(
            QStyle.StandardPixmap.SP_DirHomeIcon, "Home (Alt+Home)", self._go_home
        )
        for b in (self.back_btn, self.forward_btn, self.reload_btn, self.home_btn):
            nav_layout.addWidget(b)

        layout.addWidget(nav_cluster)
        layout.addWidget(self._toolbar_separator())

        address_wrap = QWidget()
        address_wrap.setObjectName("AddressBarWrap")
        address_layout = QHBoxLayout(address_wrap)
        address_layout.setContentsMargins(12, 0, 8, 0)
        address_layout.setSpacing(6)

        self.security_icon = QLabel()
        self.security_icon.setObjectName("SecurityIcon")
        self.security_icon.setPixmap(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton).pixmap(13, 13)
        )
        self.security_icon.setToolTip("Connection info")
        address_layout.addWidget(self.security_icon)

        self.address_bar = QLineEdit()
        self.address_bar.setObjectName("AddressBar")
        self.address_bar.setFrame(False)
        self.address_bar.setPlaceholderText("Search or enter a URL")
        self.address_bar.returnPressed.connect(self._on_address_bar_enter)
        self._address_bar_wrap = address_wrap
        self.address_bar.installEventFilter(self)
        address_layout.addWidget(self.address_bar, stretch=1)

        layout.addWidget(address_wrap, stretch=1)
        layout.addWidget(self._toolbar_separator())

        utility_cluster = QWidget()
        utility_layout = QHBoxLayout(utility_cluster)
        utility_layout.setContentsMargins(0, 0, 0, 0)
        utility_layout.setSpacing(2)

        self.bookmark_star_btn = QToolButton()
        self.bookmark_star_btn.setObjectName("NavButton")
        self.bookmark_star_btn.setText("☆")
        self.bookmark_star_btn.setFixedSize(34, 34)
        self.bookmark_star_btn.setToolTip("Bookmark this page (Ctrl+D)")
        self.bookmark_star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bookmark_star_btn.setAutoRaise(True)
        self.bookmark_star_btn.clicked.connect(self._toggle_bookmark_current)
        utility_layout.addWidget(self.bookmark_star_btn)

        self.downloads_btn = self._nav_tool_button(
            QStyle.StandardPixmap.SP_ArrowDown, "Downloads (Ctrl+J)",
            lambda: self.sidebar.downloads_btn.click()
        )
        utility_layout.addWidget(self.downloads_btn)


        self.vpn_btn = QToolButton()
        self.vpn_btn.setObjectName("VPNToolButton")
        self.vpn_btn.setProperty("vpnState", "idle")
        self.vpn_btn.setText("🌍")
        self.vpn_btn.setFixedSize(50, 34)
        self.vpn_btn.setToolTip("VPN (Proxy) — Ctrl+Shift+V")
        self.vpn_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.vpn_btn.setAutoRaise(True)
        self.vpn_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.vpn_btn.clicked.connect(self._toggle_vpn)

        self.vpn_quick_menu = QMenu(self)
        self.vpn_quick_menu.addAction("Reconnect", self.vpn.reconnect)
        self.vpn_quick_menu.addAction("Test Connection", self.vpn.test_connection)
        self.vpn_quick_menu.addSeparator()
        self.vpn_quick_menu.addAction("VPN Settings…", self._open_vpn_settings)
        self.vpn_btn.setMenu(self.vpn_quick_menu)
        utility_layout.addWidget(self.vpn_btn)

        self.menu_btn = QToolButton()
        self.menu_btn.setObjectName("NavButton")
        self.menu_btn.setText("⋮")
        self.menu_btn.setFixedSize(34, 34)
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setAutoRaise(True)
        self.menu_btn.clicked.connect(self._show_main_menu)
        utility_layout.addWidget(self.menu_btn)

        layout.addWidget(utility_cluster)

        return bar



    def eventFilter(self, obj, event):
        if obj is getattr(self, "address_bar", None):
            from PyQt6.QtCore import QEvent
            if event.type() == QEvent.Type.FocusIn:
                self._address_bar_wrap.setProperty("focused", True)
                self._address_bar_wrap.style().unpolish(self._address_bar_wrap)
                self._address_bar_wrap.style().polish(self._address_bar_wrap)
            elif event.type() == QEvent.Type.FocusOut:
                self._address_bar_wrap.setProperty("focused", False)
                self._address_bar_wrap.style().unpolish(self._address_bar_wrap)
                self._address_bar_wrap.style().polish(self._address_bar_wrap)
        return super().eventFilter(obj, event)


    def _wire_shortcuts(self):
        shortcuts = {
            "Ctrl+T": lambda: self.tabs.add_tab(self.settings.home_page),
            "Ctrl+W": self.tabs.close_current_tab,
            "Ctrl+L": lambda: (self.address_bar.setFocus(), self.address_bar.selectAll()),
            "Ctrl+R": self._reload_current,
            "F5": self._reload_current,
            "Alt+Left": self._go_back,
            "Alt+Right": self._go_forward,
            "Ctrl+D": self._toggle_bookmark_current,
            "Ctrl+Shift+N": self._open_incognito_tab,
            "Ctrl+Shift+V": self._toggle_vpn,
            "Ctrl+H": lambda: self.sidebar.history_btn.click(),
            "Ctrl+J": lambda: self.sidebar.downloads_btn.click(),
            "Ctrl+Shift+B": lambda: self.sidebar.bookmarks_btn.click(),
            "F11": self._toggle_fullscreen,
            "Escape": self._exit_fullscreen_if_active,
            "Ctrl+Tab": self._next_tab,
            "Ctrl+Shift+Tab": self._prev_tab,
            "Ctrl+,": self._open_settings_tab,
        }
        for seq, handler in shortcuts.items():
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(handler)


    def _current_tab(self) -> BrowserTab | None:
        return self.tabs.current_tab()

    def navigate_current_tab(self, url: str):
        tab = self._current_tab()
        if tab:
            tab.load_url(url)
        else:
            self.tabs.add_tab(url)

    def _on_address_bar_enter(self):
        text = self.address_bar.text().strip()
        if not text:
            return
        url = self._resolve_address_bar_input(text)
        self.navigate_current_tab(url)

    def _resolve_address_bar_input(self, text: str) -> str:
        looks_like_url = (
            text.startswith(("http://", "https://", "Spectra://", "file://"))
            or ("." in text and " " not in text)
        )
        if looks_like_url:
            return text
        return self.settings.search_engine_url() + QUrl.toPercentEncoding(text).data().decode()

    def _go_back(self):
        if self._current_tab():
            self._current_tab().back()

    def _go_forward(self):
        if self._current_tab():
            self._current_tab().forward()

    def _reload_current(self):
        if self._current_tab():
            self._current_tab().reload()

    def _go_home(self):
        self.navigate_current_tab(self.settings.home_page)

    def _next_tab(self):
        if self.tabs.count() > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % self.tabs.count())

    def _prev_tab(self):
        if self.tabs.count() > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % self.tabs.count())

    def _open_incognito_tab(self):
        self.tabs.add_tab(DEFAULT_HOME_PAGE, incognito=True)

    def _open_settings_tab(self):
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, SettingsPage):
                self.tabs.setCurrentIndex(i)
                return
        page = SettingsPage(self.settings, self.theme_manager, vpn_manager=self.vpn, adblocker=self.adblocker)
        index = self.tabs.addTab(page, "Settings")
        self.tabs.setCurrentIndex(index)

    def _open_vpn_settings(self):
        self._open_settings_tab()
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, SettingsPage):
                advanced_index = w.PAGES.index("Advanced")
                w.nav_group.button(advanced_index).setChecked(True)
                w.stack.setCurrentIndex(advanced_index)
                return

    def _toggle_bookmark_current(self):
        tab = self._current_tab()
        if not tab or isinstance(tab, SettingsPage):
            return
        url = tab.current_url()
        title = tab.current_title()
        now_bookmarked = self.bookmark_manager.toggle(title, url)
        self.bookmark_star_btn.setText("★" if now_bookmarked else "☆")


    def _on_active_tab_changed(self, tab):
        if tab is None or isinstance(tab, SettingsPage):
            self.progress_bar.hide()
            return

        self._sync_chrome_to_tab(tab)

        tab.url_changed.connect(lambda url, t=tab: self._on_tab_url_changed(t, url))
        tab.load_progress.connect(lambda pct, t=tab: self._on_tab_progress(t, pct))
        tab.load_finished.connect(lambda ok, t=tab: self._on_tab_load_finished(t, ok))
        tab.title_changed.connect(lambda title, t=tab: self._on_tab_title_for_history(t, title))

    def _sync_chrome_to_tab(self, tab: BrowserTab):
        self.address_bar.setText(tab.current_url())
        self.back_btn.setEnabled(tab.view.history().canGoBack())
        self.forward_btn.setEnabled(tab.view.history().canGoForward())
        is_bookmarked = self.bookmark_manager.is_bookmarked(tab.current_url())
        self.bookmark_star_btn.setText("★" if is_bookmarked else "☆")
        self.titlebar.title_label.setText(f"Spectra{'  ·  Incognito' if tab.is_incognito else ''}")

    def _on_tab_url_changed(self, tab: BrowserTab, url: QUrl):
        if tab is not self._current_tab():
            return
        self.address_bar.setText(url.toString())
        self.back_btn.setEnabled(tab.view.history().canGoBack())
        self.forward_btn.setEnabled(tab.view.history().canGoForward())
        self.bookmark_star_btn.setText(
            "★" if self.bookmark_manager.is_bookmarked(url.toString()) else "☆"
        )

    def _on_tab_progress(self, tab: BrowserTab, pct: int):
        if tab is not self._current_tab():
            return
        self.progress_bar.show()
        self.progress_bar.setValue(pct)

    def _on_tab_load_finished(self, tab: BrowserTab, ok: bool):
        if tab is self._current_tab():
            self.progress_bar.setValue(100)
            self.progress_bar.hide()

    def _on_tab_title_for_history(self, tab: BrowserTab, title: str):
        if not tab.is_incognito:
            self.history_manager.add_entry(title, tab.current_url())

    def _show_main_menu(self):
        menu = QMenu(self)
        menu.addAction("New Tab\tCtrl+T", lambda: self.tabs.add_tab(self.settings.home_page))
        menu.addAction("New Incognito Tab\tCtrl+Shift+N", self._open_incognito_tab)
        menu.addSeparator()
        vpn_label = "Disconnect VPN\tCtrl+Shift+V" if self.vpn.isEnabled else "Toggle VPN\tCtrl+Shift+V"
        menu.addAction(vpn_label, self._toggle_vpn)
        menu.addSeparator()
        menu.addAction("Bookmarks\tCtrl+Shift+B", lambda: self.sidebar.bookmarks_btn.click())
        menu.addAction("History\tCtrl+H", lambda: self.sidebar.history_btn.click())
        menu.addAction("Downloads\tCtrl+J", lambda: self.sidebar.downloads_btn.click())
        menu.addSeparator()
        menu.addAction("Settings\tCtrl+,", self._open_settings_tab)
        menu.addAction("Toggle Fullscreen\tF11", self._toggle_fullscreen)
        menu.addSeparator()
        menu.addAction("Quit", self.close)
        menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))

    def contextMenuEvent(self, event):
        tab = self._current_tab()
        if not tab or isinstance(tab, SettingsPage):
            return super().contextMenuEvent(event)

        menu = QMenu(self)
        menu.addAction("Back", self._go_back)
        menu.addAction("Forward", self._go_forward)
        menu.addAction("Reload", self._reload_current)
        menu.addSeparator()
        menu.addAction("Bookmark this page", self._toggle_bookmark_current)
        menu.addAction("Copy URL", lambda: QApplication.clipboard().setText(tab.current_url()))
        menu.addSeparator()
        menu.addAction("New Tab", lambda: self.tabs.add_tab(self.settings.home_page))
        menu.addAction("View Page Source", lambda: self.tabs.add_tab("view-source:" + tab.current_url()))
        menu.exec(event.globalPos())

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.titlebar.show()
        else:
            self.showFullScreen()
            self.titlebar.hide()

    def _exit_fullscreen_if_active(self):
        if self.isFullScreen():
            self._toggle_fullscreen()

    def _on_setting_changed(self, key: str):
        if key == "adblock_enabled":
            self.adblocker.set_enabled(self.settings.adblock_enabled)

    def apply_theme(self, *_):
        QApplication.instance().setStyleSheet(self.theme_manager.global_stylesheet())


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._edge_at(event.position().toPoint())
            if edge:
                self._resizing = True
                self._resize_edge = edge
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_edge:
            self._perform_resize(event.globalPosition().toPoint())
        else:
            self._update_resize_cursor(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self._resize_edge = None
        super().mouseReleaseEvent(event)

    def _edge_at(self, pos: QPoint) -> str | None:
        m = self.RESIZE_MARGIN
        rect = self.rect()
        left = pos.x() <= m
        right = pos.x() >= rect.width() - m
        top = pos.y() <= m
        bottom = pos.y() >= rect.height() - m
        if top and left: return "top_left"
        if top and right: return "top_right"
        if bottom and left: return "bottom_left"
        if bottom and right: return "bottom_right"
        if left: return "left"
        if right: return "right"
        if top: return "top"
        if bottom: return "bottom"
        return None

    def _update_resize_cursor(self, pos: QPoint):
        edge = self._edge_at(pos)
        cursors = {
            "left": Qt.CursorShape.SizeHorCursor, "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor, "bottom": Qt.CursorShape.SizeVerCursor,
            "top_left": Qt.CursorShape.SizeFDiagCursor, "bottom_right": Qt.CursorShape.SizeFDiagCursor,
            "top_right": Qt.CursorShape.SizeBDiagCursor, "bottom_left": Qt.CursorShape.SizeBDiagCursor,
        }
        self.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))

    def _perform_resize(self, global_pos: QPoint):
        geo = self.geometry()
        edge = self._resize_edge
        new_geo = geo

        if "right" in edge:
            new_geo.setWidth(max(self.minimumWidth(), global_pos.x() - geo.x()))
        if "bottom" in edge:
            new_geo.setHeight(max(self.minimumHeight(), global_pos.y() - geo.y()))
        if "left" in edge:
            new_width = max(self.minimumWidth(), geo.right() - global_pos.x())
            new_geo.setX(geo.right() - new_width)
            new_geo.setWidth(new_width)
        if "top" in edge:
            new_height = max(self.minimumHeight(), geo.bottom() - global_pos.y())
            new_geo.setY(geo.bottom() - new_height)
            new_geo.setHeight(new_height)

        self.setGeometry(new_geo)

    def closeEvent(self, event):
        self.history_manager.close()
        super().closeEvent(event)
