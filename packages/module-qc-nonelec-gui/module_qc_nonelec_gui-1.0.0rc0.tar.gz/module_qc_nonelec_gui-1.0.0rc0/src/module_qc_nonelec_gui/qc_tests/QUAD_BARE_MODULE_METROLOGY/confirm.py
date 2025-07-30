from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConfirmWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        titlebox = QVBoxLayout()
        layout = QVBoxLayout()
        button_box = QHBoxLayout()
        inner_box = QVBoxLayout()

        label_title = QLabel()
        label_title.setText(
            '<center><font size="5">Confirm before uploading to the database</font></center>'
        )
        label_practice = QLabel()
        label_practice.setText(
            '<center><font size="4" color = "green"> Practice Mode</font></center>'
        )

        Upload_button = QPushButton("&Upload!")
        Upload_button.clicked.connect(self.upload_to_db)
        json_button = QPushButton("&Check json (for expert)")
        json_button.clicked.connect(self.check_json)
        back_button = QPushButton("&Back")
        back_button.clicked.connect(self.back_page)

        titlebox.addWidget(label_title)

        button_box.addWidget(back_button)
        button_box.addStretch()
        button_box.addWidget(json_button)
        button_box.addWidget(Upload_button)

        inner = QScrollArea()
        inner.setFixedWidth(600)
        inner.setFixedHeight(600)
        result_wid = QWidget()
        result_wid.setLayout(self.make_layout())

        inner.setWidgetResizable(True)
        inner.setWidget(result_wid)
        inner_box.addWidget(inner)

        layout.addLayout(titlebox)
        layout.addLayout(inner_box)
        layout.addLayout(button_box)

        self.setLayout(layout)

    def back_page(self):
        self.parent.back_to_test()

    def check_json(self):
        self.parent.confirm_json()

    def upload_to_db(self):
        self.parent.upload_to_db()

    def add_info(self, Form_layout, label_str, form_text):
        label = QLabel()
        label.setText(label_str)

        if label_str.lower().find("comment") > 0:
            inner = QTextEdit()
            inner.setText(form_text)
            inner.setReadOnly(True)
            inner.setFocusPolicy(Qt.NoFocus)
            inner.setStyleSheet("background-color : linen; color: black;")

            editor = QScrollArea()
            editor.setWidgetResizable(True)
            editor.setWidget(inner)

        else:
            editor = QLineEdit()
            editor.setFixedWidth(400)
            editor.setText(form_text)
            editor.setReadOnly(True)
            editor.setFocusPolicy(Qt.NoFocus)
            editor.setStyleSheet("background-color : linen; color: black;")

        Form_layout.addRow(label, editor)

    #################################################################
    def make_layout(self):
        if (
            self.parent.info_dict["componentType"] == "BARE_MODULE"
            or self.parent.info_dict["componentType"] == "practice"
        ):
            return self.layout_ModuleQC()
        return self.layout_ModuleQC()

    def layout_ModuleQC(self):
        HBox = QHBoxLayout()

        Form_layout = QFormLayout()

        for k, v in self.parent.testRun.items():
            if k not in ["results"]:
                self.add_info(Form_layout, f"{k[:1].upper()+k[1:]} :", str(v))

        for container in ["results"]:
            if container not in self.parent.testRun:
                continue

            keylist = []

            for k, v in self.parent.testRun.get(container).items():
                if k not in [
                    "results",
                    "metadata",
                    "Metadata",
                    "Measurements",
                    "properties",
                    "property",
                ]:
                    if k not in keylist:
                        self.add_info(Form_layout, f"{k[:1].upper()+k[1:]} :", str(v))
                        keylist.append(k)
                else:
                    for k2, v2 in self.parent.testRun.get(container).get(k).items():
                        if k2 not in keylist:
                            self.add_info(
                                Form_layout, f"{k2[:1].upper()+k2[1:]} :", str(v2)
                            )
                            keylist.append(k2)

        HBox.addLayout(Form_layout)

        return HBox
