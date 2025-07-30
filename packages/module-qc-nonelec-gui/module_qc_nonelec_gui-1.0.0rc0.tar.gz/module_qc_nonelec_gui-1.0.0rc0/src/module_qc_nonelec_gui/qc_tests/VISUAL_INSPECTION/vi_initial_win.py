from __future__ import annotations

from PyQt5.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

# from PyQt5.QtWidgets import QGridLayout, QLabel, QLineEdit, QPushButton, QWidget
# from PyQt5.QtGUI import *
#


class InitialWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        self.setMinimumWidth(400)
        self.setMinimumHeight(250)

        # Check if doing VI for PCB
        is_PCB = "PCB" in self.parent.type_name
        # Add instrument to the parent
        self.parent.instrument = ""

        # layout
        layout = QGridLayout()

        # QLabel
        label_text = QLabel()
        label_text.setText(
            f'<center><font size="6"> {self.parent.mode.capitalize()}-Side Inspection</font><center>'
        )
        label_atlsn = QLabel()
        label_atlsn.setText("ATLAS Serial Number:")
        label_typename = QLabel()
        label_typename.setText("Component Type:")
        # label_orginstitution = QLabel()
        # label_orginstitution.setText("Original Institution:")
        # label_currentlocation = QLabel()
        # label_currentlocation.setText("Current Location:")
        label_currentstage = QLabel()
        label_currentstage.setText("Current Stage:")
        label_inspector = QLabel()
        label_inspector.setText("Inspector:")
        label_institute = QLabel()
        label_institute.setText("Institution:")
        # Add one QLabel with instrument for PCB Visual Inspection
        if is_PCB:
            label_instrument = QLabel()
            label_instrument.setText("Instrument:")

        # QLineEdit
        self.edit_atlsn = QLineEdit()
        self.edit_typename = QLineEdit()
        # self.edit_origininstitution = QLineEdit()
        # self.edit_currentlocation = QLineEdit()
        self.edit_currentstage = QLineEdit()
        self.edit_inspector = QLineEdit()
        # Add one QLineEdit with instrument for PCB Visual Inspection
        if is_PCB:
            self.edit_instrument = QLineEdit()

        # Differentiate between PCB and others
        if is_PCB:
            for e in [
                self.edit_atlsn,
                self.edit_typename,
                self.edit_currentstage,
            ]:
                e.setReadOnly(True)
                e.setStyleSheet("background-color : linen; color: black;")
        else:
            for e in [
                self.edit_atlsn,
                self.edit_typename,
                self.edit_currentstage,
                self.edit_inspector,
            ]:
                e.setReadOnly(True)
                e.setStyleSheet("background-color : linen; color: black;")

        self.edit_atlsn.setText(self.parent.atlsn)
        self.edit_typename.setText(self.parent.type_name)
        # self.edit_origininstitution.setText(self.parent.original_institution)
        # self.edit_currentlocation.setText(self.parent.current_location)
        if self.parent.type_name == "MODULE":
            self.edit_currentstage.setText(self.parent.stage)
            self.edit_inspector.setText(self.parent.inspector)
            # self.edit_institute.setText()
        else:
            self.edit_currentstage.setText(self.parent.stage)

        # Button
        button_layout = QGridLayout()

        button = QPushButton("&Select Image...")

        button.clicked.connect(self.chooseimage)
        button_back = QPushButton("&Back")
        button_back.clicked.connect(self.backpage)

        button_layout.addWidget(button_back, 0, 0)
        button_layout.addWidget(button, 0, 2)

        # Set Layout
        layout.addWidget(label_text, 0, 0, 1, 2)
        layout.addWidget(label_atlsn, 1, 0)
        layout.addWidget(self.edit_atlsn, 1, 1)
        layout.addWidget(label_typename, 2, 0)
        layout.addWidget(self.edit_typename, 2, 1)
        # layout.addWidget(label_orginstitution, 3, 0)
        # layout.addWidget(self.edit_origininstitution, 3, 1)
        # layout.addWidget(label_currentlocation, 4, 0)
        # layout.addWidget(self.edit_currentlocation, 4, 1)
        layout.addWidget(label_currentstage, 5, 0)
        layout.addWidget(self.edit_currentstage, 5, 1)
        layout.addWidget(label_inspector, 6, 0)
        layout.addWidget(self.edit_inspector, 6, 1)
        # Add instrument line to layout for PCB
        if is_PCB:
            layout.addWidget(label_instrument, 7, 0)
            layout.addWidget(self.edit_instrument, 7, 1)
        # layout.addWidget(button,8,2)
        layout.addLayout(button_layout, 8, 0, 1, 2)

        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

    def chooseimage(self):
        # self.parent.atlsn = self.edit_atlsn.text()
        # self.parent.type_name = self.edit_typename.text()
        # self.parent.inspector = self.edit_inspector.text()
        # Need to read-out operator and instrument field
        if "PCB" in self.parent.type_name:
            self.parent.inspector = self.edit_inspector.text()
            self.parent.instrument = self.edit_instrument.text()

        self.parent.load_img(self.parent.mode)

    def backpage(self):
        if self.parent.mode == "front":
            self.parent.close_and_return()
        else:
            self.parent.mode = "front"
            self.parent.go_to_summary(self)
