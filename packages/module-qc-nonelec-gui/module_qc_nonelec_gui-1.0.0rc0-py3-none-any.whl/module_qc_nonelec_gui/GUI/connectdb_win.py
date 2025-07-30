from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ConnectDBWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        self.setMinimumWidth(340)
        self.setMinimumHeight(200)

        layout = QVBoxLayout()
        hbox_bottom = QHBoxLayout()
        edit_form = QFormLayout()
        form_box = QHBoxLayout()

        label_text = QLabel()
        label_text.setText('<center><font size="7">Log in to Local DB</font></center>')
        label_user = QLabel()
        label_user.setText("User:")
        label_password = QLabel()
        label_password.setText("Password:")

        self.edit_user = QLineEdit()
        self.edit_user.setText(self.parent.db_user)
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit().Password)

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.go_to_modqc)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        hbox_bottom.addWidget(Back_button)
        hbox_bottom.addStretch()
        hbox_bottom.addWidget(Next_button)

        edit_form.addRow(label_user, self.edit_user)
        edit_form.addRow(label_password, self.edit_password)

        form_box.addLayout(edit_form)

        layout.addStretch()
        layout.addWidget(label_text)
        layout.addStretch()
        layout.addLayout(form_box)
        layout.addLayout(hbox_bottom)

        self.setLayout(layout)

    def go_to_modqc(self):
        self.parent.receive_db_user(self.edit_user.text(), self.edit_password.text())

    def back_page(self):
        self.parent.init_ui()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.go_to_modqc()
