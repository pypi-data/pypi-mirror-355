from __future__ import annotations

import contextlib
import json
import logging
import os
import pprint
import sys
import traceback
from datetime import date, datetime, timezone
from importlib import machinery
from pathlib import Path

import requests
from bson.objectid import ObjectId
from PyQt5 import QtCore
from PyQt5.QtGui import qt_set_sequence_auto_mnemonic
from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from module_qc_nonelec_gui import __version__
from module_qc_nonelec_gui.dbinterface import (
    localdb_authenticator,
    localdb_retriever,
)
from module_qc_nonelec_gui.GUI import (
    choosetest_win,
    componentinfo_win,
    connectdb_win,
    continue_win,
    inputatlsn_win,
    setup_win,
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

UTC = timezone.utc


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.version = __version__

        qt_set_sequence_auto_mnemonic(
            True
        )  # shortcut enabled on MacOS (otherhand, default enabled on Linux)

        self.module_qc_nonelec_gui_dir = "/".join(
            os.path.realpath(__file__).split("/")[:-2]
        )
        log.info(self.module_qc_nonelec_gui_dir)

        self.setWindowTitle(f"module-qc-nonelec-gui v{self.version}")
        self.setGeometry(0, 0, 340, 255)

        # hacks
        self.VI_grayout_with_emptyATLSN = False  # if True, Optical inspection get grayout with empty atlas serial No. (ref: choosetest_win.py)

        # initial
        self.institute_dict = {}
        self.info_dict = {}
        self.localDB_dict = {}
        self.test_dict = {}
        self.summary_dict = {}
        self.component_list = []

        self.isOK_to_upload = True
        self.isPractice = False
        self.isSummarize = False
        self.isSameComponent = False

        self.atlsn = ""
        self.db_user = None
        self.db_pass = None

        self.supportedComponentTypes = ["MODULE", "BARE_MODULE", "PCB"]

        self.make_statusbar()
        self.update_statusbar(self)

        self.cptTypeMap = {
            "module": "MODULE",
            "bare_module": "BARE_MODULE",
            "module_pcb": "PCB",
            "sensor_tile": "SENSOR_TILE",
            "front-end_chip": "FE_CHIP",
        }

        # other member variables used
        self.config = None
        self.connectdb_wid = None
        self.inputatlsn_wid = None
        self.token = None
        self.component = None
        self.override_conf = None
        self.qcStatus = None
        self.qcStages = None
        self.u = None
        self.componentinfo_wid = None
        self.localDB = None
        self.localDBtools = None
        self.module_id = None
        self.user_info = None
        self.choosetest_wid = None
        self.testRunFormat = None
        self.testRun = None
        self.test_module = None
        self.test_win = None
        self.confirm_module = None
        self.confirm_wid = None
        self.json_wid = None
        self.continue_wid = None

        self.init_ui()

    def init_ui(self):
        # self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # configuration1
        try:
            log.info("loading custom json file...")
            with Path(
                self.module_qc_nonelec_gui_dir + "/configuration/custom.json"
            ).open(encoding="utf-8") as f:
                self.custom_conf = json.load(f)

            log.info("loaded custom json file:")
            log.info(pprint.pformat(self.custom_conf))
        except Exception as e:
            log.error(e)
            self.close()
            wid = setup_win.SetupWindow(self)
            self.update_widget(wid)
            return

        try:
            with Path(
                self.module_qc_nonelec_gui_dir + "/configuration/config_default.json"
            ).open(encoding="utf-8") as f1:
                self.default_conf = json.load(f1)

        except Exception as e:
            log.error(e)

        self.config = self.default_conf

        if self.isSameComponent:
            self.fill_info()

        else:
            self.connectdb_wid = connectdb_win.ConnectDBWindow(self)
            self.update_widget(
                self.connectdb_wid,
                self.connectdb_wid.sizeHint().width(),
                self.connectdb_wid.sizeHint().height(),
            )

    def set_windowsize(self, x, y):
        self.setGeometry(0, 0, x, y)

    def scale_window(self, x, y):
        QApplication.processEvents()
        self.set_windowsize(x, y)

    def make_statusbar(self):
        self.status_label = QLabel()
        self.status_label.setText("")
        self.status_practice = QLabel()
        self.status_practice.setText("")

        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet(
            "QStatusBar{border-style :dot-dot-dash ; border-width : 1px 0px 0px 0px ; border-color : black;}"
        )
        self.statusbar.addWidget(self.status_label)
        self.statusbar.addPermanentWidget(self.status_practice)
        self.setStatusBar(self.statusbar)

    def update_statusbar(self, window):
        try:
            self.status_label.setText("Current user : " + self.info_dict["user"])
        except Exception:
            self.status_label.setText("")

        if self.isPractice:
            self.status_practice.setText('<font color = "green"> practice mode</font>')
        else:
            self.status_practice.setText("")

        window.setStatusBar(self.statusbar)

    def update_widget(self, widget, width=None, height=None):
        if hasattr(self, "position"):
            self.position = [self.pos().x(), self.pos().y()]

        self.update_statusbar(self)
        self.setCentralWidget(widget)

        if width is not None and height is not None:
            self.scale_window(width, height)

        if not hasattr(self, "position"):
            self.move(100, 100)
            self.position = [self.pos().x(), self.pos().y()]
        else:
            self.move(self.position[0], self.position[1])

        self.show()

    def call_another_window(self, window):
        self.hide()
        self.update_statusbar(window)
        window.init_ui()

    def login_localdb(self):
        self.connectdb_wid = connectdb_win.ConnectDBWindow(self)
        self.update_widget(
            self.connectdb_wid,
            self.connectdb_wid.sizeHint().width(),
            self.connectdb_wid.sizeHint().height(),
        )

    def start_QCupload(self):
        if self.isPractice and self.token == 0:
            self.practice_pd()
        else:
            self.inputatlsn_wid = inputatlsn_win.InitialWindow(self)
            self.update_widget(
                self.inputatlsn_wid,
                self.inputatlsn_wid.sizeHint().width(),
                self.inputatlsn_wid.sizeHint().height(),
            )

    def receive_atlsn(self, sn):
        self.atlsn = sn
        if self.isPractice and self.atlsn == "":
            self.practice_pd()
        else:
            self.get_component_info()
            log.info("[ATLAS SerialNumber] " + sn)

    def get_component_info(self):
        self.component = self.localDB.component.find_one({"serialNumber": self.atlsn})

        componentType = self.component["componentType"]
        cptCfgFile = ""

        self.fill_info()

        if componentType == "module":
            # triplet stave
            if any((tok in self.atlsn) for tok in ["MS", "R6", "R3"]):
                log.exception(self.atlsn + ": triplet stave module")
                cptCfgFile = "config_triplet_s.json"

            # triplet ring
            elif any(
                (tok in self.atlsn) for tok in ["M0", "M5", "R7", "R8", "R4", "R5"]
            ) and ("XM" not in self.atlsn):
                log.info(self.atlsn + ": triplet ring module")
                cptCfgFile = "config_triplet_r.json"

            # quad
            else:
                log.info(self.atlsn + ": quad module")
                cptCfgFile = "config_quad.json"

        # bare_module
        elif componentType == "bare_module":
            log.info(self.atlsn + ": bare_module")
            cptCfgFile = "config_quad.json"

        # pcb
        elif componentType == "module_pcb":
            log.info(self.atlsn + ": pcb")
            cptCfgFile = "config_quad.json"

        self.config = self.default_conf

        try:
            with (
                Path(self.module_qc_nonelec_gui_dir)
                .joinpath("configuration", cptCfgFile)
                .open(encoding="utf-8") as f
            ):
                self.override_conf = json.load(f)

            for code, obj in self.override_conf[self.info_dict.get("componentType")][
                "test"
            ].items():
                self.config[self.info_dict.get("componentType")]["test"][code] = obj

        except Exception:
            log.warning("cptCfgFile not possible to open")

    def fill_info(self):
        try:
            self.qcStatus = self.localDB.QC.module.status.find_one(
                {"component": str(self.component["_id"])}
            )
            self.qcStages = self.localDBtools.QC.stages.find_one(
                {"code": self.cptTypeMap.get(self.component["componentType"])}
            )

            self.info_dict["component"] = self.atlsn
            self.info_dict["componentType"] = self.cptTypeMap.get(
                self.component["componentType"]
            )
            with contextlib.suppress(Exception):
                self.info_dict["FE_version"] = next(
                    [
                        d.get("value")
                        for d in self.component["properties"]
                        if d.get("code") == "FECHIP_VERSION"
                    ]
                )

            self.info_dict["date"] = datetime.now(UTC)
            self.info_dict["sys"] = {
                "cts": datetime.now(UTC),
                "mts": datetime.now(UTC),
                "rev": 0,
            }

            self.info_dict["stage"] = (
                self.qcStatus["stage"]
                if self.qcStatus.get("stage") is not None
                else self.qcStatus.get("stage")
            )
            self.info_dict["stageCode"] = self.qcStages["stages"].get(
                self.info_dict["stage"]
            )

            log.info("[Component type] " + self.info_dict["componentType"])
            self.moduleQC_choose_test()

        except Exception:
            log.exception(traceback.format_exc())
            if self.isPractice:
                self.practice_pd()
            else:
                msgBox = QMessageBox.warning(
                    None,
                    "Warning",
                    "component:" + self.atlsn + " is not found in ITkPD."
                    "Do you want to continue as practice mode?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if msgBox == QMessageBox.Yes:
                    self.isPractice = True
                    self.practice_pd()
                elif msgBox == QMessageBox.No:
                    self.isPractice = False
                    self.start_QCupload()

    def practice_pd(self):
        if self.atlsn != "":
            self.info_dict["component"] = self.atlsn
        else:
            self.info_dict["component"] = "practice"

        self.info_dict["bare_module"] = ["practice"]
        self.info_dict["bare_module_code"] = ["practice"]
        self.info_dict["chip_quantity"] = 4
        self.info_dict["FE_version"] = "practice"

        self.info_dict["componentType"] = "practice"
        self.info_dict["institution"] = "practice"
        self.info_dict["currentLocation"] = "practice"
        self.info_dict["type"] = "practice"
        self.info_dict["typeCode"] = "practice"
        self.info_dict["stage"] = "practice"
        self.info_dict["stageCode"] = "practice"
        self.info_dict["date"] = datetime.now(UTC)
        self.info_dict["sys"] = {
            "cts": datetime.now(UTC),
            "mts": datetime.now(UTC),
            "rev": 0,
        }
        self.fill_practice_testtype_dict()
        if self.isPractice and self.token == 0:
            self.institute_dict = {"practice": "Practice"}
        self.see_info()

    def see_info(self):
        self.componentinfo_wid = componentinfo_win.ComponentInfoWindow(self)
        self.update_widget(
            self.componentinfo_wid,
            self.componentinfo_wid.sizeHint().width(),
            self.componentinfo_wid.sizeHint().height(),
        )

    def back_from_componentinfo(self):
        self.isSameComponent = False
        if self.isPractice and self.token == 0:
            self.call_selectmode()
        else:
            self.start_QCupload()

    def back_from_choosetest(self):
        self.start_QCupload()

    def receive_db_user(self, username, password):
        self.db_user = username
        self.db_pass = password

        try:
            self.localDB, self.localDBtools = localdb_authenticator.connectDB(
                self.custom_conf["mongoDB"]["address"],
                self.custom_conf["mongoDB"]["port"],
                self.db_user,
                self.db_pass,
            )
        except Exception:
            QMessageBox.warning(
                None,
                "Warning",
                "Failed in LocalDB User Authentication",
                QMessageBox.Ok,
            )

            self.connectdb_wid = connectdb_win.ConnectDBWindow(self)
            self.update_widget(
                self.connectdb_wid,
                self.connectdb_wid.sizeHint().width(),
                self.connectdb_wid.sizeHint().height(),
            )
            return

        self.info_dict["user"] = self.db_user
        self.db_pass = None

        self.component_list = [
            c["serialNumber"] for c in self.localDB.component.find({})
        ]

        self.start_QCupload()

    def moduleQC_choose_test(self):
        if self.isPractice:
            self.practice_choosetest()
        else:
            try:
                self.module_id = self.component["_id"]

                self.user_info = localdb_retriever.userinfo_retriever(
                    self.localDBtools, self.db_user
                )

                self.localDB_dict["component"] = self.module_id
                self.localDB_dict["stage"] = self.info_dict["stage"]
                self.localDB_dict["user"] = self.user_info["name"]
                self.fill_testtype_dict()

                try:
                    self.choosetest_wid = choosetest_win.ChooseTestWindow(self)
                    self.update_widget(
                        self.choosetest_wid,
                        self.choosetest_wid.sizeHint().width(),
                        self.choosetest_wid.sizeHint().height(),
                    )

                except Exception as e:
                    QMessageBox.warning(
                        None,
                        "Warning",
                        str(e),
                    )
                    self.inputatlsn_wid = inputatlsn_win.InitialWindow(self)
                    self.update_widget(
                        self.inputatlsn_wid,
                        self.inputatlsn_wid.sizeHint().width(),
                        self.inputatlsn_wid.sizeHint().height(),
                    )
            except Exception:
                log.exception(traceback.format_exc())
                msgBox = QMessageBox.warning(
                    None,
                    "Warning",
                    "Authentication failed or LocalDB not ready. Do you want to continue as practice mode?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if msgBox == QMessageBox.Yes:
                    self.isPractice = True
                    self.practice_choosetest()
                elif msgBox == QMessageBox.No:
                    self.isPractice = False
                    self.connectdb_wid = connectdb_win.ConnectDBWindow(self)
                    self.update_widget(
                        self.connectdb_wid,
                        self.connectdb_wid.sizeHint().width(),
                        self.connectdb_wid.sizeHint().height(),
                    )

    def practice_choosetest(self):
        self.info_dict["user"] = "practice"
        self.localDB_dict["component"] = "practice"
        self.localDB_dict["stage"] = "practice"
        self.localDB_dict["user"] = "practice"
        self.localDB_dict["address"] = "practice"
        self.localDB_dict["stage"] = "practice"

        self.choosetest_wid = choosetest_win.ChooseTestWindow(self)
        self.update_widget(
            self.choosetest_wid,
            self.choosetest_wid.sizeHint().width(),
            self.choosetest_wid.sizeHint().height(),
        )

    def back_from_test(self):
        if (
            self.info_dict["componentType"] in self.supportedComponentTypes
            or self.info_dict["componentType"] == "practice"
        ):
            self.moduleQC_choose_test()
        else:
            QMessageBox.critical(
                None,
                "Warning",
                " ComponentType:"
                + self.info_dict["componentType"]
                + " is not supported now. ",
                QMessageBox.Ok,
            )

    def receive_testtype(self, testtype):
        self.info_dict["testType"] = testtype

        self.call_targetGUI()

    def call_targetGUI(self):
        try:
            cptType = self.info_dict.get("componentType")
            cptCfgTests = self.config.get(cptType).get("test")
            testType = self.info_dict.get("testType")

            log.debug("cptType: " + cptType)
            log.debug("cptCfgTests: " + pprint.pformat(cptCfgTests))
            log.debug("testType: " + testType)

            self.testRunFormat = self.localDBtools.QC.tests.find_one(
                {
                    "code": self.info_dict["testType"],
                    "componentType.code": self.info_dict["componentType"],
                }
            )

            self.testRun = {
                "serialNumber": self.atlsn,
                "testType": testType,
                "subtestType": "",
                "results": {
                    "property": {
                        prop["code"]: None for prop in self.testRunFormat["properties"]
                    },
                    "comment": "",
                    "Metadata": {
                        "QCHELPER_VERSION": self.version,
                        "ModuleSN": self.atlsn,
                        "TimeStart": int(self.info_dict["date"].timestamp()),
                    },
                    "Measurements": {},
                },
            }
            if testType == "IV_MEASURE":
                self.testRun["results"]["Metadata"]["MODULE_SN"] = self.testRun[
                    "results"
                ]["Metadata"].pop("ModuleSN")

            log.info(pprint.pformat(self.testRun))

            self.testRun.get("results").update(
                {param["code"]: None for param in self.testRunFormat["parameters"]}
            )
            self.testRun["results"]["property"].setdefault(
                f"{testType}_MEASUREMENT_VERSION", self.version
            )

            log.debug("testRunFormat: " + pprint.pformat(self.testRunFormat))
            log.debug("testRun skeleton: " + pprint.pformat(self.testRun))

            test = cptCfgTests.get(testType)

            log.debug("identified test: " + pprint.pformat(test))

            testGUI_path = str(Path(self.module_qc_nonelec_gui_dir) / test["path"])

            log.debug("testGUI_path: " + testGUI_path)

            self.test_module = machinery.SourceFileLoader(
                testType, testGUI_path
            ).load_module()

            try:
                module_property_list = []
                for _code, property_i in self.config[cptType]["property"].items():
                    module_property_list.append(property_i["code"])

                self.test_win = self.test_module.TestWindow(self)
                self.call_another_window(self.test_win)
            except Exception:
                log.exception(traceback.format_exc())
                QMessageBox.warning(
                    None,
                    "Warning",
                    "There may be error in " + testGUI_path,
                    QMessageBox.Ok,
                )
        except FileNotFoundError:
            QMessageBox.warning(
                None,
                "Warning",
                "There is no library for " + self.info_dict["testType"],
                QMessageBox.Ok,
            )
        except (KeyError, IndexError):
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None,
                "Warning",
                self.info_dict["testType"]
                + ' is not supported now.\nPlease add path of library to "configuration.json"',
                QMessageBox.Ok,
            )

    def receive_result(self, subwindow):
        subwindow.hide()

        log.debug("testRun filled: " + pprint.pformat(self.testRun))
        try:
            self.confirm_result()
        except Exception as e:
            log.exception(e)
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None,
                "Warning",
                "componentType:"
                + self.info_dict["componentType"]
                + " is not supported now.",
                QMessageBox.Ok,
            )

    def confirm_result(self):
        log.info("==========================================================")
        log.info("confirm_result(): [results]")
        if isinstance(self.testRun, dict):
            log.info(pprint.pformat(self.testRun))
        else:
            error_msg = self.testRun
            for line in error_msg.split("\n"):
                log.error(line)
        log.info("==========================================================")

        try:
            cptType = self.info_dict.get("componentType")
            cptCfgTests = self.config.get(cptType).get("test")
            testType = self.info_dict.get("testType")

            test_confirm = cptCfgTests.get(testType).get("confirm_path")

            log.info(f"test_confirm = {test_confirm}")

            test_confirm = str(Path(self.module_qc_nonelec_gui_dir) / test_confirm)
            log.info(f"test_confirm = {test_confirm}")

            self.confirm_module = machinery.SourceFileLoader(
                "confirm", test_confirm
            ).load_module()
            self.confirm_wid = self.confirm_module.ConfirmWindow(self)

            self.update_widget(
                self.confirm_wid,
                self.confirm_wid.sizeHint().width(),
                self.confirm_wid.sizeHint().height(),
            )

        except Exception:
            log.exception(traceback.format_exc())
            try:
                test_confirm = Path(self.module_qc_nonelec_gui_dir).joinpath(
                    "GUI", "lib", "ConfirmWindow", "default_layout;py"
                )
                self.confirm_module = machinery.SourceFileLoader(
                    "default_layout", test_confirm
                ).load_module()
                self.confirm_wid = self.confirm_module.ConfirmWindow(self)
            except FileNotFoundError:
                log.exception(traceback.format_exc())
                QMessageBox.warning(
                    None,
                    "Warning",
                    'Module: "default_layout.py" is not found',
                    QMessageBox.Ok,
                )
        self.update_widget(
            self.confirm_wid,
            self.confirm_wid.sizeHint().width(),
            self.confirm_wid.sizeHint().height(),
        )

    def confirm_init_common(self, sub, width=None, height=None):
        titlebox = QVBoxLayout()
        layout = QVBoxLayout()
        button_box = QHBoxLayout()

        label_title = QLabel()
        label_title.setText(
            '<center><font size="5">QC TestRun Registration Preview</font></center>'
        )
        label_practice = QLabel()
        label_practice.setText(
            '<center><font size="4" color = "green"> Practice Mode</font></center>'
        )
        Upload_button = QPushButton("&Upload!")
        Upload_button.clicked.connect(sub.upload_to_db)
        json_button = QPushButton("&Check json (for expert)")
        json_button.clicked.connect(sub.check_json)
        back_button = QPushButton("&Back")
        back_button.clicked.connect(sub.back_page)

        titlebox.addWidget(label_title)
        if self.isPractice:
            titlebox.addWidget(label_practice)

        button_box.addWidget(back_button)
        button_box.addStretch()
        button_box.addWidget(json_button)
        button_box.addWidget(Upload_button)

        inner = QScrollArea()
        if width:
            inner.setFixedWidth(width)
        if height:
            inner.setFixedHeight(height)
        result_wid = QWidget()
        result_wid.setLayout(sub.make_layout())

        inner.setWidgetResizable(True)
        inner.setWidget(result_wid)

        layout.addLayout(titlebox)
        layout.addWidget(inner)
        layout.addLayout(button_box)
        sub.setLayout(layout)

        self.update_widget(sub, sub.sizeHint().width(), sub.sizeHint().height())

    def confirm_layout_common(self, sub):
        Form_layout = QFormLayout()
        sub.add_info(Form_layout, "Serial Number :", self.info_dict["component"])
        sub.add_info(Form_layout, "Component Type :", self.info_dict["componentType"])
        sub.add_info(
            Form_layout,
            "Current Stage :",
            sub.parent.info_dict["stage"],
        )
        sub.add_info(Form_layout, "Test Type :", self.info_dict["testType"])

        return Form_layout

    def back_from_json(self):
        self.confirm_result()

    def confirm_json(self):
        try:
            json_confirm = str(
                Path(self.module_qc_nonelec_gui_dir)
                / "GUI"
                / "lib"
                / "ConfirmWindow"
                / "json_layout.py"
            )
            self.confirm_module = machinery.SourceFileLoader(
                "json_layout", json_confirm
            ).load_module()
            self.json_wid = self.confirm_module.JsonWindow(self)
            self.update_widget(self.json_wid)
        except Exception:
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None, "Warning", 'Module: "json_layout.py" is not found', QMessageBox.Ok
            )

    def back_to_test(self):
        self.hide()
        self.call_another_window(self.test_win)

    def upload_to_db(self):
        if self.isPractice:
            self.terminate_message()
        else:
            if self.isOK_to_upload:
                try:
                    self.local_save()

                    protocol = self.custom_conf.get("localDB_web").get(
                        "protocol", "http"
                    )
                    host = self.custom_conf.get("localDB_web").get(
                        "address", "127.0.0.1"
                    )
                    port = self.custom_conf.get("localDB_web").get("port", "5000")

                    log.info(
                        f"attempting to upload TestRun to LocalDB on {protocol}://{host}:{port}/localdb/ ..."
                    )
                    res = requests.post(
                        f"{protocol}://{host}:{port}/localdb/qc_uploader_post",
                        json=[[self.testRun]],
                        timeout=60,
                    )
                    log.info("... posted!")

                    out = json.loads(str(res.text))

                    if isinstance(out, list):
                        log.info(pprint.pformat(out))
                        self.terminate_message()

                    else:
                        error = out.get("ERROR").replace("\\n", "\n").split("\n")
                        log.error("ERROR")
                        for line in error:
                            log.error(line)

                        QMessageBox.warning(
                            None,
                            "Warning",
                            "ERROR: failed to upload result to DB",
                            QMessageBox.Ok,
                        )

                except Exception:
                    log.exception(traceback.format_exc())
                    log.exception(str(res.text))
                    QMessageBox.warning(
                        None,
                        "Warning",
                        "ERROR: failed to upload result to DB:\n\n======================\n\n"
                        + str(res.text),
                        QMessageBox.Ok,
                    )
            else:
                QMessageBox.warning(
                    None,
                    "Warning",
                    "you can not have prepared to upload",
                    QMessageBox.Ok,
                )

    def local_save(self):
        try:
            file_name = (
                "_".join(
                    [
                        self.info_dict["component"],
                        self.info_dict["stage"].replace("/", "__"),
                        self.info_dict["testType"],
                        datetime.now(UTC).strftime("%YY%mm%dd__%H_%M_%S%z"),
                    ]
                )
                + ".json"
            )

            Path(file_name).parent.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            log.exception(str(e))
            log.exception(traceback.format_exc())
            file_name = datetime.now(UTC).strftime("%YY%mm%dd__%H_%M_%S%z")

        practice_path = Path(self.module_qc_nonelec_gui_dir).joinpath(
            "results", "practice", file_name
        )
        result_path = Path(self.module_qc_nonelec_gui_dir).joinpath(
            "results", file_name
        )
        summary_path = Path(self.module_qc_nonelec_gui_dir).joinpath(
            "results", "summary", file_name
        )

        if self.isPractice:
            Path(self.module_qc_nonelec_gui_dir).joinpath("results", "practice").mkdir(
                parents=True, exist_ok=True
            )
            self.write_to_json(self.testRun, practice_path)
            log.info(f"saved result JSON to {result_path}")
        else:
            Path(self.module_qc_nonelec_gui_dir).joinpath("results").mkdir(
                parents=True, exist_ok=True
            )
            self.write_to_json(self.testRun, result_path)
            log.info(f"saved result JSON to {result_path}")

        if self.isSummarize:
            Path(self.module_qc_nonelec_gui_dir).joinpath("results", "summary").mkdir(
                parents=True, exist_ok=True
            )
            self.write_to_json(self.summary_dict, summary_path)
            log.info(f"saved result JSON to {result_path}")

    def write_to_json(self, output_dict, file_path):
        try:
            with Path(file_path).open(mode="w", encoding="utf-8") as f:
                json.dump(output_dict, f, default=self.json_rule, indent=4)
        except Exception:
            log.exception(traceback.format_exc())

    def terminate_message(self):
        msgBox = QMessageBox()
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        if self.isPractice:
            msgBox.setText('<center><font size="7">Good practice!</font></center>')
            msgBox.setInformativeText(
                '<center><font size="5">Do you want to go actual inspection?</font></center>'
            )
        elif not self.isPractice:
            msgBox.setText('<center><font size="7">Upload successful!</font></center>')
            msgBox.setInformativeText(
                '<center><font size="5">Do you want to continue to another inspection?</font></center>'
            )

        button_alt = msgBox.exec()
        if button_alt == QMessageBox.Yes:
            if self.isPractice:
                self.isPractice = False
                #                self.restart(0,0)
                self.init_ui()
            else:
                self.isPractice = False
                self.continue_from()
        elif button_alt == QMessageBox.No:
            self.finish_GUI()

    def continue_from(self):
        self.continue_wid = continue_win.ContinueWindow(self)
        self.update_widget(
            self.continue_wid,
            self.continue_wid.sizeHint().width(),
            self.continue_wid.sizeHint().height(),
        )

    def restart(self, is_sameuser, is_sameconmponent):
        self.info_dict.clear()
        self.localDB_dict.clear()
        self.testRun.clear()

        self.isSummarize = False

        if is_sameuser == 0:
            self.info_dict["user"] = self.db_user
            self.db_pass = ""
        else:
            self.db_user = ""
            self.db_pass = ""
        if is_sameconmponent == 0:
            self.isSameComponent = True
        else:
            self.isSameComponent = False
            self.atlsn = ""

        #        self.init_ui()
        self.do_again()

    def do_again(self):
        if self.isSameComponent:
            self.fill_info()
        else:
            self.start_QCupload()

    def finish_GUI(self):
        log.info("Finish QCHelper :" + str(self.close()))
        log.info("---------------------------------------------------------------\n")

    def fill_practice_testtype_dict(self):
        self.test_dict.setdefault("practice", {})
        cptType = self.info_dict["componentType"]

        for i in self.config[cptType]:
            for test_i in [
                (d.get("name"), d.get("code"), d.get("path"))
                for d in self.config[cptType][i]
                if d.get("supported")
            ]:
                name = test_i[0]
                code = test_i[1]
                if test_i[2] == "":
                    name = name + "(TBA)"
                self.test_dict["practice"][name] = code

    def fill_testtype_dict(self):
        cptType = self.info_dict["componentType"]
        stage = self.info_dict["stage"]

        self.test_dict[stage] = {}

        for test_code in self.qcStages["stage_test"][stage]:
            try:
                log.info(test_code)

                supported_tests = self.config[cptType]["test"]

                for _code, testCfg in supported_tests.items():
                    if testCfg["path"] == "":
                        name = testCfg["name"] + "(TBA)"
                    else:
                        name = testCfg["name"]
                    if testCfg["supported"] and (test_code in testCfg["ITkPDcode"]):
                        self.test_dict[stage][name] = testCfg["code"]
                        log.info(f'--> added test {testCfg["code"]}')

            except Exception as e:
                log.info(pprint.pformat(e))
                log.info(traceback.format_exc())

        log.info(pprint.pformat(self.test_dict))

    def json_rule(self, obj):
        if isinstance(obj, (datetime | date)):
            return int(obj.timestamp())
        if isinstance(obj, ObjectId):
            return str(obj)

        msg = "Type {type(obj)} not serializable"
        raise TypeError(msg)
