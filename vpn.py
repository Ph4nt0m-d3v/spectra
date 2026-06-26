from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox
)
from PyQt6.QtNetwork import QNetworkProxy, QTcpSocket

MIN_PORT = 1
MAX_PORT = 65535
TEST_CONNECTION_TIMEOUT_MS = 4000


class VPNManager(QWidget):


    connection_changed = pyqtSignal(bool)


    state_changed = pyqtSignal(str)

    def __init__(self, browser=None):
        super().__init__()

        self.browser = browser
        self.connected = False
        self.state = "idle"
        self.setObjectName("VPNPanel")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(10)

        header = QLabel("Proxy / VPN")
        header.setObjectName("VPNHeader")
        self.layout.addWidget(header)

        self.status_label = QLabel("Disconnected")
        self.status_label.setObjectName("VPNStatusLabel")
        self.status_label.setProperty("state", "idle")
        self.layout.addWidget(self.status_label)

        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["HTTP", "SOCKS5"])
        self.layout.addWidget(self.proxy_type)

        host_row = QHBoxLayout()
        host_row.setSpacing(6)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Proxy host or IP")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port")
        self.port_input.setFixedWidth(70)
        host_row.addWidget(self.ip_input, stretch=1)
        host_row.addWidget(self.port_input)
        self.layout.addLayout(host_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(6)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("VPNConnectBtn")
        self.connect_btn.clicked.connect(self.toggle_vpn)
        button_row.addWidget(self.connect_btn, stretch=1)

        self.reconnect_btn = QPushButton("Reconnect")
        self.reconnect_btn.setObjectName("VPNReconnectBtn")
        self.reconnect_btn.setToolTip("Disconnect and reconnect using the current settings")
        self.reconnect_btn.clicked.connect(self.reconnect)
        button_row.addWidget(self.reconnect_btn)
        self.layout.addLayout(button_row)


        self.ip_input.returnPressed.connect(self._handle_return_pressed)
        self.port_input.returnPressed.connect(self._handle_return_pressed)

        self.setStyleSheet(self._local_stylesheet())


    @property
    def isEnabled(self):
        return self.connected

    def _handle_return_pressed(self):
        if not self.connected:
            self.connect_proxy()

    def toggle_vpn(self):
        if self.connected:
            self.disconnect_proxy()
        else:
            self.connect_proxy()


    def connect_proxy(self) -> bool:
        ip = self.ip_input.text().strip()
        port_text = self.port_input.text().strip()

        if not ip or not port_text:
            self._set_status("Enter a host and port", "error")
            return False

        try:
            port = int(port_text)
        except ValueError:
            self._set_status("Port must be a number", "error")
            return False

        if not (MIN_PORT <= port <= MAX_PORT):
            self._set_status(f"Port must be {MIN_PORT}-{MAX_PORT}", "error")
            return False

        self._set_status(f"Connecting to {ip}:{port}…", "connecting")
        self.connect_btn.setEnabled(False)

        proxy = QNetworkProxy()
        if self.proxy_type.currentText() == "HTTP":
            proxy.setType(QNetworkProxy.ProxyType.HttpProxy)
        else:
            proxy.setType(QNetworkProxy.ProxyType.Socks5Proxy)

        proxy.setHostName(ip)
        proxy.setPort(port)

        QNetworkProxy.setApplicationProxy(proxy)


        try:
            if self.browser:
                if hasattr(self.browser, "normal_profile"):
                    self.browser.normal_profile.setProxy(proxy)
                if hasattr(self.browser, "incognito_profile"):
                    self.browser.incognito_profile.setProxy(proxy)
        except Exception as e:
            print("WebEngine proxy hook failed:", e)

        test = QNetworkProxy.applicationProxy()
        if test.hostName() != ip or test.port() != port:
            self._set_status("Failed to apply proxy", "error")
            self.connected = False
            self.connect_btn.setEnabled(True)
            self.connection_changed.emit(False)
            return False

        if test.type() == QNetworkProxy.ProxyType.NoProxy:
            self._set_status("Proxy rejected by system", "error")
            self.connected = False
            self.connect_btn.setEnabled(True)
            self.connection_changed.emit(False)
            return False

        self.connected = True
        self._set_status(f"Connected to {ip}:{port}", "connected")
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Disconnect")

        if self.browser and hasattr(self.browser, "statusBar"):
            self.browser.statusBar().showMessage(f"VPN active: {ip}:{port}", 4000)

        self.connection_changed.emit(True)
        return True

    def disconnect_proxy(self) -> bool:
        QNetworkProxy.setApplicationProxy(QNetworkProxy())

        try:
            if self.browser:
                if hasattr(self.browser, "normal_profile"):
                    self.browser.normal_profile.setProxy(QNetworkProxy())
                if hasattr(self.browser, "incognito_profile"):
                    self.browser.incognito_profile.setProxy(QNetworkProxy())
        except Exception as e:
            print("WebEngine reset failed:", e)

        was_connected = self.connected
        self.connected = False
        self._set_status("Disconnected", "idle")
        self.connect_btn.setText("Connect")

        if self.browser and hasattr(self.browser, "statusBar"):
            self.browser.statusBar().showMessage("VPN disconnected", 4000)

        if was_connected:
            self.connection_changed.emit(False)
        return True


    def reconnect(self) -> bool:
        if self.connected:
            self.disconnect_proxy()
        return self.connect_proxy()


    def test_connection(self, on_result=None):

        ip = self.ip_input.text().strip()
        port_text = self.port_input.text().strip()

        if not ip or not port_text:
            msg = "Enter a host and port to test"
            self._flash_test_result(False, msg)
            if on_result:
                on_result(False, msg)
            return

        try:
            port = int(port_text)
            if not (MIN_PORT <= port <= MAX_PORT):
                raise ValueError
        except ValueError:
            msg = f"Port must be {MIN_PORT}-{MAX_PORT}"
            self._flash_test_result(False, msg)
            if on_result:
                on_result(False, msg)
            return

        self._set_status(f"Testing {ip}:{port}…", "connecting")

        socket = QTcpSocket(self)

        def finish(success: bool, message: str):
            socket.deleteLater()
            self._flash_test_result(success, message)
            if on_result:
                on_result(success, message)

        socket.connected.connect(lambda: finish(True, f"{ip}:{port} is reachable"))
        socket.errorOccurred.connect(
            lambda _err: finish(False, f"Could not reach {ip}:{port}")
        )

        timeout = QTimer(self)
        timeout.setSingleShot(True)
        timeout.timeout.connect(lambda: finish(False, f"Timed out reaching {ip}:{port}"))
        timeout.start(TEST_CONNECTION_TIMEOUT_MS)
        socket.connected.connect(timeout.stop)
        socket.errorOccurred.connect(timeout.stop)

        socket.connectToHost(ip, port)

    def _flash_test_result(self, success: bool, message: str):
        self._set_status(message, "connected" if success else "error")
        QTimer.singleShot(2500, self._restore_real_status)

    def _restore_real_status(self):
        if self.connected:
            ip = self.ip_input.text().strip()
            port = self.port_input.text().strip()
            self._set_status(f"Connected to {ip}:{port}", "connected")
        else:
            self._set_status("Disconnected", "idle")

    def current_proxy_info(self) -> dict:
        return {
            "connected": self.connected,
            "state": self.state,
            "host": self.ip_input.text().strip(),
            "port": self.port_input.text().strip(),
            "type": self.proxy_type.currentText(),
        }


    def _set_status(self, text: str, state: str):
        self.state = state
        self.status_label.setText(text)
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.state_changed.emit(state)

    @staticmethod
    def _local_stylesheet() -> str:

        return """
            #VPNPanel {
                background-color: #2b2b33;
                border: 1px solid #44444e;
                border-radius: 8px;
            }
            #VPNHeader {
                color: #f0f0f5;
                font-weight: 600;
                font-size: 13px;
            }
            #VPNStatusLabel {
                color: #9a9aa5;
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.06);
            }
            #VPNStatusLabel[state="connected"] {
                color: #2ecc71;
                background-color: rgba(46, 204, 113, 0.12);
            }
            #VPNStatusLabel[state="connecting"] {
                color: #e6b400;
                background-color: rgba(230, 180, 0, 0.12);
            }
            #VPNStatusLabel[state="error"] {
                color: #e74c3c;
                background-color: rgba(231, 76, 60, 0.12);
            }
            QLineEdit, QComboBox {
                background-color: #1f1f26;
                color: #f0f0f5;
                border: 1px solid #44444e;
                border-radius: 6px;
                padding: 5px 8px;
            }
            #VPNConnectBtn {
                background-color: #3a7afe;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 7px 10px;
                font-weight: 600;
            }
            #VPNConnectBtn:hover {
                background-color: #5b91ff;
            }
            #VPNConnectBtn:disabled {
                background-color: #2c2c36;
                color: #6e6e78;
            }
            #VPNReconnectBtn {
                background-color: transparent;
                color: #f0f0f5;
                border: 1px solid #44444e;
                border-radius: 6px;
                padding: 7px 10px;
                font-weight: 600;
            }
            #VPNReconnectBtn:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """
