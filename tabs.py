from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWidgets import (
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QLabel
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings
)
from PyQt6.QtGui import QIcon

from settings import DEFAULT_HOME_PAGE



class _FakeHistory:
    def canGoBack(self):
        return False

    def canGoForward(self):
        return False


class _FakeView(QWidget):
    def __init__(self):
        super().__init__()
        self._zoom = 1.0
        self._url = QUrl()

    def history(self):
        return _FakeHistory()

    def setZoomFactor(self, factor):
        self._zoom = factor

    def zoomFactor(self):
        return self._zoom

    def url(self):
        return self._url

    def findText(self, *args, **kwargs):
        pass


class BrowserTab(QWidget):
    title_changed = pyqtSignal(str)
    url_changed = pyqtSignal(QUrl)
    icon_changed = pyqtSignal(QIcon)
    load_progress = pyqtSignal(int)
    load_finished = pyqtSignal(bool)
    new_tab_requested = pyqtSignal(QUrl)

    def __init__(self, profile: QWebEngineProfile,
                 url: str = DEFAULT_HOME_PAGE,
                 incognito: bool = False,
                 is_incognito: bool = None,
                 parent=None):
        super().__init__(parent)

        self.is_incognito = incognito if is_incognito is None else is_incognito
        self.profile = profile

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.view = QWebEngineView(self)

        page = QWebEnginePage(profile, self.view)
        self.view.setPage(page)

        layout.addWidget(self.view)

        self._wire_signals()
        self._configure_page_settings()

        if url:
            self.load_url(url)


    def _configure_page_settings(self):
        s = self.view.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        s.setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,
            False
        )


    def _wire_signals(self):
        self.view.titleChanged.connect(self.title_changed.emit)
        self.view.urlChanged.connect(self.url_changed.emit)
        self.view.iconChanged.connect(self.icon_changed.emit)
        self.view.loadProgress.connect(self.load_progress.emit)
        self.view.loadFinished.connect(self.load_finished.emit)
        self.view.page().newWindowRequested.connect(
            self._on_new_window_requested
        )

    def _on_new_window_requested(self, request):
        self.new_tab_requested.emit(request.requestedUrl())

    def load_url(self, url):
        if not url:
            return

        if isinstance(url, QUrl):
            url = url.toString()

        if url == "spectra://home":
            self.load_spectra_home()
            return

        qurl = QUrl.fromUserInput(url)
        self.view.load(qurl)

    def load_spectra_home(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        body{
            margin:0;
            background: radial-gradient(circle at center, #050d1f, #000);
            font-family: Arial;
            color:white;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
            overflow:hidden;
        }

        .container{
            text-align:center;
        }

        .logo{
            width:220px;
            border-radius:40px;
            box-shadow: 0 0 50px rgba(0,140,255,0.6);
            animation: pulse 2s infinite ease-in-out;
        }

        h1{
            color:#00aaff;
            font-size:60px;
            letter-spacing:10px;
            margin-top:20px;
        }

        input{
            width:600px;
            padding:18px;
            margin-top:30px;
            border:none;
            border-radius:30px;
            background:#081120;
            color:white;
            font-size:18px;
            outline:none;
        }

        .quick{
            margin-top:30px;
        }

        .quick button{
            padding:12px 20px;
            margin:8px;
            border:none;
            border-radius:20px;
            background:#091625;
            color:#00aaff;
            cursor:pointer;
        }

        @keyframes pulse{
            0%{transform:scale(1);}
            50%{transform:scale(1.05);}
            100%{transform:scale(1);}
        }
        </style>
        </head>
        <body>
            <div class="container">
                <h1>SPECTRA</h1>
                <form onsubmit="searchSpectra(); return false;">
                    <input id="searchBox" type="text"
                    placeholder="Search Spectra...">
                </form>

                <script>
                    function searchSpectra() {
                        let query =
                        document.getElementById("searchBox").value;
                        window.location.href =
                        "https://duckduckgo.com/?q=" +
                        encodeURIComponent(query);
                    }
                </script>
            </div>
        </body>
        </html>
        """
        self.view.setHtml(html, QUrl("spectra://home"))


    def current_url(self) -> str:
        return self.view.url().toString()

    def current_title(self) -> str:
        title = self.view.title()
        return title if title else "New Tab"

    def back(self):
        self.view.back()

    def forward(self):
        self.view.forward()

    def reload(self):
        self.view.reload()

    def stop(self):
        self.view.stop()

    def find_text(self, text: str):
        self.view.findText(text)



class TabWidget(QTabWidget):
    active_tab_changed = pyqtSignal(object)
    all_tabs_closed = pyqtSignal()
    new_tab_requested_from_tab = pyqtSignal(QUrl)

    def __init__(self,
                 profile: QWebEngineProfile,
                 incognito_profile: QWebEngineProfile,
                 parent=None):
        super().__init__(parent)

        self.normal_profile = profile
        self.incognito_profile = incognito_profile

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self._on_current_changed)


    def add_tab(self,
                url: str = DEFAULT_HOME_PAGE,
                incognito: bool = False,
                background: bool = False) -> BrowserTab:

        profile = self.incognito_profile if incognito else self.normal_profile

        tab = BrowserTab(
            profile,
            url=url,
            incognito=incognito,
            parent=self
        )

        tab.title_changed.connect(
            lambda title, t=tab: self._on_tab_title_changed(t, title)
        )
        tab.icon_changed.connect(
            lambda icon, t=tab: self._on_tab_icon_changed(t, icon)
        )
        tab.new_tab_requested.connect(
            self.new_tab_requested_from_tab.emit
        )

        label = "Incognito Tab" if incognito else "New Tab"
        index = self.addTab(tab, label)

        if incognito:
            self.setTabIcon(index, QIcon())

        if not background:
            self.setCurrentIndex(index)

        return tab

    def close_tab(self, index: int):
        widget = self.widget(index)
        self.removeTab(index)

        if widget:
            widget.deleteLater()

        if self.count() == 0:
            self.all_tabs_closed.emit()

    def close_current_tab(self):
        if self.count() > 0:
            self.close_tab(self.currentIndex())

    def current_tab(self):
        w = self.currentWidget()
        return w if isinstance(w, BrowserTab) else None

    def _on_current_changed(self, index: int):
        tab = self.widget(index) if index >= 0 else None
        self.active_tab_changed.emit(tab)

    def _on_tab_title_changed(self, tab: BrowserTab, title: str):
        index = self.indexOf(tab)

        if index < 0:
            return

        display_title = title if title else (
            "Incognito Tab" if tab.is_incognito else "New Tab"
        )

        self.setTabText(index, display_title)
        self.setTabToolTip(index, tab.current_url())

    def _on_tab_icon_changed(self, tab: BrowserTab, icon: QIcon):
        index = self.indexOf(tab)

        if index >= 0 and not icon.isNull():
            self.setTabIcon(index, icon)
