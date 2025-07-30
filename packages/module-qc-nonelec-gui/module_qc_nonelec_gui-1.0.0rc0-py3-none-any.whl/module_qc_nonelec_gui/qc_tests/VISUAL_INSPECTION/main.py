from __future__ import annotations

import json
import logging
import pprint
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from module_qc_nonelec_gui.dbinterface import localdb_uploader
from module_qc_nonelec_gui.qc_tests.VISUAL_INSPECTION import (
    inspection_win,
    shaping_win,
    splitimg_win,
    summary_win,
    vi_initial_win,
)
from module_qc_nonelec_gui.qc_tests.VISUAL_INSPECTION.functions.cv2_func import (
    cv2,
    img_rotate,
    read_img,
    write_img,
)

log = logging.getLogger(__name__)


class TestWindow(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        self.parent = parent

        # other member variables
        self.path_gm = None
        self.checklist_dict = None
        self.initial_wid = None
        self.img_bgr = None
        self.img_h = None
        self.img_w = None
        self.img_d = None
        self.scale = None
        self.n_page = None
        self.shape_img_wid = None
        self.split_img_wid = None
        self.msg_map = None

        self.setGeometry(0, 0, 500, 300)

        time = datetime.now()
        self.temp_dir_path = "/var/tmp/module-qc-nonelec-gui/vi" + str(time)
        try:
            Path(self.temp_dir_path).mkdir(parents=True)
        except FileExistsError:
            shutil.rmtree(self.temp_dir_path)
            Path(self.temp_dir_path).mkdir(parents=True)

        # window title
        self.setWindowTitle("Visual Inspection GUI")

        # list and dict of anomalies
        self.anomaly_dic = {}
        self.comment_dic = {}
        self.img_dic = {}

        # component and user information
        self.atlsn = self.parent.info_dict["component"]
        self.type_name = self.parent.info_dict["componentType"]
        # self.original_institution = self.parent.info_dict["institution"]
        # self.current_location = self.parent.info_dict["currentLocation"]
        if self.type_name in ["MODULE", "PCB", "BARE_MODULE"]:
            self.stage = self.parent.info_dict["stage"]
            self.inspector = self.parent.db_user
        else:
            self.stage = ""
            self.inspector = ""

        # load configuration file
        log.info(f"type_name = {self.type_name}")
        log.info(f"stage = {self.stage}")

        stage_alt = self.stage.replace("/", "__")

        if self.type_name in ["MODULE", "PCB", "BARE_MODULE"]:
            self.json_default = str(
                Path(__file__).parent / f"config/config_{self.type_name}_default.json"
            )
            self.json_config = str(
                Path(__file__).parent
                / f"config/config_{self.type_name}_{stage_alt}.json"
            )

        with Path(self.json_default).open(encoding="utf-8") as f:
            self.config = json.load(f)
        with Path(self.json_config).open(encoding="utf-8") as f:
            self.custom = json.load(f)

            for key in [
                "frontside_goldenmodule_path",
                "backside_goldenmodule_path",
                "ntile",
                "nsplit",
                "backside",
                "tile_check_sequence",
            ]:
                if key in self.custom:
                    self.config[key] = self.custom[key]

            if "checklist" in self.custom:
                for side in ["front", "back"]:
                    if side in self.custom["checklist"]:
                        for flag in ["Yellow", "Red"]:
                            if flag in self.custom["checklist"][side]:
                                self.config["checklist"][side][flag] = (
                                    self.custom["checklist"][side][flag]
                                    + self.config["checklist"][side][flag]
                                )

        if self.config.get("backside") is True:
            QMessageBox.warning(
                self,
                "Warning",
                "Back-side inspection is required in this stage: "
                "please make sure that the photograph is already recorded at this point, "
                "otherwise you will be required to re-do the front-side inspection again!",
            )

        log.info(pprint.pformat(self.config))

        self.origImgPath = {"front": "", "back": ""}
        self.mode = "front"

        # checked page list
        self.rev = 0
        self.ntile = int(self.config["ntile"])
        self.tot_page = int(self.config["ntile"])
        self.nsplit = int(self.config["nsplit"])
        if self.config.get("tile_check_sequence"):
            self.tot_page = len(self.config.get("tile_check_sequence"))
            log.info(f"total number of pages overridden to {self.tot_page}")

        self.page_checked = []
        for i in range(int(self.config["ntile"])):
            self.page_checked.insert(i, False)

    def init_ui(self):
        # check the presence of golden modules

        try:
            self.path_gm = str(
                Path(__file__).parent
                / self.config[f"{self.mode}side_goldenmodule_path"]
            )

        except Exception:
            QMessageBox.warning(
                self,
                "Warning",
                f"{self.mode.capitalize()}-side Golden module path is undefined in the config file!",
            )

        try:
            with (Path(self.path_gm).parent / ".version").open(encoding="utf-8") as f:
                version_info = f.read()

                if version_info.find("2023-09-04") < 0:
                    msg = "Golden module version outdated"
                    raise Exception(msg)

        except Exception:
            log.exception("missing the golden image file")

            while True:
                msgBox = QMessageBox(self)
                msgBox.setTextFormat(Qt.RichText)
                msgBox.setText(
                    "Golden module image bank needs to be deployed.<br /><br />"
                    "[Step-1] Download the following zip file: "
                    '<br /><a href="https://cernbox.cern.ch/s/PAMujVUmRUni0um">https://cernbox.cern.ch/s/PAMujVUmRUni0um</a><br /><br />'
                    "[Step-2] Indicate the path of the zip file to this GUI."
                )
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBtn = msgBox.button(QMessageBox.Ok)
                msgBtn.setText("Yes, downloaded the zip file")
                msgBox.exec()

                dlg = QFileDialog(self)
                dlg.setFileMode(QFileDialog.FileMode.ExistingFiles)
                dlg.setNameFilter("ZIP files (*.zip)")
                dlg.setViewMode(QFileDialog.Detail)

                filename = None

                try:
                    dlg.show()
                    if dlg.exec_():
                        filename = dlg.selectedFiles()[0]
                        break
                except Exception:
                    log.error("fail in dlg.exec_()")
                    continue

            subprocess.run(
                f"cp {filename} /var/tmp; cd /var/tmp; unzip {filename.split('/')[-1]}",
                shell=True,
                check=False,
            )

            shutil.rmtree(str(Path(self.path_gm).parent))

            subprocess.run(
                f"mv -f /var/tmp/golden_module {Path(self.path_gm).parent.parent!s}; rm -rf /var/tmp/golden_module*",
                shell=True,
                check=False,
            )

            with Path(self.path_gm + "/main_img.jpg").open(encoding="utf-8") as f:
                pass

            QMessageBox.warning(
                self,
                "Information",
                "The latest golden module image bank was deployed.",
            )

        for index, _check in enumerate(self.page_checked):
            self.page_checked[index] = False

        self.anomaly_dic = {}
        self.comment_dic = {}
        self.img_dic = {}

        # check list
        self.checklist_dict = {}

        checklist = self.config["checklist"].get(self.mode)

        for tile in range(36):
            if checklist:
                self.checklist_dict[str(tile)] = checklist

        self.initial_wid = vi_initial_win.InitialWindow(self)
        self.parent.update_widget(self.initial_wid)

    def close_and_return(self):
        self.close()
        self.parent.back_from_test()

    def update_img(self, img):
        self.rev = self.rev + 1
        path = f"{self.temp_dir_path}/img_{self.mode}_{self.rev}.jpg"
        write_img(img, path)
        log.info(f"dumped image {path}")
        self.img_bgr, self.img_h, self.img_w, self.img_d = read_img(path)

    def load_img(self, mode="front"):
        options = QFileDialog.Options()
        inputFileName, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Images (*.bmp *.dib *.pbm *.pgm *.ppm *.sr *.ras *.jpeg *.jpg *.jpe *.jp2 *.png *.tiff *.tif);;Any files (*)",
            options=options,
        )
        if not inputFileName:
            log.info("image is not chosen")
        else:
            self.statusBar().showMessage(inputFileName)
            log.info(inputFileName)

            self.img_bgr, self.img_h, self.img_w, self.img_d = read_img(inputFileName)

            self.mode = mode

            self.origImgPath[self.mode] = (
                f"{self.temp_dir_path}/img_{self.mode}_org.jpg"
            )
            write_img(self.img_bgr, self.origImgPath[self.mode])

            if self.img_h > 1000 and self.img_w > 1000:
                self.scale = 10
            else:
                self.scale = 1
            self.n_page = 0
            log.info("OpenCV image read success.")

            self.rev = 0

            self.shape_img()

    def shape_img(self):
        log.info("shape_img()")
        img, h, w, d = read_img(self.origImgPath.get(self.mode))

        stage = self.parent.info_dict.get("stage", "")
        log.info(f"shape_img(): stage = {stage}")

        if "BAREMODULE" in stage:
            if self.mode == "front":
                self.shape_img_wid = shaping_win.BareFrontTrimmer(self, {})
            elif self.mode == "back":
                self.shape_img_wid = shaping_win.QuadBackTrimmer(self, {})
        elif "MODULE" in stage:
            if self.mode == "front":
                if "pictures_param" in self.custom:
                    self.shape_img_wid = shaping_win.QuadFrontTrimmer(
                        self, self.custom["pictures_param"]
                    )
                else:
                    self.shape_img_wid = shaping_win.QuadFrontTrimmer(self, {})
            elif self.mode == "back":
                if "pictures_param" in self.custom:
                    self.shape_img_wid = shaping_win.QuadBackTrimmer(
                        self, self.custom["pictures_param"]
                    )
                else:
                    self.shape_img_wid = shaping_win.QuadBackTrimmer(self, {})

        elif "PCB" in stage:
            if self.mode == "front":
                self.shape_img_wid = shaping_win.QuadFrontTrimmer(
                    self, {"CropRange": 31.0}
                )
            elif self.mode == "back":
                self.shape_img_wid = shaping_win.QuadPCBBackTrimmer(
                    self,
                    {
                        "CropRange": 31.0,
                        "Brightness": -50,
                        "Contrast": 2.0,
                        "InitialBlur": 8,
                        "InitialParam2": 35,
                    },
                )

        self.parent.update_widget(self.shape_img_wid)

    def rotate_img(self):
        try:
            img, h, w, d = read_img(
                f"{self.temp_dir_path}/img_{self.mode}_{self.rev}.jpg"
            )
        except Exception:
            img, h, w, d = read_img(self.origImgPath.get(self.mode))

        img, h, w, d = img_rotate(img)
        self.update_img(img)

    def split_img(self):
        self.split_img_wid = splitimg_win.SplitImageWindow(self)
        self.parent.update_widget(self.split_img_wid)

    def inspection(self):
        # Guiding dialog
        self.msg_map = {
            "BAREMODULERECEPTION": "Check carefully for defect at the edges and cornners of both sensor and FE chips.",
            "MODULE/ASSEMBLY": "Check carefully:\n * Glue must not reach the edge of sensor/PCB;\n * Glue does not infiltrate the pads or back-side of the sensor",
            "MODULE/WIREBONDING": "Check carefully:\n * All wires match the wire bond map;\n * No shorts due to bad bonding.",
            "MODULE/PARYLENE_MASKING": "Check carefully:\n * Masking of pickup points;\n * Masking of pigtail connectors;\n * Back-side masking",
            "MODULE/PARYLENE_COATING": "Check carefully:\n * Quality of parylene coating",
            "MODULE/PARYLENE_UNMASKING": 'Check carefully:\n * Has the parylene coating penetrated the pickup and strain relief or connector areas?\n * Are there any areas where de-lamination of the parylene layer is seen that may result in contamination of the module?\n * Is the back of the module free of parylene such that only small "witness marks" are visible on the edges of the ASICs?',
            "MODULE/WIREBOND_PROTECTION": "",
            "MODULE/THERMAL_CYCLES": "",
            "PCB_RECEPTION": "Check carefully the central part for defects, including scratches, surface contamination and other damage.",
            "PCB_POPULATION": "Check carefully the central part for defects, especially soldering problems.",
            "PCB_CUTTING": "",
            "PCB_RECEPTION_MODULE_SITE": "",
        }

        if self.n_page == 0:
            QMessageBox.information(
                self,
                "Note",
                "\n\n".join(
                    [
                        self.parent.info_dict.get("stage", ""),
                        self.msg_map.get(self.parent.info_dict.get("stage", ""), ""),
                        "Key-binds:\n * X: Checkout Tile\n * F: Next Page\n * B: Previous Page\n * S: Switch Target/Reference",
                    ]
                ),
            )

        inspection_wid = inspection_win.InspectionWindow(self)
        self.parent.update_widget(inspection_wid)

    def make_result(self):
        path_target = f"{self.temp_dir_path}/main_{self.mode}_img.jpg"
        cv2.imwrite(path_target, self.img_bgr)

        oid_target = str(
            localdb_uploader.jpeg_formatter(self.parent.localDB, path_target)
        )

        for page, path_jpeg in self.img_dic.items():
            self.img_dic[page] = str(
                localdb_uploader.jpeg_formatter(self.parent.localDB, path_jpeg)
            )

        self.parent.testRun["results"]["Metadata"][
            f"{self.mode}_defects"
        ] = self.anomaly_dic
        self.parent.testRun["results"]["Metadata"][
            f"{self.mode}_comments"
        ] = self.comment_dic
        self.parent.testRun["results"]["Metadata"][f"{self.mode}_image"] = oid_target
        self.parent.testRun["results"]["Metadata"][
            f"{self.mode}_defect_images"
        ] = self.img_dic
        # Fill in operator and instrument properties (PCB only)
        if self.type_name == "PCB":
            self.parent.testRun["results"]["property"]["OPERATOR"] = self.inspector
            self.parent.testRun["results"]["property"]["INSTRUMENT"] = self.instrument

        if self.config.get("backside") is True and self.mode == "front":
            self.mode = "back"
            self.init_ui()

        else:
            self.return_result()

    def go_to_summary(self, sub):
        sub.hide()
        summary_wid = summary_win.SummaryWindow(self)
        self.parent.update_widget(summary_wid)

    def return_result(self):
        self.parent.receive_result(self)
