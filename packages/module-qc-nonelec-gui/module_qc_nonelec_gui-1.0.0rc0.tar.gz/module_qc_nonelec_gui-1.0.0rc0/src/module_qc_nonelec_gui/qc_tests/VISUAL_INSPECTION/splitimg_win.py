from __future__ import annotations

import logging
from pathlib import Path

import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QPushButton,
    QWidget,
)

from module_qc_nonelec_gui.qc_tests.VISUAL_INSPECTION.functions.cv2_func import (
    img_cvt_rgb,
    read_img,
    write_img,
)

# Import ML scan functions
from module_qc_nonelec_gui.qc_tests.VISUAL_INSPECTION.functions.ml_apply import (
    ML_unsup_scan,  # ML_sup_scan TODO not available yet
)

log = logging.getLogger(__name__)


class SplitImageWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        layout = QGridLayout()

        self.setMinimumWidth(650)
        self.setMinimumHeight(700)

        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        self.parent.update_img(self.parent.img_bgr)
        self.img_bgr_line, h, w, _d = read_img(
            f"{self.parent.temp_dir_path}/img_{self.parent.mode}_{self.parent.rev}.jpg"
        )

        nsplit = self.parent.config.get("nsplit", 6)
        grid_size_w = int(w / nsplit)
        grid_size_h = int(h / nsplit)

        # Check if a ML model is available for this component and stage
        self.parent.overlay = False
        model_path = str(Path(__file__).parent)
        if self.parent.mode == "front":
            model_path = (
                model_path
                + f"/model/model_{self.parent.type_name}_{self.parent.stage}/"
            )
        else:
            model_path = (
                model_path
                + f"/model/model_{self.parent.type_name}_{self.parent.stage}_back/"
            )
        if Path.exists(Path(model_path)):
            log.info("Found ML model for automatic defect scan.")
            log.info("RUNNING SCAN ...")

            # Check unsupervised defect scan
            if Path.exists(Path(model_path + "AE_config.txt")):
                self.parent.img_rgb_overlay = ML_unsup_scan(
                    self.img_bgr_line,
                    [grid_size_h, -grid_size_h, grid_size_w, -grid_size_w],
                    model_path,
                )
                self.parent.overlay = True

        for i in range(nsplit - 1):
            # draw vertical line
            self.img_bgr_line = cv2.line(
                self.img_bgr_line,
                (grid_size_w * (i + 1), 0),
                (grid_size_w * (i + 1), h),
                (0, 255, 128),
                10,
            )
            # draw horizontal line
            self.img_bgr_line = cv2.line(
                self.img_bgr_line,
                (0, grid_size_h * (i + 1)),
                (w, grid_size_h * (i + 1)),
                (0, 255, 128),
                10,
            )

        path_line = f"{self.parent.temp_dir_path}/split_{self.parent.mode}_img.jpg"
        write_img(self.img_bgr_line, path_line)
        img_bgr_line, h_line, w_line, _d_line = read_img(path_line)
        scale = 600.0 / max(float(h_line), float(w_line)) * 0.97
        resize_img = cv2.resize(
            img_bgr_line,
            dsize=None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_LANCZOS4,
        )
        img_rgb, h_rgb, w_rgb, d_rgb = img_cvt_rgb(resize_img)
        bytesPerLine = d_rgb * w_rgb

        self.image = QImage(
            img_rgb.data, w_rgb, h_rgb, bytesPerLine, QImage.Format_RGB888
        )
        self.item = QGraphicsPixmapItem(QPixmap.fromImage(self.image))
        self.scene.addItem(self.item)

        # Add the overlay image if available
        if self.parent.overlay:
            over_rgb = cv2.resize(
                self.parent.img_rgb_overlay, dsize=None, fx=scale, fy=scale
            )
            bytesPerLine2 = (d_rgb + 1) * w_rgb
            self.image2 = QImage(
                over_rgb.data, w_rgb, h_rgb, bytesPerLine2, QImage.Format_RGBA8888
            )
            self.item2 = QGraphicsPixmapItem(QPixmap.fromImage(self.image2))
            self.scene.addItem(self.item2)

        self.view.setScene(self.scene)
        self.view.setFixedWidth(600)
        self.view.setFixedHeight(600)
        layout.addWidget(self.view, 0, 0)

        button_start = QPushButton("Start Inspection")
        button_start.clicked.connect(self.start)

        layout.addWidget(button_start, 1, 0)
        self.setLayout(layout)

    def start(self):
        self.close()
        self.parent.inspection()
