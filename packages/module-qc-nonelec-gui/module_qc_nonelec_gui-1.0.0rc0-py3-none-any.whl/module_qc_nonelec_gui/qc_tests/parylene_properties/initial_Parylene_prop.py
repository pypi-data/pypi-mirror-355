from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QComboBox,
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
            '<center><font size="7">Input Parylene properties</font></center>'
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
        label_vendor = QLabel()
        label_vendor.setText("Parylene thickness measured by vendor : ")
        label_ITk = QLabel()
        label_ITk.setText("Parylene thickness measured by ITk Institute : ")

        self.edit_comment = QTextEdit()
        self.edit_comment.setText(self.parent.result_info["comment"])

        #        self.edit_parylene   = self.make_textform('Parylene type : ',self.parent.result_info['Parylene_type'],grid_edit,0)
        self.edit_parylene = self.make_parylene(
            "Parylene type : ", self.parent.result_info["Parylene_type"], grid_edit, 0
        )
        self.edit_mask = self.make_textform(
            "Name of Masking Operator : ",
            self.parent.result_info["Name_of_Masking_Operator"],
            grid_edit,
            1,
        )
        self.edit_mask_ins = self.make_inscombo(
            "Institution of Masking Operator : ",
            self.parent.result_info["Institution_of_Masking_Operator"],
            grid_edit,
            2,
        )
        self.edit_remove = self.make_textform(
            "Name of Operator Removing Mask : ",
            self.parent.result_info["Name_of_Operator_Removing_Mask"],
            grid_edit,
            3,
        )
        self.edit_remove_ins = self.make_inscombo(
            "Institution of Operator Removing Mask : ",
            self.parent.result_info["Institution_of_Operator_Removing_Mask"],
            grid_edit,
            4,
        )
        self.edit_batch = self.make_textform(
            "Parylene batch number : ", self.parent.result_info["batch"], grid_edit, 5
        )

        grid_edit.addWidget(label_vendor, 6, 0)
        grid_edit.addLayout(self.make_thickness_vendor(), 6, 1)

        grid_edit.addWidget(label_ITk, 7, 0)
        grid_edit.addLayout(self.make_thickness_ITk(), 7, 1)

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

    def make_thickness_vendor(self):
        grid_layout, self.edit_thickness_vendor = self.make_value_unit_layout(
            str(self.parent.result_info["Parylene_thickness_measured_by_vendor"]),
            self.parent.result_info["Thickness_unit"],
        )

        return grid_layout

    def make_thickness_ITk(self):
        grid_layout, self.edit_thickness_ITk = self.make_value_unit_layout(
            str(
                self.parent.result_info["Parylene_thickness_measured_by_ITk_Institute"]
            ),
            self.parent.result_info["Thickness_unit"],
        )

        return grid_layout

    def make_parylene(self, label, initial, layout, i):
        combo = self.make_combobox(label, initial, layout, i)
        #        combo.addItems( ['Type-N','Type-C' ] )
        combo.addItems(self.parent.result_info["Parylene_type_list"])
        combo.lineEdit().setReadOnly(True)
        return combo

    def make_inscombo(self, label, initial, layout, i):
        combo = self.make_combobox(label, initial, layout, i)
        combo.addItem("")
        combo.addItems(list(self.parent.result_info["Institution"].keys()))

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
                for element in list(self.parent.result_info["Institution"].keys())
                if currenttext.upper() in element.upper()
            ]
            combo.addItems(new_list)
        else:
            combo.addItems(list(self.parent.result_info["Institution"].keys()))

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

    def pass_result(self):
        token = 0
        try:
            ins_token = 0
            if {
                self.edit_mask_ins.currentText(),
                self.edit_remove_ins.currentText(),
            } <= set(self.parent.result_info["Institution"].keys()):
                ins_token = 1
            else:
                ins_msgBox = QMessageBox.warning(
                    None,
                    "Warning",
                    "Either or both institutions are not registered in ITkPD. Do you want to continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if ins_msgBox == QMessageBox.Yes:
                    ins_token = 1
                elif ins_msgBox == QMessageBox.No:
                    ins_token = 0
            if ins_token == 1:
                result_dict = {
                    "comment": self.edit_comment.toPlainText(),
                    "batch": self.edit_batch.text(),
                    "Parylene_type": self.edit_parylene.currentText(),
                    "Name_of_Masking_Operator": self.edit_mask.text(),
                    "Name_of_Operator_Removing_Mask": self.edit_remove.text(),
                    "Institution_of_Masking_Operator": self.edit_mask_ins.currentText(),
                    "Institution_of_Operator_Removing_Mask": self.edit_remove_ins.currentText(),
                    "Parylene_thickness_measured_by_vendor": float(
                        self.edit_thickness_vendor.text()
                    ),
                    "Parylene_thickness_measured_by_ITk_Institute": float(
                        self.edit_thickness_ITk.text()
                    ),
                }
                if (
                    float(self.edit_thickness_vendor.text()) > 1000
                    or float(self.edit_thickness_vendor.text()) < 0
                    or float(self.edit_thickness_ITk.text()) > 1000
                    or float(self.edit_thickness_ITk.text()) < 0
                ):
                    QMessageBox.warning(
                        None, "Warning", "Parylen thickness is strange.", QMessageBox.Ok
                    )
                else:
                    token = 1
        except Exception:
            #            import traceback
            #            print (traceback.format_exc() )
            QMessageBox.warning(
                None, "Warning", "Please Fill these form.", QMessageBox.Ok
            )

        if token == 1:
            self.parent.receive_result(result_dict)

    def back_page(self):
        self.parent.close_and_return()
