from __future__ import annotations

import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SetupWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        button_box = QHBoxLayout()

        label_text = QLabel()
        label_text.setText('<center><font size="6">Initial Setup</font></center>')

        label_localdb_protocol = QLabel()
        label_localdb_protocol.setText("LocalDB Protocol (http or https):")

        self.edit_localdb_protocol = QLineEdit()
        self.edit_localdb_protocol.setText("http")

        label_localdb_host = QLabel()
        label_localdb_host.setText("LocalDB Hostname:")

        self.edit_localdb_host = QLineEdit()
        self.edit_localdb_host.setText("127.0.0.1")

        label_localdb_port = QLabel()
        label_localdb_port.setText("LocalDB Port:")

        self.edit_localdb_port = QLineEdit()
        self.edit_localdb_port.setText("5000")

        label_mongodb_host = QLabel()
        label_mongodb_host.setText("MongoDB Hostname:")

        self.edit_mongodb_host = QLineEdit()
        self.edit_mongodb_host.setText("127.0.0.1")

        label_mongodb_port = QLabel()
        label_mongodb_port.setText("MongoDB Port:")

        self.edit_mongodb_port = QLineEdit()
        self.edit_mongodb_port.setText("27017")

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.register_setup)

        button_box.addStretch()
        button_box.addWidget(Next_button)

        form_layout.addRow(label_localdb_protocol, self.edit_localdb_protocol)
        form_layout.addRow(label_localdb_host, self.edit_localdb_host)
        form_layout.addRow(label_localdb_port, self.edit_localdb_port)
        form_layout.addRow(label_mongodb_host, self.edit_mongodb_host)
        form_layout.addRow(label_mongodb_port, self.edit_mongodb_port)

        layout.addStretch()
        layout.addWidget(label_text)
        layout.addStretch()
        layout.addLayout(form_layout)
        layout.addLayout(button_box)

        self.setLayout(layout)

    def register_setup(self):
        with Path(
            self.parent.module_qc_nonelec_gui_dir + "/configuration/custom.json"
        ).open(mode="w", encoding="utf-8") as f:
            j = {
                "mongoDB": {
                    "address": self.edit_mongodb_host.text(),
                    "port": self.edit_mongodb_port.text(),
                },
                "localDB_web": {
                    "protocol": self.edit_localdb_protocol.text(),
                    "address": self.edit_localdb_host.text(),
                    "port": self.edit_localdb_port.text(),
                },
            }

            json.dump(j, f, indent=4)

        self.close()
        self.parent.init_ui()
