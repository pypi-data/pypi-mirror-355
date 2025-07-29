#!/usr/bin/env python3
# temp_py.py created on Sat Jun 14 12:41:55 AM CDT 2025

import sys
import json
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QComboBox, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from abstract_apis import getRequest, postRequest

# ─── Logging Handler ──────────────────────────────────────────────────────
class QTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.widget.setReadOnly(True)
    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)
        self.widget.ensureCursorVisible()

# ─── Worker Thread ────────────────────────────────────────────────────────
class APIWorker(QObject):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, method, url, headers, data):
        super().__init__()
        self.method  = method
        self.url     = url
        self.headers = headers or {}
        self.data    = data or {}

    def run(self):
        try:
            if self.method == "GET":
                result = getRequest(url=self.url, headers=self.headers, data=self.data)
            else:
                result = postRequest(url=self.url, headers=self.headers, data=self.data)
            logging.info(f"✔ Response received")
            self.finished.emit(result)
        except Exception as e:
            logging.error(f"✖ Request failed: {e}")
            self.error.emit(str(e))

# ─── Async Client ────────────────────────────────────────────────────────
class APIClient(QObject):
    responseReceived = pyqtSignal(object)
    requestFailed    = pyqtSignal(str)

    def get(self, url, headers=None, data=None):
        logging.debug(f"→ GET {url} params={data}")
        self._start_thread("GET", url, headers, data)

    def post(self, url, headers=None, data=None):
        logging.debug(f"→ POST {url} body={data}")
        self._start_thread("POST", url, headers, data)

    def _start_thread(self, method, url, headers, data):
        thread = QThread(self)
        worker = APIWorker(method, url, headers, data)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self.responseReceived.emit)
        worker.error.connect(self.requestFailed.emit)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.start()

# ─── Main GUI ─────────────────────────────────────────────────────────────
class APIConsole(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Console (uses abstract_apis)")
        self.resize(800, 800)
        
        # Inputs
        self.url_input     = QLineEdit()
        self.method_box    = QComboBox(); self.method_box.addItems(["GET", "POST"])
        self.headers_input = QTextEdit()
        self.body_input    = QTextEdit()
        self.send_button   = QPushButton("Send Request")

        # Outputs
        self.response_output = QTextEdit()
        self.log_output      = QTextEdit()

        self._build_layout()
        self._setup_logging()

        self.client = APIClient()
        self.client.responseReceived.connect(self.show_response)
        self.client.requestFailed.connect(self.show_error)
        self.send_button.clicked.connect(self.send_request)

    def _build_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("URL:"))
        layout.addWidget(self.url_input)

        mrow = QHBoxLayout()
        mrow.addWidget(QLabel("Method:"))
        mrow.addWidget(self.method_box)
        layout.addLayout(mrow)

        layout.addWidget(QLabel("Headers (JSON):"))
        layout.addWidget(self.headers_input)

        layout.addWidget(QLabel("Body (JSON for POST / query params for GET):"))
        layout.addWidget(self.body_input)

        layout.addWidget(self.send_button)

        layout.addWidget(QLabel("Response:"))
        self.response_output.setReadOnly(True)
        layout.addWidget(self.response_output)

        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def _setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        handler = QTextEditLogger(self.log_output)
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    def send_request(self):
        url    = self.url_input.text().strip()
        method = self.method_box.currentText()
        headers_txt = self.headers_input.toPlainText()
        body_txt    = self.body_input.toPlainText()

        try:
            headers = json.loads(headers_txt) if headers_txt else {}
            data    = json.loads(body_txt)    if body_txt    else {}
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", str(e))
            return

        logging.info(f"↪ Sending {method} request")
        self.response_output.setText("…waiting for response…")

        if method == "GET":
            self.client.get(url, headers=headers, data=data)
        else:
            self.client.post(url, headers=headers, data=data)

    def show_response(self, result):
        if isinstance(result, dict):
            text = json.dumps(result, indent=4)
        else:
            text = str(result)
        self.response_output.setText(text)

    def show_error(self, error):
        self.response_output.setText(f"Error: {error}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = APIConsole()
    win.show()
    sys.exit(app.exec_())
