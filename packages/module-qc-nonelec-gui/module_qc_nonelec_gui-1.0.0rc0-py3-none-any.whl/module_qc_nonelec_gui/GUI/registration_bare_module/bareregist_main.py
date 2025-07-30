from __future__ import annotations

import logging
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from module_qc_nonelec_gui.GUI.registration_bare_module import (
    bareinfo_win,
    bareregist_win,
    feinfo_win,
    initial_win,
    sensorinfo_win,
)

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Bare module registration tool")
        self.setGeometry(0, 0, 340, 255)

        self.baremodule_info = {
            "project": "P",
            "subproject": "PG",
            "institution": "",
            "componentType": "BARE_MODULE",
            "type": "",
            "properties": {"FECHIP_VERSION": "", "THICKNESS": "", "SENSOR_TYPE": ""},
            "child": {"FE_CHIP": [], "SENSOR_TILE": []},
        }

        self.baremodule_doc = {}
        self.user_info = {}

        # other member variables
        self.bare_doc = None
        self.initial_wid = None
        self.bareinfo_wid = None
        self.bareregist_wid = None
        self.feinfo_wid = None
        self.sensorinfo_wid = None
        self.u = None

    def init_ui(self):
        self.choose_menu()

    def choose_menu(self):
        self.bare_doc = {}
        self.baremodule_info["child"]["FE_CHIP"] = []
        self.baremodule_info["child"]["SENSOR_TILE"] = []
        self.initial_wid = initial_win.InitialWindow(self)
        self.parent.update_widget(self.initial_wid)
        log.info("\n---------------------------------------------------------------")

    def bareupdate(self):
        self.bareinfo_wid = bareinfo_win.BareInfoWindow(self)
        self.parent.update_widget(self.bareinfo_wid)

    def bareregist(self):
        self.bareregist_wid = bareregist_win.BareRegistWindow(self)
        self.parent.update_widget(self.bareregist_wid)

    def set_windowsize(self, x, y):
        self.setGeometry(0, 0, x, y)

    def feinfo(self):
        self.feinfo_wid = feinfo_win.FEInfoWindow(self)
        self.parent.update_widget(self.feinfo_wid)

    def sensorinfo(self):
        self.sensorinfo_wid = sensorinfo_win.SensorInfoWindow(self)
        self.parent.update_widget(self.sensorinfo_wid)

    def scale_window(self, x, y):
        QApplication.processEvents()
        self.set_windowsize(x, y)

    def call_another_window(self, window):
        self.hide()
        self.update_statusbar(window)
        window.init_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
