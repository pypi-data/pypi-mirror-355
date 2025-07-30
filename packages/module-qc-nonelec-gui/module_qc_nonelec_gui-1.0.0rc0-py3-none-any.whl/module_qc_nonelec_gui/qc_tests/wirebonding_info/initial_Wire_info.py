from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class InitialWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        layout = QVBoxLayout()
        bottom_box = QHBoxLayout()
        grid_edit = QGridLayout()

        label_title = QLabel()
        label_title.setText(
            '<center><font size="7">Input Wirebonding information</font></center>'
        )

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.pass_result)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        bottom_box.addWidget(Back_button)
        bottom_box.addStretch()
        bottom_box.addWidget(Next_button)

        label_comment = QLabel()
        label_comment.setText("comment : ")
        label_roomTemp = QLabel()
        label_roomTemp.setText("Room temperature : ")
        label_humidity = QLabel()
        label_humidity.setText("Humidity : ")

        self.edit_comment = QTextEdit()
        self.edit_comment.setText(self.parent.result_info["comment"])

        self.edit_machine = self.make_textform(
            "Machine used : ", self.parent.result_info["Machine"], grid_edit, 0
        )
        self.edit_operator = self.make_textform(
            "Operator Name : ", self.parent.result_info["Operator"], grid_edit, 1
        )
        self.edit_institution = self.make_inscombo(
            "Institution of Operator : ",
            self.parent.result_info["Institution_of_operator"],
            grid_edit,
            2,
        )
        self.edit_batch = self.make_textform(
            "Bond wire batch : ", self.parent.result_info["batch"], grid_edit, 3
        )
        self.edit_jig = self.make_textform(
            "Bonding jig : ", self.parent.result_info["jig"], grid_edit, 4
        )

        self.edit_program = self.select_file_layout(
            "Bond program : ", self.parent.result_info["program_path"], grid_edit, 5
        )

        grid_edit.addWidget(label_roomTemp, 6, 0)
        grid_edit.addLayout(self.make_roomTemp_layout(), 6, 1)

        grid_edit.addWidget(label_humidity, 7, 0)
        grid_edit.addLayout(self.make_humidity_layout(), 7, 1)

        grid_edit.addWidget(label_comment, 8, 0)

        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setWidget(self.edit_comment)
        grid_edit.addWidget(outer, 8, 1)

        layout.addWidget(label_title)
        layout.addStretch()
        layout.addLayout(grid_edit)
        layout.addLayout(bottom_box)

        self.setLayout(layout)

    def make_inscombo(self, label, initial, layout, i):
        combo = self.make_combobox(label, initial, layout, i)
        combo.addItem("")
        combo.addItems(list(self.parent.result_info["Institutions"].keys()))

        combo.lineEdit().textEdited.connect(
            lambda: self.inscomobo_refresh(combo, combo.currentText())
        )
        return combo

    def inscomobo_refresh(self, combo, currenttext):
        combo.clear()
        combo.addItem("")
        combo.lineEdit().setText(currenttext)
        if currenttext != "":
            new_list = [
                element
                for element in list(self.parent.result_info["Institutions"].keys())
                if currenttext.upper() in element.upper()
            ]
            combo.addItems(new_list)
        else:
            combo.addItems(list(self.parent.result_info["Institutions"].keys()))

    def make_combobox(self, label, initial, layout, i):
        label_text = QLabel()
        label_text.setText(label)
        combo = QComboBox()
        LE = QLineEdit()
        combo.setLineEdit(LE)
        combo.lineEdit().setText(initial)
        #        combo.lineEdit().setCompleter(None)
        if initial == "TBA":
            LE.setReadOnly(True)
            #            combo.lineEdit().setReadOnly(True)
            combo.setStyleSheet("color: black; background-color:linen;")
            combo.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(label_text, i, 0)
        layout.addWidget(combo, i, 1)

        return combo

    def make_roomTemp_layout(self):
        grid_layout, self.edit_roomTemp = self.make_value_unit_layout(
            str(self.parent.result_info["Temp_value"]),
            self.parent.result_info["Temp_unit"],
        )

        return grid_layout

    def make_humidity_layout(self):
        grid_layout, self.edit_humidity = self.make_value_unit_layout(
            str(self.parent.result_info["Humidity_value"]),
            self.parent.result_info["Humidity_unit"],
        )

        return grid_layout

    def make_value_unit_layout(self, value_str, unit_str):
        grid_layout = QGridLayout()

        label = QLabel()
        label.setText(unit_str)

        edit_value = QLineEdit()
        edit_value.setValidator(QDoubleValidator())
        edit_value.setAlignment(Qt.AlignRight)
        edit_value.setText(value_str)

        grid_layout.addWidget(edit_value, 0, 0)
        grid_layout.addWidget(label, 0, 1)

        return grid_layout, edit_value

    def make_textform(self, label, initial, layout, i):
        label_text = QLabel()
        label_text.setText(label)
        edit_text = QLineEdit()
        edit_text.setText(initial)

        if initial == "TBA":
            edit_text.setStyleSheet("color: black; background-color:linen;")
            edit_text.setReadOnly(True)
            edit_text.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(label_text, i, 0)
        layout.addWidget(edit_text, i, 1)

        return edit_text

    def select_file_layout(self, label, initial, layout, i):
        label_text = QLabel()
        label_text.setText(label)
        edit_text = QLineEdit()
        edit_text.setText(initial)
        edit_text.setFocusPolicy(Qt.NoFocus)
        edit_text.setReadOnly(True)

        Choose_button = QPushButton("Choose file")
        Choose_button.clicked.connect(lambda: self.get_path(edit_text))

        box = QHBoxLayout()
        box.addWidget(edit_text)
        box.addWidget(Choose_button)

        layout.addWidget(label_text, i, 0)
        layout.addLayout(box, i, 1)

        return edit_text

    def get_path(self, lineedit):
        lineedit.setText(self.choose_file())

    def choose_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        try:
            dlg.exec_()
            return dlg.selectedFiles()[0]
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Please choose correct file", QMessageBox.Ok
            )
        return None

    def pass_result(self):
        token = 0
        try:
            ins_token = 0
            if {self.edit_institution.currentText()} <= set(
                self.parent.result_info["Institutions"].keys()
            ):
                ins_token = 1
            else:
                ins_msgBox = QMessageBox.warning(
                    None,
                    "Warning",
                    "The institution is not registered in ITkPD. Do you want to continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if ins_msgBox == QMessageBox.Yes:
                    ins_token = 1
                elif ins_msgBox == QMessageBox.No:
                    ins_token = 0
            if ins_token == 1:
                result_dict = {
                    "comment": self.edit_comment.toPlainText(),
                    "Machine": self.edit_machine.text(),
                    "Operator": self.edit_operator.text(),
                    "Institution_of_operator": self.edit_institution.currentText(),
                    "batch": self.edit_batch.text(),
                    "jig": self.edit_jig.text(),
                    "program_path": self.edit_program.text(),
                    "Temp_value": float(self.edit_roomTemp.text()),
                    "Humidity_value": float(self.edit_humidity.text()),
                }
                token = 1
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Please fill these form.", QMessageBox.Ok
            )

        if token == 1:
            if (
                float(self.edit_roomTemp.text()) < -50
                or float(self.edit_roomTemp.text()) > 50
            ):
                QMessageBox.warning(
                    None, "Warning", "Temperature looks wrong.", QMessageBox.Ok
                )
            else:
                if (
                    float(self.edit_humidity.text()) < 0
                    or float(self.edit_humidity.text()) > 100
                ):
                    QMessageBox.warning(
                        None,
                        "Warning",
                        "It is impossible humidity value.",
                        QMessageBox.Ok,
                    )
                else:
                    if Path(self.edit_program.text()).is_file():
                        self.parent.receive_result(result_dict)
                    else:
                        QMessageBox.critical(
                            None, "Warning", "Program file not exist.", QMessageBox.Ok
                        )

    def back_page(self):
        self.parent.close_and_return()
