from __future__ import annotations

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.qc_tests.WIREBOND_PULL_TEST import user_input


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        self.parent = parent
        self.initial_wid = None

        self.setWindowTitle("Wirebond pull tests")
        self.scale_window(340, 255)

        self.result_info = {
            "minimum_load": "",
            "minimum_load_unit": "g",
            "maximum_load": "",
            "maximum_load_unit": "g",
            "mean_load": "",
            "mean_load_unit": "g",
            "load_standard_deviation": "",
            "load_standard_deviation_unit": "g",
            "percentage_of_heel_breaks": "",
            "percentage_of_heel_breaks_unit": "%",
            "comment": "",
        }

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

    def return_result(self):
        self.parent.receive_result(self, self.test_result_dict)
