from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
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
        if self.parent.isPractice:
            titlebox.addWidget(label_practice)

        button_box.addWidget(back_button)
        button_box.addStretch()
        button_box.addWidget(json_button)
        button_box.addWidget(Upload_button)

        inner = QScrollArea()
        result_wid = QWidget()
        result_wid.setLayout(self.layout_ModuleQC())

        inner.setWidgetResizable(True)
        inner.setWidget(result_wid)

        layout.addLayout(titlebox)
        layout.addWidget(inner)
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

        if label_str == "Comment :":
            inner = QTextEdit()
            inner.setText(form_text)
            inner.setReadOnly(True)
            inner.setFocusPolicy(Qt.NoFocus)
            inner.setStyleSheet("background-color : linen; color: black")

            editor = QScrollArea()
            editor.setWidgetResizable(True)
            editor.setWidget(inner)

        else:
            editor = QLineEdit()
            editor.setText(form_text)
            editor.setReadOnly(True)
            editor.setFocusPolicy(Qt.NoFocus)
            editor.setFixedWidth(350)
            editor.setStyleSheet("background-color : linen; color: black")

        Form_layout.addRow(label, editor)

    #################################################################
    def layout_ModuleQC(self):
        Form_layout = self.parent.confirm_layout_common(self)

        for prop_code in ["OPERATOR_IDENTITY", "INSTRUMENT"]:
            self.add_info(
                Form_layout,
                prop_code.lower().capitalize() + " : ",
                self.parent.testRun["results"]["property"][prop_code],
            )

        for index, pull_data in enumerate(
            self.parent.testRun["results"]["Metadata"]["pull_data"]
        ):
            self.add_info(
                Form_layout,
                f"Wire #{index+1} : ",
                f"Strength: {pull_data['strength']}, Break Mode: {pull_data['break_mode']}",
            )

        self.add_info(
            Form_layout, "Comment :", self.parent.testRun["results"]["comment"]
        )

        return Form_layout
