from __future__ import annotations

import logging

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.qc_tests.IV_MEASURE_BARE import user_input

log = logging.getLogger(__name__)


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        self.parent = parent

        self.setWindowTitle("Sensor I-V")
        self.scale_window(510, 255)

        self.result_info = {"comment": "", "filename": ""}

        self.initial_wid = None

    ###########################################################################################

    def init_ui(self):
        self.initial_wid = user_input.InitialWindow(self)
        self.parent.update_widget(self.initial_wid)

    def scale_window(self, x, y):
        self.setGeometry(0, 0, x, y)

    def close_and_return(self):
        self.close()
        self.parent.back_from_test()

    def back_page(self):
        self.parent.init_ui()

    def call_another_window(self, window):
        self.hide()
        window.init_ui()
