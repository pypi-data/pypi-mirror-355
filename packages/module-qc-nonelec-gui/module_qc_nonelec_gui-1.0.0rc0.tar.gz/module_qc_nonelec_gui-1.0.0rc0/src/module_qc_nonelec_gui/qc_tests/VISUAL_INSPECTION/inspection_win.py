from __future__ import annotations

import contextlib
import logging
import re
from functools import reduce
from pathlib import Path

import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QImage, QPixmap, qt_set_sequence_auto_mnemonic
from PyQt5.QtWidgets import (
    QCheckBox,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# import checklist
# import checklist_Module
# import checklist_PCB
from module_qc_nonelec_gui.qc_tests.VISUAL_INSPECTION.functions.cv2_func import (
    img_cvt_rgb,
    read_img,
    write_img,
)

log = logging.getLogger(__name__)


class InspectionWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)

        log.debug("__init__:Init InspectionWindow")
        log.debug("__init__:---------------------")

        self.parent = parent
        self.brightness = None
        self.contrast = None
        self.tile_position = self.tile_to_be_seen(self.parent.n_page)
        log.debug(
            f">>>>> n_page: {self.parent.n_page}, tile_position:{self.tile_position}"
        )

        self.TabWidget = None

        layout = QHBoxLayout()

        switch_button_layout = QHBoxLayout()

        self.img_bgr = self.parent.img_bgr
        self.img_h = self.parent.img_h
        self.img_w = self.parent.img_w

        if "pictures_param" in self.parent.custom:
            self.brightness = self.parent.custom["pictures_param"].get("Brightness", 0)
            self.contrast = self.parent.custom["pictures_param"].get("Contrast", 1.0)
        else:
            self.brightness = 0
            self.contrast = 1.0

        ## prepare target images
        log.debug("__init__:   Prepare split image to check")
        self.path_target = self.split_img(self.img_bgr, self.parent.n_page)

        log.debug("__init__:   Prepare GM image")
        current_gm_tile_filename = f"tile{self.tile_to_be_seen(self.parent.n_page)}.jpg"
        self.path_gm = str(Path(self.parent.path_gm, current_gm_tile_filename))

        self.view = self.setImg(
            self.path_target,
            0,
            self.contrast,
            self.brightness,
        )
        self.view_gm = self.setImg(self.path_gm, 1)

        # Prepare anomaly overlay if available
        if self.parent.overlay:
            self.view_over = self.setImg(
                self.path_target, 2, self.contrast, self.brightness, overlay=True
            )

        # prepare window
        label_page = QLabel(self)
        label_page.setText(f"page: {self.parent.n_page + 1}/{self.parent.tot_page}")

        label_message = QLabel(self)
        label_message.setText("Tick checkboxes for identified defects.")

        label_message2 = QLabel(self)

        label_message2.setText(
            self.parent.msg_map.get(self.parent.parent.info_dict.get("stage"))
        )

        label_comment = QLabel(self)
        label_comment.setText("Describe observation and details of defects:")

        self.edit_comment = QPlainTextEdit(self)
        self.edit_comment.setFixedHeight(100)
        with contextlib.suppress(Exception):
            self.edit_comment.setPlainText(
                self.parent.comment_dic[str(self.parent.n_page)]
            )

        ## prepare buttons
        label_brightness = QLabel(self)
        label_brightness.setText("Brightness: ")

        label_contrast = QLabel(self)
        label_contrast.setText("Contrast: ")

        self.input_brightness = QLineEdit(self)
        self.input_brightness.setFixedWidth(30)
        self.input_brightness.setValidator(QDoubleValidator(-100, 100, 0))
        self.input_brightness.setText(str(self.brightness))

        self.input_contrast = QLineEdit(self)
        self.input_contrast.setFixedWidth(30)
        self.input_contrast.setValidator(QDoubleValidator(0.0, 2.0, 1))
        self.input_contrast.setText(str(self.contrast))

        switch_button_layout.addWidget(label_brightness)
        switch_button_layout.addWidget(self.input_brightness)
        switch_button_layout.addWidget(label_contrast)
        switch_button_layout.addWidget(self.input_contrast)

        self.input_brightness.returnPressed.connect(self.retouch)
        self.input_contrast.returnPressed.connect(self.retouch)

        self.button_checked = QPushButton("Checkout This Tile", self)
        self.button_checked.setCheckable(True)
        self.button_checked.clicked.connect(self.checkout)
        self.button_checked.setChecked(self.parent.page_checked[self.parent.n_page])

        button_back = QPushButton("Back", self)
        button_back.clicked.connect(self.back_page)
        button_next = QPushButton("Next", self)
        button_next.clicked.connect(self.next_page)

        if self.parent.type_name == "PCB":
            pass
            # button_vanilla = QPushButton("Vanilla", self)
            # button_vanilla.clicked.connect(self.setVanillaImg)
            # button_platting = QPushButton("Platting", self)
            # button_platting.clicked.connect(self.setPlattingImg)
            # button_smd = QPushButton("SMD", self)
            # button_smd.clicked.connect(self.setSMDImg)

        if self.parent.type_name == "MODULE":
            if self.parent.stage == "MODULETOPCB":
                button_vanilla = QPushButton("Vanilla", self)
                button_vanilla.clicked.connect(self.setVanillaImg)
                button_platting = QPushButton("Platting", self)
                button_platting.clicked.connect(self.setPlattingImg)
                button_smd = QPushButton("SMD", self)
                button_smd.clicked.connect(self.setSMDImg)

                switch_button_layout.addWidget(button_vanilla)
                switch_button_layout.addWidget(button_platting)
                switch_button_layout.addWidget(button_smd)

            else:
                button_vanilla = QPushButton("Vanilla", self)
                button_vanilla.clicked.connect(self.setVanillaImg)
                button_wire = QPushButton("Wire", self)
                button_wire.clicked.connect(self.setWireImg)

                switch_button_layout.addWidget(button_vanilla)
                switch_button_layout.addWidget(button_wire)

        self.checklist_gen(self.parent.n_page, self.parent.tot_page)

        cb_layout_list = []
        for first_key, value in self.cb.items():
            cb_layout_list.append(QVBoxLayout())
            cb_layout_list[-1].setAlignment(Qt.AlignTop)
            label = QLabel()
            label.setText(first_key + " Defects")
            label.resize(200, 30)
            cb_layout_list[-1].addWidget(label)
            for _second_key, checkbox in value.items():
                cb_layout_list[-1].addWidget(checkbox)

        cb_layout = QHBoxLayout()
        for i in cb_layout_list:
            cb_layout.addLayout(i)

        cb_widget = QWidget()
        cb_widget.setLayout(cb_layout)

        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setWidget(cb_widget)

        input_layout = QGridLayout()
        input_layout.addWidget(label_message, 0, 0)
        input_layout.addWidget(label_message2, 1, 0)
        input_layout.addWidget(outer, 2, 0)
        input_layout.addWidget(label_comment, 3, 0)
        input_layout.addWidget(self.edit_comment, 4, 0)
        input_layout.addWidget(self.button_checked, 5, 0)

        button_layout = QHBoxLayout()
        button_layout.addWidget(button_back)
        button_layout.addStretch()
        button_layout.addWidget(button_next)

        switch_button_layout.addStretch()
        switch_button_layout.addWidget(label_page)

        control_layout = QVBoxLayout()
        control_layout.addLayout(switch_button_layout)
        control_layout.addLayout(input_layout)
        control_layout.addLayout(button_layout)

        layout.addLayout(self.make_tab_layout())
        #        layout.addLayout( input_layout )
        layout.addLayout(control_layout)
        self.setLayout(layout)
        self.setFixedSize(layout.sizeHint())

    def keyPressEvent(self, event):
        if event.key() == 83:  # s
            self.TabWidget.setCurrentIndex(1 - self.TabWidget.currentIndex())
        if event.key() == 88:  # x
            self.button_checked.setChecked(True)
            self.checkout()
        if event.key() == 70:  # f
            pageStatus = self.parent.page_checked[self.parent.n_page]
            if pageStatus is False:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "The tile is not checked out!",
                )
            else:
                self.next_page()

            return

        if event.key() == 66:  # b
            self.back_page()

    def back_page(self):
        self.anomaly_update()
        if self.parent.n_page == 0:
            QMessageBox.warning(
                self,
                "Warning",
                "This is the first tile",
            )
        else:
            self.parent.n_page = self.parent.n_page - 1

        self.parent.inspection()

    def next_page(self):
        self.anomaly_update()

        if self.check_status():
            log.info("Inspected all tiles ==> goto summary")
            self.close()
            self.parent.go_to_summary(self)

        else:
            if self.parent.n_page == self.parent.tot_page - 1:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "This is the last tile",
                )
            else:
                self.parent.n_page = self.parent.n_page + 1

            self.parent.inspection()

    def setImg(self, path, index, contrast=1.3, brightness=15.0, overlay=False):
        view = QGraphicsView(self)

        log.info(f"setImg(): path = {path}")

        pictRefSize = 800.0
        img, h, w, d = read_img(path)
        scale = min(pictRefSize / float(h), pictRefSize / float(w))
        imgResizedForQtWindow = cv2.resize(
            img, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4
        )
        out = cv2.convertScaleAbs(
            imgResizedForQtWindow, alpha=contrast, beta=brightness
        )
        img_rgb, h, w, d = img_cvt_rgb(out)
        bytesPerLine = d * w
        qImage = QImage(img_rgb.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixItem = QGraphicsPixmapItem(QPixmap.fromImage(qImage))
        pixItem.setPixmap(pixItem.pixmap())

        scene = QGraphicsScene()
        scene.addItem(pixItem)

        # Add anomaly overlay if specified
        if overlay:
            self.tile_img_over = cv2.resize(
                self.tile_img_over,
                dsize=None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_LANCZOS4,
            )
            bytesPerLine2 = (d + 1) * w
            qImage2 = QImage(
                bytes(self.tile_img_bgr.data),
                w,
                h,
                bytesPerLine2,
                QImage.Format_RGBA8888,
            )
            pixItem2 = QGraphicsPixmapItem(QPixmap.fromImage(qImage2))
            pixItem2.setPixmap(pixItem2.pixmap().scaled(800, 800, Qt.KeepAspectRatio))
            scene.addItem(pixItem2)

        view.setScene(scene)
        rect = scene.sceneRect()
        log.info(
            f"setImg(): scene {rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}"
        )
        # view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # view.fitInView( -400, -400, 800, 800, Qt.KeepAspectRatio)

        if self.TabWidget:
            tab = self.TabWidget.widget(index)
            tab.layout().itemAt(0).widget().deleteLater()
            tab.layout().addWidget(view)

        return view

    def retouch(self):
        ## prepare target images
        self.path_target = self.split_img(self.img_bgr, self.parent.n_page)

        self.brightness = float(self.input_brightness.text())
        self.contrast = float(self.input_contrast.text())

        log.info(
            f"retouch(): retouching the target image with brightness = {self.brightness}, "
            f"contrast = {self.contrast}"
        )

        self.view = self.setImg(
            self.path_target,
            0,
            self.contrast,
            self.brightness,
        )
        self.view_gm = self.setImg(self.path_gm, 1, 1.3, 15.0)

    def setVanillaImg(self):
        self.setImg(self.path_gm, 1)

    def setPlattingImg(self):
        try:
            self.setImg(
                self.parent.path_gm + f"/tile{self.parent.n_page}_plating.jpg", 1
            )
        except Exception:
            self.setImg(self.path_gm, 1)

    def setSMDImg(self):
        try:
            self.setImg(self.parent.path_gm + f"/tile{self.parent.n_page}_SMD.png", 1)
        except Exception:
            self.setImg(self.path_gm, 1)

    def setWireImg(self):
        try:
            self.setImg(
                self.parent.path_gm + f"/tile{self.parent.n_page}_wireline.jpg", 1
            )
        except Exception:
            self.setImg(self.path_gm, 1)

    def checkout(self):
        if self.parent.page_checked[self.parent.n_page] is False:
            self.anomaly_update()
            self.parent.comment_dic[str(self.parent.n_page)] = (
                self.edit_comment.toPlainText()
            )

            self.parent.page_checked[self.parent.n_page] = True
            log.debug(f" Just checked out: tileID {self.parent.n_page} ")
            log.debug(f" Tiles checked: {self.nb_checked()} ")

        else:
            self.parent.page_checked[self.parent.n_page] = False
            log.debug(f" Just checked in: tileID {self.parent.n_page} ")
            log.debug(f" Tiles checked: {self.nb_checked()} ")

    def nb_checked(self):
        return reduce(lambda a, b: int(a) + int(b), self.parent.page_checked)

    def check_status(self):
        n_checked = self.nb_checked()

        log.info(f"checked tiles: {n_checked} / {self.parent.tot_page}")

        return n_checked == self.parent.tot_page

    def checkBoxChangeAction(self, state, element):
        if Qt.Checked == state:
            try:
                self.parent.anomaly_dic[str(self.parent.n_page)].append(element)
            except Exception:
                self.parent.anomaly_dic[str(self.parent.n_page)] = [element]
            pathexsit = False
            try:
                for path in self.parent.img_dic.values():
                    p = re.split("[/_.]", path)[3]
                    # print("current page is " + p)
                    if str(self.parent.n_page) == p:
                        pathexsit = True
                if not pathexsit:
                    self.parent.img_dic[str(self.parent.n_page)] = self.path_target
            except Exception:
                self.parent.img_dic[str(self.parent.n_page)] = self.path_target
            # print("anomaly at " + element)
        else:
            self.parent.anomaly_dic[str(self.parent.n_page)].remove(element)
            del self.parent.img_dic[str(self.parent.n_page)]

    def anomaly_update(self):
        categories = list(self.parent.checklist_dict[str(self.parent.n_page)].keys())

        for category in categories:
            items = self.parent.checklist_dict[str(self.parent.n_page)][category]
            for index, item in enumerate(items):
                try:
                    state = self.cb[category][index].checkState()
                    self.checkbox_action(category, state, item)
                except Exception:
                    pass
        self.image_update()

    def checkbox_action(self, category, state, item):
        defectId = ".".join(
            [category, item.replace(" ", "_").replace("(", "").replace(")", "")]
        )

        if state == Qt.Checked:
            if str(self.parent.n_page) not in self.parent.anomaly_dic:
                self.parent.anomaly_dic[str(self.parent.n_page)] = [defectId]
            elif defectId not in self.parent.anomaly_dic[str(self.parent.n_page)]:
                self.parent.anomaly_dic[str(self.parent.n_page)].append(defectId)
        else:
            if (
                str(self.parent.n_page) in self.parent.anomaly_dic
                and defectId in self.parent.anomaly_dic[str(self.parent.n_page)]
            ):
                self.parent.anomaly_dic[str(self.parent.n_page)].remove(defectId)

    def image_update(self):
        is_anomaly = False
        if str(self.parent.n_page) in self.parent.anomaly_dic:
            if len(self.parent.anomaly_dic[str(self.parent.n_page)]):
                is_anomaly = True
        elif len(self.edit_comment.toPlainText()) > 0:
            is_anomaly = True

        if is_anomaly:
            if str(self.parent.n_page) not in self.parent.img_dic:
                self.parent.img_dic[str(self.parent.n_page)] = self.path_target
                log.debug(
                    f"Add img {self.path_target} to img_dic[{self.parent.n_page}]"
                )
        else:
            if str(self.parent.n_page) in self.parent.img_dic:
                del self.parent.img_dic[str(self.parent.n_page)]

    def write_data(self):
        self.parent.write_to_localdb()

    def tile_to_be_seen(self, n_page):
        # Call the "tile_check_sequence" list from custom JSON
        if "tile_check_sequence" in self.parent.custom:
            output = self.parent.custom["tile_check_sequence"][n_page]
        else:
            output = n_page

        return output

    def split_img(self, _img, n_page):
        current_tile = self.tile_to_be_seen(n_page)
        # Define number of columns and rows
        col, row = divmod(current_tile, self.parent.nsplit)
        ncol, _mod = divmod(self.parent.ntile, self.parent.nsplit)
        assert _mod == 0
        nrow = n_page / ncol

        # Define nominal width and height of all tiles
        grid_size_w = int(self.img_w / self.parent.nsplit)
        grid_size_h = int(self.img_h / self.parent.nsplit)

        log.info(f"split_img(): grid_size: width={grid_size_w}, height={grid_size_h} ")
        log.info(
            f"split_img(): full image dimensions: width={self.img_w}, height={self.img_h} "
        )

        # Change picture navigation order according to stage
        stage = self.parent.stage
        log.info(f"split_img(): current stage = {stage}")

        i = row
        j = col

        #  Define pixel coordinates for the current tile to be extracted from original picture
        y1 = grid_size_w * i
        y2 = grid_size_w * (i + 1)
        x1 = grid_size_h * j
        x2 = grid_size_h * (j + 1)

        # Picture margin for the standard navigation over the module
        if i == 0:
            y1 = 0
        elif i == nrow - 1:
            y1 -= 100
        else:
            y1 -= 50

        if i == 0:
            y2 += 100
        elif i == nrow - 1:
            y2 = self.img_w
        else:
            y2 += 50

        if j == 0:
            x1 = 0
        elif j == ncol - 1:
            x1 -= 100
        else:
            x1 -= 50

        if j == 0:
            x2 += 100
        elif j == ncol - 1:
            x2 = self.img_h
        else:
            x2 += 50

        log.info(
            f"split_img(): {current_tile} / {self.parent.tot_page}: [{y1}:{y2}, {x1}:{x2}] "
        )
        self.tile_img_bgr = self.img_bgr[x1:x2, y1:y2]
        # Automatically split the anomaly overlay if available
        if self.parent.overlay:
            self.tile_img_over = self.parent.img_rgb_overlay[x1:x2, y1:y2]

        split_image_file_path = str(
            Path(
                self.parent.temp_dir_path,
                f"tile_img_{self.parent.mode}_{current_tile}.jpg",
            )
        )
        write_img(
            self.tile_img_bgr,
            split_image_file_path,
        )

        log.debug(f"split_img() - saved tile: {split_image_file_path}")
        return split_image_file_path

    def checklist_gen(self, page, _tot_page):
        self.cb = {}

        defectTypes = self.parent.checklist_dict.get(str(page))

        defects = self.parent.anomaly_dic.get(str(page))

        categories = list(defectTypes.keys())

        for _index_key, key in enumerate(categories):
            items = defectTypes[key]
            # nitems = len(items)
            # interval = int(h / (nitems + 1))
            self.cb[key] = {}
            for index, item in enumerate(items):
                self.cb[key][index] = QCheckBox(item, self)
                if key == "Wire":
                    _q, _mod = divmod(index, 20)

                try:
                    if defects is None:
                        continue

                    defectId = ".".join(
                        [key, item.replace(" ", "_").replace("(", "").replace(")", "")]
                    )

                    if defectId in defects:
                        self.cb[key][index].toggle()

                except Exception as e:
                    log.exception(str(e))

    def make_tab_layout(self):
        layout = QHBoxLayout()

        self.TabWidget = QTabWidget()
        self.TabWidget.resize(850, 850)
        self.TabWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Check for overlay
        if self.parent.overlay:
            for view, title in zip(
                [self.view, self.view_over, self.view_gm],
                ["&Target", "&Defects", "&Reference"],
                strict=False,
            ):
                self.add_tab(
                    self.make_tab(view),
                    self.TabWidget,
                    title,
                )
        else:
            for view, title in zip(
                [self.view, self.view_gm], ["&Target", "&Reference"]
            ):
                self.add_tab(
                    self.make_tab(view),
                    self.TabWidget,
                    title,
                )

        layout.addWidget(self.TabWidget)
        return layout

    def add_tab(self, layout, TabWidget, tab_label):
        qt_set_sequence_auto_mnemonic(True)

        tab = QWidget()
        tab.setFixedWidth(850)
        tab.setFixedHeight(850)
        tab.setLayout(layout)

        TabWidget.addTab(tab, tab_label)

    def make_tab(self, view):
        layout = QHBoxLayout()
        layout.addWidget(view)

        return layout
