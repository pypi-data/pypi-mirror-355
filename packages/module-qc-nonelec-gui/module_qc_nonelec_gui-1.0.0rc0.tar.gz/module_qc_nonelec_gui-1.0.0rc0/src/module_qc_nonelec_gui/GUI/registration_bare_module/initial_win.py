from __future__ import annotations

import logging

from PyQt5.QtWidgets import QGridLayout, QLabel, QPushButton, QRadioButton, QWidget

log = logging.getLogger(__name__)


class InitialWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        layout = QGridLayout()
        self.menu = "NULL"

        label_text = QLabel()
        label_text.setText("Choose Menu")

        self.rb_bareregist = QRadioButton("Register Bare Module")
        self.rb_bareupdate = QRadioButton("Update Bare Module Info.")

        self.rb_bareregist.toggled.connect(self.onClicked)
        self.rb_bareupdate.toggled.connect(self.onClicked)

        button_next = QPushButton("&Next")
        button_next.clicked.connect(self.pass_menu)
        button_back = QPushButton("&Back")
        button_back.clicked.connect(self.back)

        layout.addWidget(label_text, 0, 0, 1, 2)
        layout.addWidget(self.rb_bareregist, 1, 0, 1, 2)
        layout.addWidget(self.rb_bareupdate, 2, 0, 1, 2)
        layout.addWidget(button_next, 3, 1, 1, 1)
        layout.addWidget(button_back, 3, 0, 1, 1)

        self.setLayout(layout)

    def onClicked(self):
        radiobtn = self.sender()
        if radiobtn.isChecked():
            if radiobtn.text() == "Register Bare Module":
                self.menu = "Register"
            elif radiobtn.text() == "Update Bare Module Info.":
                self.menu = "Update"

    def pass_menu(self):
        if self.menu == "Register":
            self.parent.bareregist()
        elif self.menu == "Update":
            self.parent.bareupdate()
        elif self.menu == "NULL":
            log.info("Please choose menu")

    def back(self):
        self.parent.parent.call_selectmode()
