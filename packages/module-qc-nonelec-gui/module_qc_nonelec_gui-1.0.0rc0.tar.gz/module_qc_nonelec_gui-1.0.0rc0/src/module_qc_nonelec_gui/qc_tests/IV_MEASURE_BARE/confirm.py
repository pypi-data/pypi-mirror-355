from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from module_qc_nonelec_gui.qc_tests.IV_MEASURE_BARE import function


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
        if function.upload_to_db_IV(self.parent):
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

    #################################################################
    def make_layout(self):
        if (
            self.parent.info_dict["componentType"] == "MODULE"
            or self.parent.info_dict["componentType"] == "practice"
        ):
            return self.layout_ModuleQC()
        return self.layout_ModuleQC()

    def layout_ModuleQC(self):
        HBox = QHBoxLayout()
        Form_layout = self.parent.confirm_layout_common(self)

        self.add_info(
            Form_layout,
            "Comment :",
            self.parent.testRun_sen["results"]["comment"],
        )

        current = []
        voltage = []
        current_error = []
        for v, i, sigmaI in zip(
            self.parent.testRun_sen["results"]["IV_ARRAY"]["voltage"],
            self.parent.testRun_sen["results"]["IV_ARRAY"]["current"],
            self.parent.testRun_sen["results"]["IV_ARRAY"]["sigma current"],
            strict=False,
        ):
            current.append(i)
            voltage.append(v)
            current_error.append(sigmaI)
        current_unit = "Negative Current [uA]"
        voltage_unit = "Negative Voltage [V]"

        graph = Create_Canvas(self)
        graph.setFixedHeight(380)
        graph.setFixedWidth(400)
        graph.graph_plot(voltage, current, voltage_unit, current_unit, current_error)
        graph.canvas_show()

        HBox.addLayout(Form_layout)
        HBox.addWidget(graph)

        return HBox


class Create_Canvas(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.ax = None

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(toolbar)
        self.setLayout(layout)

    def graph_plot(self, x_list, y_list, x_unit, y_unit, y_error_list):
        self.ax = self.figure.add_subplot(111)
        self.ax.scatter(x_list, y_list, c="black")
        self.ax.errorbar(
            x_list, y_list, yerr=y_error_list, capsize=3, ecolor="black", c="black"
        )
        self.ax.set_title("Sensor I-V")
        self.ax.set_xlabel(x_unit)
        self.ax.set_ylabel(y_unit)
        self.figure.subplots_adjust(bottom=0.15)
        self.figure.subplots_adjust(left=0.25)

    def canvas_show(self):
        self.canvas.draw()
