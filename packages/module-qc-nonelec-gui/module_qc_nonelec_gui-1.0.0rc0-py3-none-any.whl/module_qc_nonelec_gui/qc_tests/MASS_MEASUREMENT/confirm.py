from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QScrollArea,
    QTextEdit,
    QWidget,
)


class ConfirmWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        self.parent.confirm_init_common(self, width=500, height=500)

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
            inner.setStyleSheet("background-color : linen; color: black;")

            editor = QScrollArea()
            editor.setWidgetResizable(True)
            editor.setWidget(inner)

        else:
            editor = QLineEdit()
            editor.setText(form_text)
            editor.setReadOnly(True)

        editor.setFocusPolicy(Qt.NoFocus)
        editor.setStyleSheet("background-color : linen; color: black;")
        editor.setFixedWidth(300)
        editor.setMaximumWidth(400)

        Form_layout.addRow(label, editor)

    #################################################################
    def make_layout(self):
        if (
            self.parent.info_dict["componentType"] == "MODULE"
            or self.parent.info_dict["componentType"] == "practice"
        ):
            return self.layout_ModuleQC()
        return self.layout_ModuleQC()

    def layout_ModuleQC(self):
        Form_layout = self.parent.confirm_layout_common(self)

        mass_value = f'{self.parent.testRun["results"]["MASS"]} {self.parent.testRun["results"]["Metadata"]["MASS_UNIT"]}'
        acu_value = f'{self.parent.testRun["results"]["property"]["SCALE_ACCURACY"]} {self.parent.testRun["results"]["Metadata"]["SCALE_ACCURACY_UNIT"]}'

        self.add_info(Form_layout, "Total weight :", mass_value)
        self.add_info(Form_layout, "Scale accuracy :", acu_value)
        self.add_info(
            Form_layout, "Comment :", self.parent.testRun["results"]["comment"]
        )

        return Form_layout
