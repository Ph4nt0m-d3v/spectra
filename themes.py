from PyQt6.QtCore import QObject, pyqtSignal



THEMES = {
    "blue": {
        "name": "Blue (Default)",
        "bg": "#1b1d2a",            # main window background
        "bg_alt": "#20232f",        # secondary panels (sidebar, tab bar)
        "bg_elevated": "#262a3b",   # cards, address bar, dialogs
        "border": "#33384d",
        "text": "#e8e9f0",
        "text_dim": "#9098b3",
        "accent": "#5b7cff",        # primary accent (buttons, highlights)
        "accent_hover": "#7191ff",
        "accent_pressed": "#4866d6",
        "danger": "#ff5b6e",
        "success": "#4ad991",
        "warning": "#e6b400",
        "tab_active": "#262a3b",
        "tab_inactive": "#1b1d2a",
        "scrollbar": "#3a3f57",
    },
    "dark_green": {
        "name": "Dark Green",
        "bg": "#0f1715",
        "bg_alt": "#13201c",
        "bg_elevated": "#182822",
        "border": "#264136",
        "text": "#e6f2ec",
        "text_dim": "#8caa9b",
        "accent": "#2ecc71",
        "accent_hover": "#4cdb84",
        "accent_pressed": "#23a85b",
        "danger": "#ff5b6e",
        "success": "#2ecc71",
        "warning": "#e6b400",
        "tab_active": "#182822",
        "tab_inactive": "#0f1715",
        "scrollbar": "#23382f",
    },
    "light": {
        "name": "Light",
        "bg": "#f5f6f8",
        "bg_alt": "#ffffff",
        "bg_elevated": "#ffffff",
        "border": "#dde1e8",
        "text": "#1d1f27",
        "text_dim": "#6b7280",
        "accent": "#3366ff",
        "accent_hover": "#5580ff",
        "accent_pressed": "#274dcc",
        "danger": "#e0394d",
        "success": "#1fa463",
        "warning": "#c98a00",
        "tab_active": "#ffffff",
        "tab_inactive": "#eceef2",
        "scrollbar": "#d3d7de",
    },
}

DEFAULT_THEME = "blue"


class ThemeManager(QObject):


    theme_changed = pyqtSignal(str)  # emits the new theme key

    def __init__(self, theme_key: str = DEFAULT_THEME):
        super().__init__()
        self._theme_key = theme_key if theme_key in THEMES else DEFAULT_THEME

    @property
    def key(self) -> str:
        return self._theme_key

    @property
    def palette(self) -> dict:
        return THEMES[self._theme_key]

    def set_theme(self, theme_key: str):
        if theme_key in THEMES and theme_key != self._theme_key:
            self._theme_key = theme_key
            self.theme_changed.emit(theme_key)

    @staticmethod
    def available_themes():
        return [(k, v["name"]) for k, v in THEMES.items()]


    def global_stylesheet(self) -> str:

        p = self.palette
        return f"""
        QWidget {{
            background-color: {p['bg']};
            color: {p['text']};
            font-family: "Segoe UI", "Inter", sans-serif;
            font-size: 13px;
        }}

        /* ---- Titlebar ---- */
        #TitleBar {{
            background-color: {p['bg_alt']};
            border-bottom: 1px solid {p['border']};
        }}
        #TitleBar QLabel#TitleLabel {{
            color: {p['text_dim']};
            font-weight: 600;
            padding-left: 8px;
        }}
        #TitleBar QPushButton {{
            background: transparent;
            border: none;
            border-radius: 4px;
            padding: 6px;
            color: {p['text']};
        }}
        #TitleBar QPushButton:hover {{
            background-color: {p['bg_elevated']};
        }}
        #TitleBar QPushButton#CloseBtn:hover {{
            background-color: {p['danger']};
            color: white;
        }}

        /* ---- Navigation / Toolbar ---- */
        #NavToolBar {{
            background-color: {p['bg_alt']};
            border-bottom: 1px solid {p['border']};
        }}

        /* Icon buttons: back/forward/reload/home, bookmark, menu */
        #NavToolBar QToolButton#NavButton {{
            background: transparent;
            border: none;
            border-radius: 8px;
            color: {p['text']};
            font-size: 15px;
        }}
        #NavToolBar QToolButton#NavButton:hover {{
            background-color: {p['bg_elevated']};
        }}
        #NavToolBar QToolButton#NavButton:pressed {{
            background-color: {p['accent_pressed']};
        }}
        #NavToolBar QToolButton#NavButton:disabled {{
            color: {p['text_dim']};
        }}

        /* Thin vertical dividers between toolbar zones */
        #ToolbarSeparator {{
            background-color: {p['border']};
        }}

        /* VPN button: neutral when idle, accent-green and slightly lit when
           the proxy is actually connected (driven by vpn.py's signal, not
           just hover) so the state is visible at a glance. */
        #NavToolBar QToolButton#VPNToolButton {{
            background: transparent;
            border: none;
            border-radius: 8px;
            color: {p['text_dim']};
            font-size: 15px;
        }}
        #NavToolBar QToolButton#VPNToolButton:hover {{
            background-color: {p['bg_elevated']};
        }}
        #NavToolBar QToolButton#VPNToolButton[vpnState="connected"] {{
            background-color: rgba(74, 217, 145, 0.16);
            color: {p['success']};
        }}
        #NavToolBar QToolButton#VPNToolButton[vpnState="connected"]:hover {{
            background-color: rgba(74, 217, 145, 0.26);
        }}

        /* ---- Address bar (pill-shaped wrapper + frameless inner field) ---- */
        #AddressBarWrap {{
            background-color: {p['bg_elevated']};
            border: 1px solid {p['border']};
            border-radius: 17px;
        }}
        #AddressBarWrap:hover {{
            border: 1px solid {p['text_dim']};
        }}
        #AddressBarWrap[focused="true"] {{
            border: 1px solid {p['accent']};
        }}
        #AddressBarWrap QLabel#SecurityIcon {{
            background: transparent;
        }}
        QLineEdit#AddressBar {{
            background: transparent;
            border: none;
            padding: 7px 4px;
            color: {p['text']};
            selection-background-color: {p['accent']};
        }}

        /* ---- Tab bar ---- */

        QTabWidget::pane {{
            border: none;
            background-color: {p['bg']};
        }}
        QTabBar {{
            background-color: {p['bg_alt']};
        }}
        QTabBar::tab {{
            background-color: {p['tab_inactive']};
            color: {p['text_dim']};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 8px 14px;
            margin-right: 2px;
            min-width: 140px;
            max-width: 220px;
        }}
        QTabBar::tab:selected {{
            background-color: {p['tab_active']};
            color: {p['text']};
            border-bottom: 2px solid {p['accent']};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {p['bg_elevated']};
        }}
        QTabBar::close-button {{
            padding: 2px;
        }}

        /* ---- Sidebar ---- */
        #Sidebar {{
            background-color: {p['bg_alt']};
            border-right: 1px solid {p['border']};
        }}
        #Sidebar QPushButton {{
            text-align: left;
            background: transparent;
            border: none;
            border-radius: 6px;
            padding: 10px 12px;
            color: {p['text']};
        }}
        #Sidebar QPushButton:hover {{
            background-color: {p['bg_elevated']};
        }}
        #Sidebar QPushButton:checked {{
            background-color: {p['accent']};
            color: white;
        }}

        /* ---- Lists / panels (bookmarks, history, downloads) ---- */
        QListWidget, QTreeWidget {{
            background-color: {p['bg_elevated']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            padding: 4px;
            outline: none;
        }}
        QListWidget::item, QTreeWidget::item {{
            padding: 8px;
            border-radius: 6px;
        }}
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {p['accent']};
            color: white;
        }}
        QListWidget::item:hover, QTreeWidget::item:hover {{
            background-color: {p['border']};
        }}
        QHeaderView::section {{
            background-color: {p['bg_alt']};
            color: {p['text_dim']};
            border: none;
            padding: 6px;
        }}

        /* ---- Buttons ---- */
        QPushButton {{
            background-color: {p['bg_elevated']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            padding: 8px 16px;
            color: {p['text']};
        }}
        QPushButton:hover {{
            background-color: {p['border']};
        }}
        QPushButton#AccentButton {{
            background-color: {p['accent']};
            border: none;
            color: white;
            font-weight: 600;
        }}
        QPushButton#AccentButton:hover {{
            background-color: {p['accent_hover']};
        }}
        QPushButton#AccentButton:pressed {{
            background-color: {p['accent_pressed']};
        }}
        QPushButton#DangerButton {{
            background-color: transparent;
            border: 1px solid {p['danger']};
            color: {p['danger']};
        }}
        QPushButton#DangerButton:hover {{
            background-color: {p['danger']};
            color: white;
        }}

        QProgressBar#LoadProgress {{
            background-color: transparent;
            border: none;
            max-height: 3px;
        }}
        QProgressBar#LoadProgress::chunk {{
            background-color: {p['accent']};
        }}

        QLineEdit, QComboBox, QSpinBox {{
            background-color: {p['bg_elevated']};
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {p['text']};
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {p['accent']};
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid {p['border']};
            background-color: {p['bg_elevated']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {p['accent']};
            border: 1px solid {p['accent']};
        }}

        /* ---- Menus ---- */
        QMenu {{
            background-color: {p['bg_elevated']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 6px;
        }}
        QMenu::item:selected {{
            background-color: {p['accent']};
            color: white;
        }}
        QMenu::separator {{
            height: 1px;
            background: {p['border']};
            margin: 4px 8px;
        }}

        /* ---- Scrollbars ---- */
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {p['scrollbar']};
            border-radius: 5px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p['accent']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 10px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {p['scrollbar']};
            border-radius: 5px;
            min-width: 24px;
        }}

        QLabel#SectionTitle {{
            font-size: 16px;
            font-weight: 700;
            padding: 4px 0px;
        }}
        QLabel#MutedLabel {{
            color: {p['text_dim']};
        }}

        #StatusBar {{
            background-color: {p['bg_alt']};
            border-top: 1px solid {p['border']};
            color: {p['text_dim']};
        }}


        #SettingsRoot {{
            background-color: {p['bg']};
        }}
        #SettingsSidebar {{
            background-color: {p['bg_alt']};
            border-right: 1px solid {p['border']};
        }}
        #SettingsSidebar QPushButton {{
            text-align: left;
            background: transparent;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            color: {p['text_dim']};
            font-weight: 600;
            font-size: 13px;
        }}
        #SettingsSidebar QPushButton:hover {{
            background-color: {p['bg_elevated']};
            color: {p['text']};
        }}
        #SettingsSidebar QPushButton:checked {{
            background-color: {p['bg_elevated']};
            color: {p['accent']};
            border-left: 3px solid {p['accent']};
        }}
        #SettingsContent {{
            background-color: {p['bg']};
        }}
        QLabel#SettingsPageTitle {{
            font-size: 20px;
            font-weight: 700;
            padding-bottom: 4px;
        }}

        #DashboardCard {{
            background-color: {p['bg_elevated']};
            border: 1px solid {p['border']};
            border-radius: 10px;
        }}
        QLabel#DashboardCardValue {{
            font-size: 26px;
            font-weight: 700;
            color: {p['accent']};
        }}
        QLabel#DashboardCardLabel {{
            color: {p['text_dim']};
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        QLabel[pill="true"] {{
            border-radius: 10px;
            padding: 4px 12px;
            font-weight: 600;
            font-size: 12px;
        }}
        QLabel[pill="true"][pillState="connected"] {{
            color: {p['success']};
            background-color: rgba(46, 204, 113, 0.14);
        }}
        QLabel[pill="true"][pillState="connecting"] {{
            color: {p['warning']};
            background-color: rgba(230, 180, 0, 0.14);
        }}
        QLabel[pill="true"][pillState="error"] {{
            color: {p['danger']};
            background-color: rgba(231, 76, 60, 0.14);
        }}
        QLabel[pill="true"][pillState="idle"] {{
            color: {p['text_dim']};
            background-color: rgba(255, 255, 255, 0.06);
        }}

        /* ---- Settings buttons (secondary actions) ---- */
        QPushButton#SettingsSecondaryBtn {{
            background-color: {p['bg_elevated']};
            color: {p['text']};
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 7px 14px;
            font-weight: 600;
        }}
        QPushButton#SettingsSecondaryBtn:hover {{
            background-color: {p['bg_alt']};
            border-color: {p['accent']};
        }}
        QPushButton#SettingsDangerBtn {{
            background-color: transparent;
            color: {p['danger']};
            border: 1px solid {p['danger']};
            border-radius: 6px;
            padding: 7px 14px;
            font-weight: 600;
        }}
        QPushButton#SettingsDangerBtn:hover {{
            background-color: rgba(231, 76, 60, 0.12);
        }}
        """

    def new_tab_page_html(self, search_engine_url: str = "https://www.google.com/search?q=") -> str:

        p = self.palette
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                background: {p['bg']};
                color: {p['text']};
                font-family: "Segoe UI", "Inter", sans-serif;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }}
            .logo {{
                font-size: 42px;
                font-weight: 800;
                margin-bottom: 28px;
                letter-spacing: -1px;
            }}
            .logo span {{ color: {p['accent']}; }}
            .search-box {{
                width: 560px;
                max-width: 90vw;
                display: flex;
                background: {p['bg_elevated']};
                border: 1px solid {p['border']};
                border-radius: 24px;
                padding: 6px 8px;
            }}
            .search-box input {{
                flex: 1;
                background: transparent;
                border: none;
                outline: none;
                color: {p['text']};
                font-size: 15px;
                padding: 10px 14px;
            }}
            .search-box button {{
                background: {p['accent']};
                border: none;
                color: white;
                border-radius: 18px;
                padding: 10px 20px;
                cursor: pointer;
                font-weight: 600;
            }}
            .search-box button:hover {{ opacity: 0.9; }}
            .shortcuts {{
                display: flex;
                gap: 18px;
                margin-top: 40px;
                flex-wrap: wrap;
                justify-content: center;
            }}
            .shortcut {{
                width: 90px;
                height: 70px;
                background: {p['bg_elevated']};
                border: 1px solid {p['border']};
                border-radius: 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                text-decoration: none;
                color: {p['text']};
                font-size: 12px;
                transition: transform 0.15s ease;
            }}
            .shortcut:hover {{
                transform: translateY(-3px);
                border-color: {p['accent']};
            }}
            .shortcut .icon {{
                font-size: 20px;
                margin-bottom: 6px;
            }}
            .footer {{
                position: fixed;
                bottom: 16px;
                color: {p['text_dim']};
                font-size: 12px;
            }}
        </style>
        </head>
        <body>
            <div class="logo">Nova<span>Browser</span></div>
            <form class="search-box" onsubmit="search(event)">
                <input id="q" type="text" placeholder="Search the web or type a URL" autofocus>
                <button type="submit">Search</button>
            </form>
            <div class="shortcuts">
                <a class="shortcut" href="https://github.com"><div class="icon">&#128187;</div>GitHub</a>
                <a class="shortcut" href="https://youtube.com"><div class="icon">&#9654;</div>YouTube</a>
                <a class="shortcut" href="https://wikipedia.org"><div class="icon">&#128218;</div>Wikipedia</a>
                <a class="shortcut" href="https://reddit.com"><div class="icon">&#128172;</div>Reddit</a>
            </div>
            <div class="footer">NovaBrowser &mdash; built with PyQt6</div>
            <script>
                function search(e) {{
                    e.preventDefault();
                    const q = document.getElementById('q').value.trim();
                    if (!q) return false;
                    window.location.href = "{search_engine_url}" + encodeURIComponent(q);
                    return false;
                }}
            </script>
        </body>
        </html>
        """
