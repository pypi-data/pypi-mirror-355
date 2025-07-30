from __future__ import annotations

import logging
import pprint
import traceback

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)


class ChooseTestWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        label_choosetest = QLabel()
        label_choosetest.setText('<center><font size="6"> Select Test</font></center>')

        next_button = QPushButton("&Next")
        next_button.clicked.connect(self.next_page)
        back_button = QPushButton("&Back")
        back_button.clicked.connect(self.back_page)

        button_box = QHBoxLayout()

        layout = QVBoxLayout()
        info_layout = self.make_layout()

        button_box.addWidget(back_button)
        button_box.addStretch()
        button_box.addWidget(next_button)

        layout.addWidget(label_choosetest)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(self.make_testlist())
        layout.addStretch()
        layout.addLayout(button_box)
        self.setLayout(layout)

        stage = self.parent.info_dict["stage"]
        if len(self.parent.test_dict[stage]) == 0:
            msg = f"For the component {self.parent.info_dict['component']}, there are no tests which can be submitted in the current stage \"{self.parent.info_dict['stage']}\"."
            raise RuntimeError(msg)

    def next_page(self):
        title = self.select_test()
        stage = self.parent.info_dict["stage"]

        testCode = self.parent.test_dict.get(stage).get(title)

        self.parent.receive_testtype(testCode)

    def back_page(self):
        self.parent.back_from_choosetest()

    def make_testlist(self):
        layout = QHBoxLayout()

        radio_box = QGridLayout()

        label_test = QLabel()
        label_test.setText('<center><font size="3"> Test name</font></center>')
        label_uploaded = QLabel()
        label_uploaded.setText(
            '<center><font size="3"> Upload status in localDB</font></center>'
        )

        self.radiobutton_list = []
        self.radio_group = QButtonGroup()
        check = []
        label_detail = []

        radio_box.addWidget(label_test, 0, 0)
        radio_box.addWidget(label_uploaded, 0, 1)

        stage = self.parent.info_dict["stage"]

        for i, test_title in enumerate(self.parent.test_dict[stage].keys()):
            check.append(QLineEdit())
            label_detail.append(MyLabel())

            self.radiobutton_list.append(self.make_radiobutton(test_title))
            # hack
            if (
                self.parent.test_dict[stage][test_title] == "OPTICAL"
                and self.parent.atlsn == ""
                and self.parent.VI_grayout_with_emptyATLSN
            ):
                self.radiobutton_list[i].setStyleSheet(
                    "QRadioButton{font: 15pt; color:gray} QRadioButton::indicator { width: 15px; height: 15px; color:gray};"
                )
                self.radiobutton_list[i].setCheckable(False)

            self.radio_group.addButton(self.radiobutton_list[i], i)
            self.check_uploaded(
                self.parent.test_dict[stage][test_title], check[i], label_detail[i]
            )

            if i == 0:
                self.radiobutton_list[i].setChecked(True)

            radio_box.addWidget(self.radiobutton_list[i], i + 1, 0)
            radio_box.addWidget(check[i], i + 1, 1)
            radio_box.addWidget(label_detail[i], i + 1, 2)

        layout.addStretch()
        layout.addLayout(radio_box)
        layout.addStretch()

        log.info("end of make_testlist")

        return layout

    def check_uploaded(self, test_to_check, form_text, _label_text):
        form_text.setAttribute(Qt.WA_TransparentForMouseEvents)
        form_text.setFocusPolicy(Qt.NoFocus)
        form_text.setAlignment(Qt.AlignCenter)
        form_text.setFixedWidth(150)

        if self.parent.isPractice:
            form_text.setStyleSheet("color: rgb black; background-color:linen;")
            status = "Practice"
        else:
            try:
                stage = self.parent.info_dict["stage"]
                status = self.parent.qcStatus["QC_results"][stage][test_to_check]
                log.info("check_uploaded(): " + pprint.pformat(test_to_check))
                log.info("check_uploaded(): " + pprint.pformat(status))

                if status != "-1":
                    form_text.setStyleSheet("color: black; background-color:linen;")
                    status = "Already uploaded"
                else:
                    form_text.setStyleSheet("color: red; background-color:linen;")
                    status = "N/A"

            except IndexError:
                form_text.setStyleSheet("color: red; background-color:linen;")
                status = "None"
            except Exception:
                form_text.setStyleSheet("color: rgb black; background-color:linen;")
                log.exception(traceback.format_exc())
                status = "Error"
        form_text.setText(status)

    def make_radiobutton(self, label):
        radiobutton = QRadioButton(label)
        radiobutton.setCheckable(True)
        radiobutton.setFocusPolicy(Qt.NoFocus)
        radiobutton.setStyleSheet(
            "QRadioButton{font: 15pt;} QRadioButton::indicator { width: 15px; height: 15px;};"
        )

        try:
            if label == self.parent.info_dict["testType"]:
                radiobutton.setChecked(True)
        except Exception:
            pass
        return radiobutton

    def select_test(self):
        try:
            log.info("select_test(): " + self.radio_group.checkedButton().text())
            return self.radio_group.checkedButton().text()
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Please choose test you want to do", QMessageBox.Ok
            )
            return -1

    def make_layout(self):
        layout = QHBoxLayout()
        vlayout = QGridLayout()

        self.make_infotable(
            vlayout, "Serial Number", self.parent.info_dict["component"], 0
        )
        self.make_infotable(
            vlayout, "Component Type", self.parent.info_dict["componentType"], 1
        )
        self.make_infotable(vlayout, "Test Stage", self.parent.localDB_dict["stage"], 2)

        widget = QWidget()
        widget.setLayout(vlayout)
        widget.setObjectName("widget")
        widget.setStyleSheet("#widget{border: 1px solid black;}")

        layout.addStretch()
        layout.addWidget(widget)
        layout.addStretch()

        return layout

    def make_infotable(self, Grid_layout, str_label, str_info, i):
        label_text = QLabel()
        label_text.setText('<font size="4">' + str_label + "</font>")
        label_sep = QLabel()
        label_sep.setText('<font size="4">:</font>')
        info_text = QLabel()
        info_text.setText('<font size="4">' + str_info + "</font>")

        Grid_layout.addWidget(label_text, i, 0)
        Grid_layout.addWidget(label_sep, i, 1)
        Grid_layout.addWidget(info_text, i, 2)


class MyLabel(QLabel):
    mouse_entered = pyqtSignal()
    mouse_left = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(QLabel, self).__init__(parent)

    def enterEvent(self, _event):
        self.mouse_entered.emit()

    def leaveEvent(self, _event):
        self.mouse_left.emit()

    def mouseReleaseEvent(self, _event):
        self.clicked.emit()
