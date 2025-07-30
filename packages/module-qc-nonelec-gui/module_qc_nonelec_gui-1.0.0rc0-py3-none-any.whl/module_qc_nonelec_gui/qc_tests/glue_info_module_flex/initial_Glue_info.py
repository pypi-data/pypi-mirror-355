from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
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
            '<center><font size="7">Input Glue Information</font></center>'
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
        label_adhesion = QLabel()
        label_adhesion.setText("Adhesion time : ")

        self.edit_comment = QTextEdit()
        self.edit_comment.setText(self.parent.result_info["comment"])

        self.edit_glue = self.make_textform(
            "Glue name : ", self.parent.result_info["glue_name"], grid_edit, 0
        )
        self.edit_ratio = self.make_textform(
            "Volume ratio of glue mixture : ",
            self.parent.result_info["ratio"],
            grid_edit,
            1,
        )
        self.edit_batch = self.make_textform(
            "Glue batch number : ", self.parent.result_info["batch"], grid_edit, 2
        )

        grid_edit.addWidget(label_roomTemp, 3, 0)
        grid_edit.addLayout(self.make_roomTemp_layout(), 3, 1)

        grid_edit.addWidget(label_humidity, 4, 0)
        grid_edit.addLayout(self.make_humidity_layout(), 4, 1)

        #        grid_edit.addWidget(label_adhesion,5,0)
        grid_edit.addWidget(label_comment, 5, 0)

        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setWidget(self.edit_comment)
        grid_edit.addWidget(outer, 5, 1)

        layout.addWidget(label_title)
        layout.addStretch()
        layout.addLayout(grid_edit)
        layout.addLayout(bottom_box)

        self.setLayout(layout)

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

    def pass_result(self):
        token = 0
        try:
            result_dict = {
                "comment": self.edit_comment.toPlainText(),
                "glue_name": self.edit_glue.text(),
                "ratio": self.edit_ratio.text(),
                "batch": self.edit_batch.text(),
                "Temp_value": float(self.edit_roomTemp.text()),
                "Humidity_value": float(self.edit_humidity.text()),
            }
            token = 1
        except Exception:
            #            import traceback
            #            print (traceback.format_exc() )
            QMessageBox.warning(
                None, "Warning", "Please Fill these form.", QMessageBox.Ok
            )

        if token == 1:
            if (
                float(self.edit_roomTemp.text()) < -50
                or float(self.edit_roomTemp.text()) > 50
            ):
                QMessageBox.warning(
                    None,
                    "Warning",
                    "Hey! You alive? \nIt is too difficult to live at this room temperature.",
                    QMessageBox.Ok,
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
                    self.parent.receive_result(result_dict)

    def back_page(self):
        self.parent.close_and_return()
