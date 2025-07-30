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

        self.parent.confirm_init_common(self, width=800, height=500)

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
            editor.setFixedWidth(200)
            editor.setFocusPolicy(Qt.NoFocus)
            editor.setStyleSheet("background-color : linen; color: black;")
        #        editor.setStyleSheet("background-color : azure")

        Form_layout.addRow(label, editor)

    def make_layout(self):
        if (
            self.parent.info_dict["componentType"] == "MODULE"
            or self.parent.info_dict["componentType"] == "practice"
        ):
            return self.layout_ModuleQC()
        return self.layout_ModuleQC()

    """def layout_ModuleQC(self):
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

        return HBox"""

    def layout_ModuleQC(self):
        Form_layout = self.parent.confirm_layout_common(self)

        for prop_code in ["OPERATOR", "INSTRUMENT"]:
            self.add_info(
                Form_layout,
                prop_code.lower().capitalize() + " : ",
                self.parent.testRun["results"]["property"][prop_code],
            )
        return Form_layout
