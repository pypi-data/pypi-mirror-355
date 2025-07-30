from __future__ import annotations

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)


class ContinueWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        yn_box = QHBoxLayout()
        yn_hbox = QHBoxLayout()
        where_box = QHBoxLayout()
        where_vbox = QVBoxLayout()
        button_box = QHBoxLayout()

        label_text = QLabel()
        label_text.setText(
            '<center><font size="6">Choose the options you want</font></center>'
        )

        button = QPushButton("&Continue")
        button.clicked.connect(self.restart_test)
        fin_button = QPushButton("&Finish")
        fin_button.clicked.connect(self.finishGUI)

        button_box.addWidget(fin_button)
        button_box.addStretch()
        button_box.addWidget(button)

        raddio_yes = self.make_radiobutton("Yes")
        raddio_yes.setChecked(True)
        raddio_no = self.make_radiobutton("No")
        self.yn_radio_group = QButtonGroup()
        self.yn_radio_group.addButton(raddio_yes, 0)
        self.yn_radio_group.addButton(raddio_no, 1)

        yn_hbox.addWidget(raddio_yes)
        yn_hbox.addWidget(raddio_no)

        yn_box.addStretch()
        yn_box.addLayout(yn_hbox)
        yn_box.addStretch()

        yn_group = QGroupBox("Will you inspect as the same user?")
        yn_group.setStyleSheet("QGroupBox { font-size: 15px;font-weight: bold;} ")
        yn_group.setLayout(yn_box)

        raddio_test = self.make_radiobutton("same component")
        raddio_test.setChecked(True)
        raddio_comp = self.make_radiobutton("different component")
        self.where_radio_group = QButtonGroup()
        self.where_radio_group.addButton(raddio_test, 0)
        self.where_radio_group.addButton(raddio_comp, 1)

        where_vbox.addWidget(raddio_test)
        where_vbox.addWidget(raddio_comp)
        where_box.addStretch()
        where_box.addLayout(where_vbox)
        where_box.addStretch()

        where_group = QGroupBox("Which component will you inspect?")
        where_group.setStyleSheet("QGroupBox { font-size: 15px;font-weight: bold;} ")
        where_group.setLayout(where_box)

        layout.addWidget(label_text)
        layout.addStretch()
        layout.addWidget(yn_group)
        layout.addStretch()
        layout.addWidget(where_group)
        layout.addStretch()
        layout.addLayout(button_box)

        self.setLayout(layout)

    def make_radiobutton(self, label):
        radiobutton = QRadioButton(label)
        radiobutton.setCheckable(True)
        radiobutton.setFocusPolicy(Qt.NoFocus)
        radiobutton.setStyleSheet(
            "QRadioButton{font: 12pt;} QRadioButton::indicator { width: 12px; height: 12px;};"
        )
        return radiobutton

    def finishGUI(self):
        self.parent.finish_GUI()

    def restart_test(self):
        try:
            log.info(
                "[Next Inspection] same user : "
                + self.yn_radio_group.checkedButton().text()
            )
            log.info(
                "[Next Inspection] target    : "
                + self.where_radio_group.checkedButton().text()
            )
            self.parent.restart(
                self.yn_radio_group.checkedId(), self.where_radio_group.checkedId()
            )
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Please check each radiobutton.", QMessageBox.Ok
            )
