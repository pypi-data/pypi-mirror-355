#!/usr/bin/env python3
# temp_py.py — simple GUI front-end for abstract_apis

import sys
import json
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QComboBox, QHBoxLayout, QMessageBox
)
from abstract_apis import getRequest, postRequest

# ─── Logging Handler to a QTextEdit ────────────────────────────────────
class QTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.widget.setReadOnly(True)
    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)
        self.widget.ensureCursorVisible()

# ─── Main GUI ─────────────────────────────────────────────────────────
class APIConsole(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Console for abstract_apis")
        self.resize(700, 600)
        self._build_ui()
        self._setup_logging()

    def _build_ui(self):
        self.url_input       = QLineEdit("https://")
        self.method_box      = QComboBox(); self.method_box.addItems(["GET", "POST"])
        self.headers_input   = QTextEdit("{}")
        self.body_input      = QTextEdit("{}")
        self.send_button     = QPushButton("▶ Send")
        self.response_output = QTextEdit()
        self.log_output      = QTextEdit()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("URL"))
        layout.addWidget(self.url_input)

        row = QHBoxLayout()
        row.addWidget(QLabel("Method"))
        row.addWidget(self.method_box)
        layout.addLayout(row)

        layout.addWidget(QLabel("Headers (JSON)"))
        layout.addWidget(self.headers_input)

        layout.addWidget(QLabel("Body / Query-Params (JSON)"))
        layout.addWidget(self.body_input)

        layout.addWidget(self.send_button)
        layout.addWidget(QLabel("Response"))
        layout.addWidget(self.response_output)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.log_output)
        self.setLayout(layout)

        self.send_button.clicked.connect(self.send_request)

    def _setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        h = QTextEditLogger(self.log_output)
        h.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S'))
        logger.addHandler(h)

    def send_request(self):
        url    = self.url_input.text().strip()
        method = self.method_box.currentText()
        try:
            headers = json.loads(self.headers_input.toPlainText())
            data    = json.loads(self.body_input.toPlainText())
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", str(e))
            return

        logging.info(f"Sending {method} {url}  headers={headers}  data={data}")
        self.response_output.clear()

        try:
            if method == "GET":
                result = getRequest(url=url, headers=headers, data=data)
            else:
                result = postRequest(url=url, headers=headers, data=data)
            # show pretty JSON if possible
            if isinstance(result, dict):
                text = json.dumps(result, indent=4)
            else:
                text = str(result)
            self.response_output.setPlainText(text)
            logging.info("✔ Response displayed")
        except Exception as ex:
            err = f"✖ Error: {ex}"
            self.response_output.setPlainText(err)
            logging.error(err)


def run_abstract_api_gui():
    app = QApplication(sys.argv)
    win = APIConsole()
    win.show()
    sys.exit(app.exec_())
