from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class InitialWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        self.setMinimumWidth(340)
        self.setMinimumHeight(200)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        button_box = QHBoxLayout()

        label_text = QLabel()
        label_text.setText(
            '<center><font size="6">Input ATLAS Serial Number</font></center>'
        )
        label_atlsn = QLabel()
        label_atlsn.setText("ATLAS Serial Number:")

        #        self.edit_atlsn = QLineEdit()
        #        self.edit_atlsn.setText(self.parent.atlsn)
        self.edit_atlsn = self.make_comp_combo(self.parent.atlsn)

        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.parent.login_localdb)

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.pass_atlsn)

        button_box.addWidget(Back_button)
        button_box.addStretch()
        button_box.addWidget(Next_button)

        form_layout.addRow(label_atlsn, self.edit_atlsn)

        layout.addStretch()
        layout.addWidget(label_text)
        layout.addStretch()
        layout.addLayout(form_layout)
        layout.addLayout(button_box)

        self.setLayout(layout)

    def make_comp_combo(self, initial):
        combo = self.make_combobox(initial)
        combo.addItem("")
        combo.addItems(self.parent.component_list)

        combo.lineEdit().textEdited.connect(
            lambda: self.comobo_refresh(combo, combo.currentText())
        )
        return combo

    def comobo_refresh(self, combo, currenttext):
        combo.clear()
        combo.addItem("")
        combo.lineEdit().setText(currenttext)
        if currenttext != "":
            new_list = [
                element
                for element in self.parent.component_list
                if currenttext.upper() in str(element).upper()
            ]
            combo.addItems(new_list)
        else:
            combo.addItems(self.parent.component_list)

    def make_combobox(self, initial):
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

        return combo

    def pass_atlsn(self):
        try:
            self.parent.receive_atlsn(self.edit_atlsn.currentText())
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Invalid Serial Number", QMessageBox.Ok
            )
