from __future__ import annotations

import logging
import math
import statistics
import time

import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtGui import QBrush, QDoubleValidator, QImage, QPen, QPixmap
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QWidget,
)

from module_qc_nonelec_gui.qc_tests.VISUAL_INSPECTION.functions.cv2_func import (
    img_cvt_rgb,
)

log = logging.getLogger(__name__)

preview_size = 600
resize_length = 1200


class GraphicsScene(QGraphicsScene):
    def __init__(self, trimmer=None):
        QGraphicsScene.__init__(self, None)
        self.setSceneRect(0, 0, 0, 0)
        self.trimmer = trimmer
        self.turn = 0
        self.GA1_x = 0
        self.GA1_y = 0
        self.GA3_x = 0
        self.GA3_y = 0

    def mousePressEvent(self, event):
        x = event.scenePos().x()
        y = event.scenePos().y()

        if self.turn == 0:
            self.GA1_x = x
            self.GA1_y = y
            self.turn = 1

            self.addEllipse(
                self.GA1_x - 5,
                self.GA1_y - 5,
                10,
                10,
                QPen(QtCore.Qt.yellow),
                QBrush(QtCore.Qt.yellow),
            )
        else:
            self.GA3_x = x
            self.GA3_y = y
            self.turn = 0

            self.addEllipse(
                self.GA3_x - 5,
                self.GA3_y - 5,
                10,
                10,
                QPen(QtCore.Qt.yellow),
                QBrush(QtCore.Qt.yellow),
            )

            time.sleep(1)

            self.trimmer.trim_image_manual(
                {
                    "GA1": {"x": self.GA1_x, "y": self.GA1_y},
                    "GA3": {"x": self.GA3_x, "y": self.GA3_y},
                }
            )


class Trimmer(QWidget):
    def __init__(self, parent, custom_params):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.cropped = None
        self.image = None
        self.item = None

        log.info(f"Trimmer.__init__(): custom_params = {custom_params}")

        self.nLayoutRows = 0

        self.setupCommon1()
        self.setupCustom(custom_params)
        self.setupCommon2()

        self.tmp_cropped_path = f"{self.parent.temp_dir_path}/tmp_cropped.jpg"
        self.tmp_preview_path = f"{self.parent.temp_dir_path}/tmp_preview.jpg"

        self.trim()

    def setupCommon1(self):
        self.layout = QGridLayout()

        # scene for module picture
        self.view = QGraphicsView()
        self.scene = GraphicsScene(self)
        self.view.setScene(self.scene)

        # load module picture
        img_org = cv2.imread(self.parent.origImgPath[self.parent.mode])
        h, w, d = img_org.shape
        scale = min(preview_size / float(h), preview_size / float(w))

        resize_img = cv2.resize(
            img_org, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4
        )

        img_rgb, h_rgb, w_rgb, d_rgb = img_cvt_rgb(resize_img)
        bytesPerLine = d_rgb * w_rgb

        self.image = QImage(
            img_rgb.data, w_rgb, h_rgb, bytesPerLine, QImage.Format_RGB888
        )
        self.item = QGraphicsPixmapItem(QPixmap.fromImage(self.image))
        self.scene.addItem(self.item)
        self.view.setScene(self.scene)
        self.view.setFixedWidth(preview_size + 50)
        self.view.setFixedHeight(preview_size + 50)

        self.layout.addWidget(self.view, self.nLayoutRows, 0, 1, 2)
        self.nLayoutRows = self.nLayoutRows + 1

        self.buttons = QHBoxLayout()

    def setupCustom(self, custom_params):
        pass

    def setupCommon2(self):
        button_back = QPushButton("Back")
        button_back.clicked.connect(self.parent.load_img)

        button_rotate = QPushButton("Rotate (+90°)")
        button_rotate.clicked.connect(self.rotate)

        button_crop = QPushButton("Preview")
        button_crop.clicked.connect(self.trim)

        button_ok = QPushButton("Next")
        button_ok.clicked.connect(self.go_next)

        self.buttons.addWidget(button_back)
        self.buttons.addWidget(button_rotate)
        self.buttons.addWidget(button_crop)
        self.buttons.addWidget(button_ok)

        self.layout.addLayout(self.buttons, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1
        self.setLayout(self.layout)

    def rotate(self):
        self.parent.rotate_img()  # ROTATE_90_CLOCKWISE
        self.trim()

    def trim(self):
        try:
            self.trim_image(self.getParameters())

        except Exception as e:
            log.exception(e)

            QMessageBox.warning(
                self,
                "Warning",
                "Failed in cropping!\n\nManually click the center of the GA1 Pickup Point, "
                "and then click the center of the GA3 Pickup Point to determine the frame",
            )

        preview = cv2.imread(self.tmp_preview_path)

        self.cropped = cv2.imread(self.tmp_cropped_path)

        h, w, d = preview.shape

        scale = min(preview_size / float(h), preview_size / float(w))

        resize_img = cv2.resize(
            preview, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4
        )

        img_rgb, h_rgb, w_rgb, d_rgb = img_cvt_rgb(resize_img)
        bytesPerLine = d_rgb * w_rgb

        self.image = QImage(
            img_rgb.data, w_rgb, h_rgb, bytesPerLine, QImage.Format_RGB888
        )

        self.view.items().clear()
        self.scene.clear()

        pixmap = QPixmap.fromImage(self.image)
        self.item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.item)
        self.view.setScene(self.scene)

    def trim_image(self, params):
        log.info(params)

    def getParameters(self):
        return {}

    def go_next(self):
        self.parent.update_img(self.cropped)
        self.parent.split_img()


#################################################################################################


class QuadFrontTrimmer(Trimmer):
    def setupCustom(self, custom_params):
        self.cropRange = custom_params.get("CropRange", 21.8)
        log.info(f"setupCustom(): Custom Crop Range = {self.cropRange} mm")

        self.handles = QHBoxLayout()
        self.handles2 = QHBoxLayout()

        label_rot = QLabel(self)
        label_rot.setText("Rotation: [-3.00, 3.00]")

        label_brightness = QLabel(self)
        label_brightness.setText("Brightness: [-100, 100]")

        label_contrast = QLabel(self)
        label_contrast.setText("Contrast: [0, 2]")

        label_blur = QLabel(self)
        label_blur.setText("Blur: [3, 10]")

        label_tweak = QLabel(self)
        label_tweak.setText("Tweak: [20, 50]")

        self.input_rot = QDoubleSpinBox()
        self.input_rot.setMinimum(-3)
        self.input_rot.setMaximum(3)
        self.input_rot.setSingleStep(0.1)
        self.input_rot.setFixedWidth(50)

        self.input_brightness = QSpinBox()
        self.input_brightness.setMinimum(-100)
        self.input_brightness.setMaximum(100)
        self.input_brightness.setSingleStep(10)
        self.input_brightness.setFixedWidth(50)
        self.input_brightness.setValue(custom_params.get("Brightness", -20))

        self.input_contrast = QDoubleSpinBox()
        self.input_contrast.setMinimum(0.0)
        self.input_contrast.setMaximum(2.0)
        self.input_contrast.setSingleStep(0.1)
        self.input_contrast.setFixedWidth(50)
        self.input_contrast.setValue(custom_params.get("Contrast", 1.3))

        self.input_blur = QSpinBox()
        self.input_blur.setMinimum(3)
        self.input_blur.setMaximum(10)
        self.input_blur.setSingleStep(1)
        self.input_blur.setFixedWidth(40)
        self.input_blur.setValue(custom_params.get("InitialBlur", 5))

        self.input_tweak = QSpinBox()
        self.input_tweak.setMinimum(20)
        self.input_tweak.setMaximum(50)
        self.input_tweak.setSingleStep(5)
        self.input_tweak.setFixedWidth(40)
        self.input_tweak.setValue(custom_params.get("InitialParam2", 35))

        self.handles.addWidget(label_rot)
        self.handles.addWidget(self.input_rot)
        self.handles.addWidget(label_brightness)
        self.handles.addWidget(self.input_brightness)
        self.handles.addWidget(label_contrast)
        self.handles.addWidget(self.input_contrast)
        self.handles.addStretch()

        self.handles2.addWidget(label_blur)
        self.handles2.addWidget(self.input_blur)
        self.handles2.addWidget(label_tweak)
        self.handles2.addWidget(self.input_tweak)
        self.handles2.addStretch()

        self.layout.addLayout(self.handles, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

        self.layout.addLayout(self.handles2, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

    def getParameters(self):
        # get the original image
        rot_angle = float(round(self.input_rot.value(), 1))
        init_blur = int(self.input_blur.value())
        contrast = float(round(self.input_contrast.value(), 1))
        brightness = float(self.input_brightness.value())
        init_param2 = int(self.input_tweak.value())

        log.info(
            f"cropping with rot_angle {rot_angle}, "
            f"init_blur {init_blur}, "
            f"contrast {contrast}, "
            f"brightness {brightness}, "
            f"init_param2 {init_param2}"
        )

        return {
            "rot_angle": rot_angle,
            "init_blur": init_blur,
            "contrast": contrast,
            "brightness": brightness,
            "init_param2": init_param2,
        }

    def trim_image(self, params):
        rot_angle = params["rot_angle"]
        init_blur = params["init_blur"]
        contrast = params["contrast"]
        brightness = params["brightness"]
        init_param2 = params["init_param2"]

        # Image1: Copy from original
        image_1 = self.parent.img_bgr.copy()
        cv2.imwrite(self.tmp_preview_path.replace("preview", "image_1"), image_1)

        img_without_brightness = image_1

        # Image2: Rotated
        if rot_angle != 0:
            image_center = tuple(np.array(image_1.shape[1::-1]) / 2)
            rot_mat = cv2.getRotationMatrix2D(image_center, rot_angle, 1.0)

            image_2 = cv2.warpAffine(
                image_1, rot_mat, image_1.shape[1::-1], flags=cv2.INTER_LANCZOS4
            )
            cv2.imwrite(self.tmp_preview_path.replace("preview", "image_2"), image_2)
            img_without_brightness = image_2

        # Image3: Brightness and contrast adjustment
        image_3 = cv2.convertScaleAbs(
            img_without_brightness, alpha=contrast, beta=brightness
        )
        cv2.imwrite(self.tmp_preview_path.replace("preview", "image_3"), image_3)

        height_org, width_org, _channel = image_3.shape

        # Image4: Scaled for Cropping window
        resize_scale = (
            resize_length / width_org
            if width_org >= height_org
            else resize_length / height_org
        )

        # Create "Negative" picture for pickup point search
        image_4 = cv2.resize(
            image_3, None, None, resize_scale, resize_scale, cv2.INTER_LANCZOS4
        )
        cv2.imwrite(self.tmp_preview_path.replace("preview", "image_4"), image_4)

        height, width, _channel = image_4.shape

        gray = cv2.cvtColor(image_4, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(self.tmp_preview_path, gray)

        image_inverted = 255 - gray

        cv2.imwrite(
            self.tmp_preview_path.replace("preview", "preview_gray_inverted"),
            image_inverted,
        )

        log.info("Searching pickup points...")

        gauge_dic = None
        pickup_points = None

        for blurSize in range(init_blur, 3, -1):
            try:
                gauge_dic, pickup_points = self.houghScan(
                    image_inverted, blurSize, init_param2
                )
                break
            except Exception as e:
                log.info(str(e))
                continue

        if not gauge_dic:
            msg = "failed to find any pickup points"
            raise Exception(msg)

        gauge_std = sum(g["length"] for g in gauge_dic) / len(gauge_dic)
        center_x = int(sum(p[0] for p in pickup_points) / len(pickup_points))
        center_y = int(sum(p[1] for p in pickup_points) / len(pickup_points))

        pitch = gauge_std / 20.0  # pixels / mm

        log.info(
            f"gauge_std = {gauge_std:.3f} px: 1mm = {pitch:.3f} px, center = ( {center_x:6.3f}, {center_y:6.3f} )"
        )

        # Picture cropping
        cropPitch = self.cropRange * pitch
        x_remaining_left = center_x - cropPitch
        x_remaining_right = width - (center_x + cropPitch)
        if x_remaining_left > x_remaining_right:
            # module shifted on the picture right side
            x_shift = width - center_x if x_remaining_right <= 0 else cropPitch

        else:
            x_shift = center_x if x_remaining_left <= 0 else cropPitch

        y_remaining_top = center_y - cropPitch
        y_remaining_bottom = height - (center_y + cropPitch)
        if y_remaining_top > y_remaining_bottom:
            # module shifted on the picture bottom side
            y_shift = height - center_y if y_remaining_bottom <= 0 else cropPitch

        else:
            y_shift = center_y if y_remaining_top <= 0 else cropPitch

        x_edge1_0 = int(center_x - x_shift)
        y_edge1_0 = int(center_y - y_shift)
        x_edge2_0 = int(center_x + x_shift)
        y_edge2_0 = int(center_y + y_shift)

        x_edge1 = int(x_edge1_0 / resize_scale)
        y_edge1 = int(y_edge1_0 / resize_scale)
        x_edge2 = int(x_edge2_0 / resize_scale)
        y_edge2 = int(y_edge2_0 / resize_scale)

        crop_info = [[x_edge1, x_edge2], [y_edge1, y_edge2]]
        log.info(f"crop_info = {crop_info}")

        cropped = img_without_brightness[y_edge1:y_edge2, x_edge1:x_edge2].copy()

        cv2.imwrite(self.tmp_cropped_path, cropped)

        # Draw the autotrim line
        marker_width = int(0.005 * width)

        color = (0, 255, 128)  # Green
        color2 = (255, 0, 128)  # Purple

        # Draw the center reticle
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        cv2.line(
            gray_bgr,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            color,
            marker_width,
        )

        # Draw the outer corners
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0 + 50, y_edge1_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0, y_edge1_0 + 50),
            color2,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0 - 50, y_edge1_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0, y_edge1_0 + 50),
            color2,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0 + 50, y_edge2_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0, y_edge2_0 - 50),
            color2,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0 - 50, y_edge2_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0, y_edge2_0 - 50),
            color2,
            marker_width,
        )

        # Draw pickup point circles
        for p in pickup_points:
            cv2.circle(
                gray_bgr,
                (int(p[0]), int(p[1])),
                int(p[2]),
                color,
                int(marker_width * 0.5),
            )

        cv2.imwrite(self.tmp_preview_path, gray_bgr)

        return crop_info

    def trim_image_manual(self, manual_points):
        params = self.getParameters()

        rot_angle = params["rot_angle"]
        # init_blur = params["init_blur"]
        contrast = params["contrast"]
        brightness = params["brightness"]
        # init_param2 = params["init_param2"]

        image_1 = self.parent.img_bgr.copy()

        image_center = tuple(np.array(image_1.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, rot_angle, 1.0)
        image_2 = cv2.warpAffine(
            image_1, rot_mat, image_1.shape[1::-1], flags=cv2.INTER_LANCZOS4
        )

        image_3 = cv2.convertScaleAbs(image_2, alpha=contrast, beta=brightness)

        height_org, width_org, _channel = image_3.shape

        resize_scale = (
            resize_length / width_org
            if width_org >= height_org
            else resize_length / height_org
        )

        image_4 = cv2.resize(
            image_3, None, None, resize_scale, resize_scale, cv2.INTER_LANCZOS4
        )

        height, width, _channel = image_4.shape

        for i in range(height):
            for j in range(width):
                image_3[(i, j, 1)] = 0

        gray = cv2.cvtColor(image_4, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(self.tmp_preview_path, gray)

        image_inverted = 255 - gray

        cv2.imwrite(
            self.tmp_preview_path.replace("preview", "preview_gray_inverted"),
            image_inverted,
        )

        log.info("Searching pickup points...")

        center_x = int(
            sum([manual_points.get("GA1").get("x"), manual_points.get("GA3").get("x")])
        )
        center_y = int(
            sum([manual_points.get("GA1").get("y"), manual_points.get("GA3").get("y")])
        )

        gauge_std = sum(
            [
                abs(
                    manual_points.get("GA1").get("x")
                    - manual_points.get("GA3").get("x")
                ),
                abs(
                    manual_points.get("GA1").get("y")
                    - manual_points.get("GA3").get("y")
                ),
            ]
        )

        pitch = gauge_std / 20.0  # pixels / mm

        log.info(
            f"gauge_std = {gauge_std:.3f} px: 1mm = {pitch:.3f} px, center = ( {center_x:6.3f}, {center_y:6.3f} )"
        )

        x_edge1_0 = max(int(center_x - self.cropRange * pitch), 0)
        y_edge1_0 = max(int(center_y - self.cropRange * pitch), 0)
        x_edge2_0 = min(int(center_x + self.cropRange * pitch), width - 1)
        y_edge2_0 = min(int(center_y + self.cropRange * pitch), height - 1)

        x_edge1 = max(int((center_x - self.cropRange * pitch) / resize_scale), 0)
        y_edge1 = max(int((center_y - self.cropRange * pitch) / resize_scale), 0)
        x_edge2 = min(
            int((center_x + self.cropRange * pitch) / resize_scale), width_org - 1
        )
        y_edge2 = min(
            int((center_y + self.cropRange * pitch) / resize_scale), height_org - 1
        )

        crop_info = [[x_edge1, x_edge2], [y_edge1, y_edge2]]
        log.info(f"crop_info = {crop_info}")

        cropped = image_2[y_edge1:y_edge2, x_edge1:x_edge2].copy()

        cv2.imwrite(self.tmp_cropped_path, cropped)

        marker_width = int(0.005 * width)

        color = (0, 255, 128)  # Green
        color2 = (255, 0, 128)  # Purple

        # Draw the center reticle
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        cv2.line(
            gray_bgr,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            color,
            marker_width,
        )

        # Draw corner lines
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0 + 50, y_edge1_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0, y_edge1_0 + 50),
            color2,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0 - 50, y_edge1_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0, y_edge1_0 + 50),
            color2,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0 + 50, y_edge2_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0, y_edge2_0 - 50),
            color2,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0 - 50, y_edge2_0),
            color2,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0, y_edge2_0 - 50),
            color2,
            marker_width,
        )

        # Draw the clicked points
        cv2.circle(
            gray_bgr,
            (
                int(manual_points.get("GA1").get("x")) * 2,
                int(manual_points.get("GA1").get("y")) * 2,
            ),
            10,
            color,
            int(marker_width * 0.5),
        )

        cv2.circle(
            gray_bgr,
            (
                int(manual_points.get("GA3").get("x")) * 2,
                int(manual_points.get("GA3").get("y")) * 2,
            ),
            10,
            color,
            int(marker_width * 0.5),
        )

        cv2.imwrite(self.tmp_preview_path, gray_bgr)

        preview = cv2.imread(self.tmp_preview_path)

        self.cropped = cv2.imread(self.tmp_cropped_path)

        h, w, d = preview.shape

        scale = min(preview_size / float(h), preview_size / float(w))

        resize_img = cv2.resize(
            preview, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4
        )

        img_rgb, h_rgb, w_rgb, d_rgb = img_cvt_rgb(resize_img)
        bytesPerLine = d_rgb * w_rgb

        self.image = QImage(
            img_rgb.data, w_rgb, h_rgb, bytesPerLine, QImage.Format_RGB888
        )

        self.view.items().clear()
        self.scene.clear()

        pixmap = QPixmap.fromImage(self.image)
        self.item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.item)
        self.view.setScene(self.scene)

        return crop_info

    def houghScan(self, image_inverted, blurSize, param2):
        log.info(f"  Hough search: blurSize = {blurSize}")

        blur = cv2.blur(image_inverted, (blurSize, blurSize))
        cv2.imwrite(
            self.tmp_preview_path.replace("preview", f"preview_blur_{blurSize}"), blur
        )

        height, width = image_inverted.shape

        iter_num = 0

        while True:
            log.info(f"  Hough search: blurSize = {blurSize}, param2 = {param2}")
            _ret, image_4 = cv2.threshold(
                blur, thresh=120, maxval=255, type=cv2.THRESH_TOZERO
            )

            # detect circle
            circles = cv2.HoughCircles(
                image=image_4,
                method=cv2.HOUGH_GRADIENT,
                dp=1.0,
                minDist=min(width, height) * 0.12,
                param1=200,
                param2=param2,
                minRadius=int(min(width, height) * 0.03),
                maxRadius=int(min(width, height) * 0.10),
            )

            pickup_cands = []

            for i in circles[0, :]:
                # check if center is in middle of picture
                if (
                    i[0] < width * 0.05
                    or i[0] > width * 0.95
                    or i[1] < height * 0.05
                    or i[1] > height * 0.95
                ):
                    continue

                # draw the outer circle
                cv2.circle(image_4, (int(i[0]), int(i[1])), int(i[2]), (0, 0, 0), 2)

                # draw the center of the circle
                cv2.circle(image_4, (int(i[0]), int(i[1])), 2, (0, 0, 0), 3)

                pickup_cands += [i]

            gauge_dic = []
            pickup_points = set()

            for i, ci in enumerate(pickup_cands):
                for j in range(i + 1, len(pickup_cands)):
                    cj = pickup_cands[j]

                    dx = abs(cj[0] - ci[0])
                    dy = abs(cj[1] - ci[1])

                    ang = math.atan(dy / (dx + 1.0e-7))
                    deg = math.atan(1) / 45.0
                    length = math.hypot(dx, dy)

                    isHorizontal = ang < 2 * deg
                    isVertical = ang > 88 * deg

                    if not (isHorizontal or isVertical):
                        # log.info( f'{length:.2f} px, {ang/deg:6.3f} deg ==> skipped' )
                        continue

                    cv2.line(
                        image_4,
                        (int(ci[0]), int(ci[1])),
                        (int(cj[0]), int(cj[1])),
                        (0, 0, 0),
                        1,
                    )
                    gauge_dic += [
                        {
                            "horizontal": isHorizontal,
                            "vertical": isVertical,
                            "length": length,
                            "angle": ang / deg,
                        }
                    ]

                    for p in [ci, cj]:
                        pickup_points.add((p[0], p[1], p[2]))

            if len(pickup_points) < 4:
                param2 -= 1

            elif len(pickup_points) > 4:
                param2 += 1

            else:
                break

            iter_num += 1

            if iter_num > 50:
                msg = "failure in detection: too long iterations"
                log.info(msg)
                raise Exception(msg)

            if param2 > 80:
                msg = "failure in detection: scanned all param2 range"
                log.info(msg)
                raise Exception(msg)

        if len(gauge_dic) != 4:
            msg = "failure in detection: did not find good gauges"
            log.info(msg)
            raise Exception(msg)

        log.info("")
        log.info("------------------")
        log.info("Detected pickup points:")
        for p in pickup_points:
            log.info(
                f"    Pickup point: center: ({p[0]:.2f}, {p[1]:.2f}), radius: {p[2]:.2f}"
            )

        log.info("Detected pickup points gauges:")
        for g in gauge_dic:
            log.info(
                f'    {"Horizontal" if g["horizontal"] else "Vertical":12s}: length = {g["length"]:7.2f} pixels, angle = {g["angle"]:6.3f} deg'
            )

        return gauge_dic, pickup_points


#################################################################################################


class QuadBackTrimmer(Trimmer):
    def setupCustom(self, custom_params):
        self.cropRange = custom_params.get("CropRange", 21.8)
        log.info(
            f"QuadBackTrimmer.setupCustom(): Custom Crop Range = {self.cropRange} mm"
        )

        self.handles = QHBoxLayout()
        self.handles2 = QHBoxLayout()

        label_rot = QLabel(self)
        label_rot.setText("Rotation: [-3.00, 3.00]")

        label_brightness = QLabel(self)
        label_brightness.setText("Brightness: [-100, 100]")

        label_contrast = QLabel(self)
        label_contrast.setText("Contrast: [0, 4]")

        label_blur = QLabel(self)
        label_blur.setText("Blur: [1, 5]")

        label_cannyThr1 = QLabel(self)
        label_cannyThr1.setText("Thr1: [0, 255]")

        label_cannyThr2 = QLabel(self)
        label_cannyThr2.setText("Thr2: [0, 255]")

        self.input_rot = QDoubleSpinBox()
        self.input_rot.setMinimum(-3)
        self.input_rot.setMaximum(3)
        self.input_rot.setSingleStep(0.1)
        self.input_rot.setFixedWidth(50)

        self.input_brightness = QSpinBox()
        self.input_brightness.setMinimum(-100)
        self.input_brightness.setMaximum(100)
        self.input_brightness.setSingleStep(10)
        self.input_brightness.setFixedWidth(50)
        self.input_brightness.setValue(custom_params.get("Brightness", 50))

        self.input_contrast = QDoubleSpinBox()
        self.input_contrast.setMinimum(0.0)
        self.input_contrast.setMaximum(4.0)
        self.input_contrast.setSingleStep(0.1)
        self.input_contrast.setFixedWidth(50)
        self.input_contrast.setValue(custom_params.get("Contrast", 3))

        self.input_blur = QSpinBox()
        self.input_blur.setMinimum(1)
        self.input_blur.setMaximum(5)
        self.input_blur.setSingleStep(1)
        self.input_blur.setFixedWidth(40)
        self.input_blur.setValue(custom_params.get("InitialBlur", 5))

        self.input_cannyThr1 = QSpinBox()
        self.input_cannyThr1.setMinimum(0)
        self.input_cannyThr1.setMaximum(255)
        self.input_cannyThr1.setSingleStep(5)
        self.input_cannyThr1.setFixedWidth(40)
        self.input_cannyThr1.setValue(custom_params.get("CannyThr1", 100))

        self.input_cannyThr2 = QSpinBox()
        self.input_cannyThr2.setMinimum(0)
        self.input_cannyThr2.setMaximum(255)
        self.input_cannyThr2.setSingleStep(5)
        self.input_cannyThr2.setFixedWidth(40)
        self.input_cannyThr2.setValue(custom_params.get("CannyThr2", 20))

        self.handles.addWidget(label_rot)
        self.handles.addWidget(self.input_rot)
        self.handles.addWidget(label_brightness)
        self.handles.addWidget(self.input_brightness)
        self.handles.addWidget(label_contrast)
        self.handles.addWidget(self.input_contrast)

        self.handles2.addWidget(label_blur)
        self.handles2.addWidget(self.input_blur)
        self.handles2.addWidget(label_cannyThr1)
        self.handles2.addWidget(self.input_cannyThr1)
        self.handles2.addWidget(label_cannyThr2)
        self.handles2.addWidget(self.input_cannyThr2)

        self.layout.addLayout(self.handles, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

        msg = QLineEdit(self)
        msg.setFixedWidth(preview_size + 50)
        msg.setReadOnly(True)
        msg.setText(
            "If auto-detection fails, you can manually specify "
            "the cropping region by clicking two diagonal corners of the FEs"
        )
        self.layout.addWidget(msg, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

        self.layout.addLayout(self.handles2, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

        self.handles.addStretch()
        self.handles2.addStretch()

    def getParameters(self):
        # get the original image
        rot_angle = float(round(self.input_rot.value(), 1))
        init_blur = int(self.input_blur.value())
        contrast = float(round(self.input_contrast.value(), 1))
        brightness = float(round(self.input_brightness.value(), 1))
        cannyThr1 = int(self.input_cannyThr1.value())
        cannyThr2 = int(self.input_cannyThr2.value())

        log.info(
            f"cropping with rot_angle {rot_angle}, "
            f"init_blur {init_blur}, "
            f"contrast {contrast}, "
            f"brightness {brightness}, "
            f"cannyThr [{cannyThr1}, {cannyThr2}]"
        )

        return {
            "rot_angle": rot_angle,
            "init_blur": init_blur,
            "contrast": contrast,
            "brightness": brightness,
            "cannyThr1": cannyThr1,
            "cannyThr2": cannyThr2,
        }

    def trim_image_pre(self, params):
        rot_angle = params["rot_angle"]
        contrast = params["contrast"]
        brightness = params["brightness"]

        image_1 = self.parent.img_bgr.copy()

        image_center = tuple(np.array(image_1.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, rot_angle, 1.0)
        image_2 = cv2.warpAffine(
            image_1, rot_mat, image_1.shape[1::-1], flags=cv2.INTER_LANCZOS4
        )

        image_3 = cv2.convertScaleAbs(image_2, alpha=contrast, beta=brightness)

        height_org, width_org, _channel = image_3.shape
        log.info(f"original image: width {width_org}, height {height_org}")

        resize_scale = (
            resize_length / width_org
            if width_org >= height_org
            else resize_length / height_org
        )
        log.info(f"resize_scale = {resize_scale}")

        image_4 = cv2.resize(
            image_3, None, None, resize_scale, resize_scale, cv2.INTER_LANCZOS4
        )

        height, width, _channel = image_4.shape

        for i in range(height):
            for j in range(width):
                image_4.itemset((i, j, 1), 0)

        gray = cv2.cvtColor(image_4, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(self.tmp_preview_path, gray)

        return image_2, gray, width_org, height_org, width, height

    def trim_image(self, params):
        original, gray, width_org, height_org, width, height = self.trim_image_pre(
            params
        )

        init_blur = params["init_blur"]

        blur = cv2.blur(gray, (init_blur, init_blur))

        cannyThr1 = params["cannyThr1"]
        cannyThr2 = params["cannyThr2"]

        edges = cv2.Canny(blur, cannyThr2, cannyThr1)

        rho = 1  # distance resolution in pixels of the Hough grid
        theta = (
            4.0 * math.atan(1.0) / 30.0
        )  # angular resolution in radians of the Hough grid
        threshold = 200  # minimum number of votes (intersections in Hough grid cell)
        min_line_length = 200  # minimum number of pixels making up a line
        max_line_gap = 1200  # maximum gap in pixels between connectable line segments

        lines = []

        # Run Hough on edge detected image
        # Output "lines" is an array containing endpoints of detected line segments
        lines = cv2.HoughLinesP(
            edges, rho, theta, threshold, np.array([]), min_line_length, max_line_gap
        )

        if len(lines) == 0:
            msg = "No edge lines were detected"
            raise Exception(msg)

        xEdges = []
        yEdges = []

        for line in lines:
            x1 = line[0][0]
            y1 = line[0][1]
            x2 = line[0][2]
            y2 = line[0][3]
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            deg = math.atan(1) / 45.0
            ang = math.atan(dy / (dx + 1.0e-7))
            isHorizontal = ang < 2 * deg
            isVertical = ang > 88 * deg

            if not (isHorizontal or isVertical):
                continue

            if isVertical:
                xEdges += [x1]
            if isHorizontal:
                yEdges += [y1]

        xEdges.sort()
        yEdges.sort()

        if len(xEdges) == 0:
            msg = "No horizontal edge lines were detected"
            raise Exception(msg)

        if len(yEdges) == 0:
            msg = "No horizontal edge lines were detected"
            raise Exception(msg)

        crop_info = self.trim_image_post(
            gray, width, height, width_org, height_org, lines, xEdges, yEdges
        )

        # crop np.ndarray -- y first, x second!
        cropped = original[
            crop_info[1][0] : crop_info[1][1], crop_info[0][0] : crop_info[0][1]
        ].copy()

        cv2.imwrite(self.tmp_cropped_path, cropped)

        return crop_info

    def trim_image_manual(self, manual_points):
        params = self.getParameters()

        # rot_angle = params["rot_angle"]
        # init_blur = params["init_blur"]
        contrast = params["contrast"]
        # brightness = params["brightness"]
        # init_param2 = params["init_param2"]

        image_1 = self.parent.img_bgr.copy()

        image_center = tuple(np.array(image_1.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, 0.0, 1.0)
        image_2 = cv2.warpAffine(
            image_1, rot_mat, image_1.shape[1::-1], flags=cv2.INTER_LANCZOS4
        )

        # image_3 = cv2.convertScaleAbs(image_2, alpha=contrast, beta=brightness)
        image_3 = cv2.convertScaleAbs(image_2, alpha=contrast, beta=0)

        height_org, width_org, _channel = image_3.shape

        resize_scale = (
            resize_length / width_org
            if width_org >= height_org
            else resize_length / height_org
        )

        image_4 = cv2.resize(
            image_3, None, None, resize_scale, resize_scale, cv2.INTER_LANCZOS4
        )

        height, width, _channel = image_4.shape

        for i in range(height):
            for j in range(width):
                image_3.itemset((i, j, 1), 0)

        gray = cv2.cvtColor(image_4, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(self.tmp_preview_path, gray)

        image_inverted = 255 - gray

        cv2.imwrite(
            self.tmp_preview_path.replace("preview", "preview_gray_inverted"),
            image_inverted,
        )

        log.info("Searching pickup points...")

        center_x = int(
            sum([manual_points.get("GA1").get("x"), manual_points.get("GA3").get("x")])
        )
        center_y = int(
            sum([manual_points.get("GA1").get("y"), manual_points.get("GA3").get("y")])
        )

        gauge_std = sum(
            [
                abs(
                    manual_points.get("GA1").get("x")
                    - manual_points.get("GA3").get("x")
                ),
                abs(
                    manual_points.get("GA1").get("y")
                    - manual_points.get("GA3").get("y")
                ),
            ]
        )

        pitch = gauge_std / 41.236  # pixels / mm

        log.info(
            f"gauge_std = {gauge_std:.3f} px: 1mm = {pitch:.3f} px, "
            f"center = ( {center_x:6.3f}, {center_y:6.3f} )"
        )

        x_edge1_0 = max(int(center_x - self.cropRange * pitch), 0)
        y_edge1_0 = max(int(center_y - self.cropRange * pitch), 0)
        x_edge2_0 = min(int(center_x + self.cropRange * pitch), width - 1)
        y_edge2_0 = min(int(center_y + self.cropRange * pitch), height - 1)

        x_edge1 = max(int((center_x - self.cropRange * pitch) / resize_scale), 0)
        y_edge1 = max(int((center_y - self.cropRange * pitch) / resize_scale), 0)
        x_edge2 = min(
            int((center_x + self.cropRange * pitch) / resize_scale), width_org - 1
        )
        y_edge2 = min(
            int((center_y + self.cropRange * pitch) / resize_scale), height_org - 1
        )

        crop_info = [[x_edge1, x_edge2], [y_edge1, y_edge2]]
        log.info(f"crop_info = {crop_info}")

        cropped = image_2[y_edge1:y_edge2, x_edge1:x_edge2].copy()

        cv2.imwrite(self.tmp_cropped_path, cropped)

        marker_width = int(0.005 * width)

        color = (0, 255, 128)

        # Draw the center reticle
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        cv2.line(
            gray_bgr,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0 + 50, y_edge1_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0, y_edge1_0 + 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0 - 50, y_edge1_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0, y_edge1_0 + 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0 + 50, y_edge2_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0, y_edge2_0 - 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0 - 50, y_edge2_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0, y_edge2_0 - 50),
            color,
            marker_width,
        )

        cv2.circle(
            gray_bgr,
            (
                int(manual_points.get("GA1").get("x")) * 2,
                int(manual_points.get("GA1").get("y")) * 2,
            ),
            10,
            color,
            int(marker_width * 0.5),
        )

        cv2.circle(
            gray_bgr,
            (
                int(manual_points.get("GA3").get("x")) * 2,
                int(manual_points.get("GA3").get("y")) * 2,
            ),
            10,
            color,
            int(marker_width * 0.5),
        )

        cv2.imwrite(self.tmp_preview_path, gray_bgr)

        preview = cv2.imread(self.tmp_preview_path)

        self.cropped = cv2.imread(self.tmp_cropped_path)

        h, w, d = preview.shape

        scale = min(preview_size / float(h), preview_size / float(w))

        resize_img = cv2.resize(
            preview, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4
        )

        img_rgb, h_rgb, w_rgb, d_rgb = img_cvt_rgb(resize_img)
        bytesPerLine = d_rgb * w_rgb

        self.image = QImage(
            img_rgb.data, w_rgb, h_rgb, bytesPerLine, QImage.Format_RGB888
        )

        self.view.items().clear()
        self.scene.clear()

        pixmap = QPixmap.fromImage(self.image)
        self.item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.item)
        self.view.setScene(self.scene)

        return crop_info

    def trim_image_post(
        self,
        image,
        width,
        height,
        width_org,
        height_org,
        lines,
        xEdges,
        yEdges,
        std1=42.2,
        std2=41.4,
    ):
        center_x = int((xEdges[0] + xEdges[-1]) / 2.0)
        center_y = int((yEdges[0] + yEdges[-1]) / 2.0)

        horLength = abs(xEdges[0] - xEdges[-1])
        verLength = abs(yEdges[0] - yEdges[-1])
        pitch = (horLength / std1 + verLength / std2) / 2.0  # pixels / mm

        marker_width0 = int(0.005 * width)

        x_edge1_0 = max(int(center_x - self.cropRange * pitch), 0)
        y_edge1_0 = max(int(center_y - self.cropRange * pitch), 0)
        x_edge2_0 = min(int(center_x + self.cropRange * pitch), width - 1)
        y_edge2_0 = min(int(center_y + self.cropRange * pitch), height - 1)

        # Draw the center reticle
        gray_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        color = (0, 255, 128)

        cv2.line(
            gray_bgr,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0 + 50, y_edge1_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0, y_edge1_0 + 50),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0 - 50, y_edge1_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0, y_edge1_0 + 50),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0 + 50, y_edge2_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0, y_edge2_0 - 50),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0 - 50, y_edge2_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0, y_edge2_0 - 50),
            color,
            marker_width0,
        )

        for line in lines:
            x1 = line[0][0]
            y1 = line[0][1]
            x2 = line[0][2]
            y2 = line[0][3]

            cv2.line(
                gray_bgr,
                (x1, y1),
                (x2, y2),
                (255, 200, 200),
                2,
            )

        cv2.imwrite(self.tmp_preview_path, gray_bgr)

        x_edge1 = max(int((center_x - self.cropRange * pitch) / width * width_org), 0)
        y_edge1 = max(int((center_y - self.cropRange * pitch) / height * height_org), 0)
        x_edge2 = min(
            int((center_x + self.cropRange * pitch) / width * width_org), width_org - 1
        )
        y_edge2 = min(
            int((center_y + self.cropRange * pitch) / height * height_org),
            height_org - 1,
        )

        crop_info = [[x_edge1, x_edge2], [y_edge1, y_edge2]]
        log.info(f"crop_info = {crop_info}")

        return crop_info


class BareFrontTrimmer(Trimmer):
    def setupCustom(self, custom_params):
        self.cropRange = custom_params.get("CropRange", 21.8)
        log.info(
            f"QuadBackTrimmer.setupCustom(): Custom Crop Range = {self.cropRange} mm"
        )

        self.handles = QHBoxLayout()
        self.handles2 = QHBoxLayout()

        label_rot = QLabel(self)
        label_rot.setText("Rotation: [-3.00, 3.00]")

        label_brightness = QLabel(self)
        label_brightness.setText("Brightness: [-100, 100]")

        label_contrast = QLabel(self)
        label_contrast.setText("Contrast: [0, 4]")

        label_houghThr = QLabel(self)
        label_houghThr.setText("Line Thr: [0, 300]")

        label_cannyThr1 = QLabel(self)
        label_cannyThr1.setText("Thr1: [0, 255]")

        label_cannyThr2 = QLabel(self)
        label_cannyThr2.setText("Thr2: [0, 255]")

        self.input_rot = QLineEdit(self)
        self.input_rot.setFixedWidth(40)
        self.input_rot.setValidator(QDoubleValidator(-3.0, 3.0, 2))
        self.input_rot.setText(str(0.00))

        self.input_brightness = QLineEdit(self)
        self.input_brightness.setFixedWidth(40)
        self.input_brightness.setValidator(QDoubleValidator(-100, 100, 0))
        self.input_brightness.setText(str(custom_params.get("Brightness", 50)))

        self.input_contrast = QLineEdit(self)
        self.input_contrast.setFixedWidth(40)
        self.input_contrast.setValidator(QDoubleValidator(0.0, 4.0, 1))
        self.input_contrast.setText(str(custom_params.get("Contrast", 3.0)))

        self.input_houghThr = QLineEdit(self)
        self.input_houghThr.setFixedWidth(40)
        self.input_houghThr.setValidator(QDoubleValidator(1, 300, 0))
        self.input_houghThr.setText(str(custom_params.get("HouhThr", 90)))

        self.input_cannyThr1 = QLineEdit(self)
        self.input_cannyThr1.setFixedWidth(40)
        self.input_cannyThr1.setValidator(QDoubleValidator(0, 255, 0))
        self.input_cannyThr1.setText(str(custom_params.get("CannyThr1", 105)))

        self.input_cannyThr2 = QLineEdit(self)
        self.input_cannyThr2.setFixedWidth(40)
        self.input_cannyThr2.setValidator(QDoubleValidator(0, 255, 0))
        self.input_cannyThr2.setText(str(custom_params.get("CannyThr2", 30)))

        self.handles.addWidget(label_rot)
        self.handles.addWidget(self.input_rot)
        self.handles.addWidget(label_brightness)
        self.handles.addWidget(self.input_brightness)
        self.handles.addWidget(label_contrast)
        self.handles.addWidget(self.input_contrast)

        self.handles2.addWidget(label_houghThr)
        self.handles2.addWidget(self.input_houghThr)
        self.handles2.addWidget(label_cannyThr1)
        self.handles2.addWidget(self.input_cannyThr1)
        self.handles2.addWidget(label_cannyThr2)
        self.handles2.addWidget(self.input_cannyThr2)

        self.layout.addLayout(self.handles, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

        msg = QLineEdit(self)
        msg.setFixedWidth(700)
        msg.setReadOnly(True)
        msg.setText(
            "If auto-detection fails, you can manually specify the cropping region by clicking two diagonal corners of the FEs"
        )
        self.layout.addWidget(msg, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

        self.layout.addLayout(self.handles2, self.nLayoutRows, 0)
        self.nLayoutRows = self.nLayoutRows + 1

        self.handles.addStretch()
        self.handles2.addStretch()

    def getParameters(self):
        # get the original image
        rot_angle = float(self.input_rot.text())
        HouhThr = int(self.input_houghThr.text())
        contrast = float(self.input_contrast.text())
        brightness = float(self.input_brightness.text())
        cannyThr1 = int(self.input_cannyThr1.text())
        cannyThr2 = int(self.input_cannyThr2.text())

        log.info(
            f"cropping with rot_angle {rot_angle}, HouhThr {HouhThr}, contrast {contrast}, brightness {brightness}, cannyThr [{cannyThr1}, {cannyThr2}]"
        )

        return {
            "rot_angle": rot_angle,
            "HouhThr": HouhThr,
            "contrast": contrast,
            "brightness": brightness,
            "cannyThr1": cannyThr1,
            "cannyThr2": cannyThr2,
        }

    def trim_image_pre(self, params):
        rot_angle = params["rot_angle"]
        # contrast = params["contrast"]
        # brightness = params["brightness"]

        image_1 = self.parent.img_bgr.copy()

        # Apply initial rotation
        image_center = tuple(np.array(image_1.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, rot_angle, 1.0)
        image_2 = cv2.warpAffine(
            image_1, rot_mat, image_1.shape[1::-1], flags=cv2.INTER_LINEAR
        )

        # Resize image
        height_org, width_org, _channel = image_2.shape
        log.info(f"original image: width {width_org}, height {height_org}")

        resize_scale = (
            1200 / width_org if width_org >= height_org else 1200 / height_org
        )
        log.info(f"resize_scale = {resize_scale}")

        image_3 = cv2.resize(
            image_2, None, None, resize_scale, resize_scale, cv2.INTER_LINEAR
        )

        # Sharpen filter
        kern = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        image_3 = cv2.filter2D(image_3, -1, kern)

        # Reduce red intensity
        rval = 60
        image_3[:, :, 2][image_3[:, :, 2] > rval] = (
            image_3[:, :, 2][image_3[:, :, 2] > rval] - rval
        )
        image_3[:, :, 2][image_3[:, :, 2] <= rval] = 0
        # Reduce green intensity
        gval = 30
        image_3[:, :, 1][image_3[:, :, 1] > gval] = (
            image_3[:, :, 1][image_3[:, :, 1] > gval] - gval
        )
        image_3[:, :, 1][image_3[:, :, 1] <= gval] = 0
        # Increase blue intensity
        bval = 5
        image_3[:, :, 0][image_3[:, :, 0] < 255 - bval] = (
            image_3[:, :, 0][image_3[:, :, 0] < 255 - bval] + bval
        )
        image_3[:, :, 0][image_3[:, :, 0] >= 255 - bval] = 255

        # Blur filters, brightness/contrast transform and gray scale
        image_3 = cv2.convertScaleAbs(image_3, alpha=0.7, beta=2.5)
        gray = cv2.blur(cv2.cvtColor(image_3, cv2.COLOR_BGR2GRAY), (5, 5))
        gray = cv2.filter2D(gray, -1, kern)
        gray = cv2.blur(gray, (7, 7))
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=1.3)

        height, width = gray.shape

        cv2.imwrite(self.tmp_preview_path, gray)

        return image_2, gray, width_org, height_org, width, height

    def trim_image(self, params):
        original, gray, width_org, height_org, width, height = self.trim_image_pre(
            params
        )

        # Contour extraction with canny
        cannyThr1 = params["cannyThr1"]
        cannyThr2 = params["cannyThr2"]
        edges = cv2.Canny(gray, cannyThr2, cannyThr1)

        # Line extraction with Hough scan
        HouhThr = params["HouhThr"]
        rho = 1  # distance resolution in pixels of the Hough grid
        theta = (
            4.0 * math.atan(1.0) / 30.0
        )  # angular resolution in radians of the Hough grid
        threshold = (
            HouhThr  # minimum number of votes (intersections in Hough grid cell)
        )
        min_line_length = 100  # minimum number of pixels making up a line
        max_line_gap = 500  # maximum gap in pixels between connectable line segments

        lines = []

        # Run Hough on edge detected image
        # Output "lines" is an array containing endpoints of detected line segments
        lines = cv2.HoughLinesP(
            edges,
            rho=rho,
            theta=theta,
            threshold=threshold,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap,
        )

        if len(lines) == 0:
            msg = "No edge lines were detected"
            raise Exception(msg)

        # Extract component edge candidates from line list
        xEdges = []
        yEdges = []

        for line in lines:
            x1 = line[0][0]
            y1 = line[0][1]
            x2 = line[0][2]
            y2 = line[0][3]
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            isHorizontal = dx < 2
            isVertical = dy < 2
            if isHorizontal:
                yEdges.append(x1)
            elif isVertical:
                xEdges.append(y1)

        xEdges.sort()
        yEdges.sort()

        if len(xEdges) == 0:
            msg = "No horizontal edge lines were detected"
            raise Exception(msg)

        if len(yEdges) == 0:
            msg = "No horizontal edge lines were detected"
            raise Exception(msg)

        # Select true component edges based on candidates list
        xEdges = np.array(xEdges)
        yEdges = np.array(yEdges)
        xmid = gray.shape[1] // 2
        ymid = gray.shape[0] // 2

        if xEdges[xEdges < xmid].size == 0:
            msg = "No left edge lines were detected"
            raise Exception(msg)
        xmin = xEdges[xEdges < xmid][-1]
        log.info(f"Left edge found at {xmin}")

        if xEdges[xEdges > xmid].size == 0:
            msg = "No right edge lines were detected"
            raise Exception(msg)
        xmax = xEdges[xEdges > xmid][0]
        log.info(f"Right edge found at {xmax}")

        if yEdges[yEdges < ymid].size == 0:
            msg = "No top edge lines were detected"
            raise Exception(msg)
        ymin = yEdges[yEdges < ymid][-1]
        log.info(f"Top edge found at {ymin}")

        if yEdges[yEdges > ymid].size == 0:
            msg = "No bottom edge lines were detected"
            raise Exception(msg)
        ymax = yEdges[yEdges > ymid][0]
        log.info(f"Bottom edge found at {ymax}")

        crop_info = self.trim_image_post(
            gray,
            width,
            height,
            width_org,
            height_org,
            [ymin, ymax],
            [xmin, xmax],
        )

        # crop np.ndarray -- y first, x second!
        cropped = original[
            crop_info[1][0] : crop_info[1][1], crop_info[0][0] : crop_info[0][1]
        ].copy()

        cv2.imwrite(self.tmp_cropped_path, cropped)

        return crop_info

    def trim_image_manual(self, manual_points):
        params = self.getParameters()

        # rot_angle = params["rot_angle"]
        # init_blur = params["init_blur"]
        contrast = params["contrast"]
        # brightness = params["brightness"]
        # init_param2 = params["init_param2"]

        image_1 = self.parent.img_bgr.copy()

        image_center = tuple(np.array(image_1.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, 0.0, 1.0)
        image_2 = cv2.warpAffine(
            image_1, rot_mat, image_1.shape[1::-1], flags=cv2.INTER_LINEAR
        )

        # image_3 = cv2.convertScaleAbs(image_2, alpha=contrast, beta=brightness)
        image_3 = cv2.convertScaleAbs(image_2, alpha=contrast, beta=0)

        height_org, width_org, _channel = image_3.shape

        resize_scale = (
            1200 / width_org if width_org >= height_org else 1200 / height_org
        )

        image_4 = cv2.resize(
            image_3, None, None, resize_scale, resize_scale, cv2.INTER_LINEAR
        )

        height, width, _channel = image_4.shape

        for i in range(height):
            for j in range(width):
                image_3.itemset((i, j, 1), 0)

        gray = cv2.cvtColor(image_4, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(self.tmp_preview_path, gray)

        image_inverted = 255 - gray

        cv2.imwrite(
            self.tmp_preview_path.replace("preview", "preview_gray_inverted"),
            image_inverted,
        )

        log.info("Searching pickup points...")

        center_x = int(
            sum([manual_points.get("GA1").get("x"), manual_points.get("GA3").get("x")])
        )
        center_y = int(
            sum([manual_points.get("GA1").get("y"), manual_points.get("GA3").get("y")])
        )

        gauge_std = sum(
            [
                abs(
                    manual_points.get("GA1").get("x")
                    - manual_points.get("GA3").get("x")
                ),
                abs(
                    manual_points.get("GA1").get("y")
                    - manual_points.get("GA3").get("y")
                ),
            ]
        )

        pitch = gauge_std / 41.236  # pixels / mm

        log.info(
            f"gauge_std = {gauge_std:.3f} px: 1mm = {pitch:.3f} px, center = ( {center_x:6.3f}, {center_y:6.3f} )"
        )

        x_edge1_0 = max(int(center_x - self.cropRange * pitch), 0)
        y_edge1_0 = max(int(center_y - self.cropRange * pitch), 0)
        x_edge2_0 = min(int(center_x + self.cropRange * pitch), width - 1)
        y_edge2_0 = min(int(center_y + self.cropRange * pitch), height - 1)

        x_edge1 = max(int((center_x - self.cropRange * pitch) / resize_scale), 0)
        y_edge1 = max(int((center_y - self.cropRange * pitch) / resize_scale), 0)
        x_edge2 = min(
            int((center_x + self.cropRange * pitch) / resize_scale), width_org - 1
        )
        y_edge2 = min(
            int((center_y + self.cropRange * pitch) / resize_scale), height_org - 1
        )

        crop_info = [[x_edge1, x_edge2], [y_edge1, y_edge2]]
        log.info(f"crop_info = {crop_info}")

        cropped = image_2[y_edge1:y_edge2, x_edge1:x_edge2].copy()

        cv2.imwrite(self.tmp_cropped_path, cropped)

        marker_width = int(0.005 * width)

        color = (0, 255, 128)

        # Draw the center reticle
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        cv2.line(
            gray_bgr,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0 + 50, y_edge1_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0, y_edge1_0 + 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0 - 50, y_edge1_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0, y_edge1_0 + 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0 + 50, y_edge2_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0, y_edge2_0 - 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0 - 50, y_edge2_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0, y_edge2_0 - 50),
            color,
            marker_width,
        )

        cv2.circle(
            gray_bgr,
            (
                int(manual_points.get("GA1").get("x")) * 2,
                int(manual_points.get("GA1").get("y")) * 2,
            ),
            10,
            color,
            int(marker_width * 0.5),
        )

        cv2.circle(
            gray_bgr,
            (
                int(manual_points.get("GA3").get("x")) * 2,
                int(manual_points.get("GA3").get("y")) * 2,
            ),
            10,
            color,
            int(marker_width * 0.5),
        )

        cv2.imwrite(self.tmp_preview_path, gray_bgr)

        preview = cv2.imread(self.tmp_preview_path)

        self.cropped = cv2.imread(self.tmp_cropped_path)

        h, w, d = preview.shape

        scale = min(600.0 / float(h), 600.0 / float(w))

        resize_img = cv2.resize(preview, dsize=None, fx=scale, fy=scale)

        img_rgb, h_rgb, w_rgb, d_rgb = img_cvt_rgb(resize_img)
        bytesPerLine = d_rgb * w_rgb

        self.image = QImage(
            img_rgb.data, w_rgb, h_rgb, bytesPerLine, QImage.Format_RGB888
        )

        self.view.items().clear()
        self.scene.clear()

        pixmap = QPixmap.fromImage(self.image)
        self.item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.item)
        self.view.setScene(self.scene)

        return crop_info

    def trim_image_post(
        self,
        image,
        width,
        height,
        width_org,
        height_org,
        xEdges,
        yEdges,
        std1=42.2,
        std2=41.4,
    ):
        center_x = int((xEdges[0] + xEdges[-1]) / 2.0)
        center_y = int((yEdges[0] + yEdges[-1]) / 2.0)

        horLength = abs(xEdges[0] - xEdges[-1])
        verLength = abs(yEdges[0] - yEdges[-1])
        pitch = (horLength / std1 + verLength / std2) / 2.0  # pixels / mm

        marker_width0 = int(0.005 * width)

        x_edge1_0 = max(int(center_x - self.cropRange * pitch), 0)
        y_edge1_0 = max(int(center_y - self.cropRange * pitch), 0)
        x_edge2_0 = min(int(center_x + self.cropRange * pitch), width - 1)
        y_edge2_0 = min(int(center_y + self.cropRange * pitch), height - 1)

        # Draw the center reticle
        gray_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        color = (0, 255, 128)

        cv2.line(
            gray_bgr,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0 + 50, y_edge1_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0, y_edge1_0 + 50),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0 - 50, y_edge1_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0, y_edge1_0 + 50),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0 + 50, y_edge2_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0, y_edge2_0 - 50),
            color,
            marker_width0,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0 - 50, y_edge2_0),
            color,
            marker_width0,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0, y_edge2_0 - 50),
            color,
            marker_width0,
        )

        # Draw detected edges
        cv2.line(
            gray_bgr,
            (xEdges[0], yEdges[0]),
            (xEdges[1], yEdges[0]),
            (255, 200, 200),
            2,
        )

        cv2.line(
            gray_bgr,
            (xEdges[1], yEdges[0]),
            (xEdges[1], yEdges[1]),
            (255, 200, 200),
            2,
        )

        cv2.line(
            gray_bgr,
            (xEdges[1], yEdges[1]),
            (xEdges[0], yEdges[1]),
            (255, 200, 200),
            2,
        )

        cv2.line(
            gray_bgr,
            (xEdges[0], yEdges[1]),
            (xEdges[0], yEdges[0]),
            (255, 200, 200),
            2,
        )

        cv2.imwrite(self.tmp_preview_path, gray_bgr)

        x_edge1 = max(int((center_x - self.cropRange * pitch) / width * width_org), 0)
        y_edge1 = max(int((center_y - self.cropRange * pitch) / height * height_org), 0)
        x_edge2 = min(
            int((center_x + self.cropRange * pitch) / width * width_org), width_org - 1
        )
        y_edge2 = min(
            int((center_y + self.cropRange * pitch) / height * height_org),
            height_org - 1,
        )

        crop_info = [[x_edge1, x_edge2], [y_edge1, y_edge2]]
        log.info(f"crop_info = {crop_info}")

        return crop_info


class QuadPCBBackTrimmer(QuadFrontTrimmer):
    def trim_image(self, params):
        rot_angle = params["rot_angle"]
        init_blur = params["init_blur"]
        contrast = params["contrast"]
        brightness = params["brightness"]
        init_param2 = params["init_param2"]

        image_1 = self.parent.img_bgr.copy()

        image_center = tuple(np.array(image_1.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, rot_angle, 1.0)
        image_2 = cv2.warpAffine(
            image_1, rot_mat, image_1.shape[1::-1], flags=cv2.INTER_LANCZOS4
        )

        image_3 = cv2.convertScaleAbs(image_2, alpha=contrast, beta=brightness)

        height_org, width_org, _channel = image_3.shape

        resize_scale = (
            resize_length / width_org
            if width_org >= height_org
            else resize_length / height_org
        )

        image_4 = cv2.resize(
            image_3, None, None, resize_scale, resize_scale, cv2.INTER_LANCZOS4
        )

        height, width, _channel = image_4.shape

        for i in range(height):
            for j in range(width):
                image_3.itemset((i, j, 1), 0)

        # use only Red color
        gray = image_4[:, :, 2]
        cv2.imwrite(self.tmp_preview_path, gray)

        log.info("Searching pickup points...")

        pitch = None
        pickup_points = None

        for blurSize in range(init_blur, 0, -1):
            try:
                pitch, center, pickup_points = self.houghScan(
                    gray, blurSize, init_param2
                )
                break
            except Exception as e:
                log.info(str(e))
                continue

        if not pitch:
            msg = "failed to find any pickup points"
            raise Exception(msg)

        center_x = int(center[0])
        center_y = int(center[1])

        log.info(f"1mm = {pitch:.3f} px, center = ( {center_x:6.3f}, {center_y:6.3f} )")

        x_edge1_0 = max(int(center_x - self.cropRange * pitch), 0)
        y_edge1_0 = max(int(center_y - self.cropRange * pitch), 0)
        x_edge2_0 = min(int(center_x + self.cropRange * pitch), width - 1)
        y_edge2_0 = min(int(center_y + self.cropRange * pitch), height - 1)

        x_edge1 = max(int((center_x - self.cropRange * pitch) / resize_scale), 0)
        y_edge1 = max(int((center_y - self.cropRange * pitch) / resize_scale), 0)
        x_edge2 = min(
            int((center_x + self.cropRange * pitch) / resize_scale), width_org - 1
        )
        y_edge2 = min(
            int((center_y + self.cropRange * pitch) / resize_scale), height_org - 1
        )

        crop_info = [[x_edge1, x_edge2], [y_edge1, y_edge2]]
        log.info(f"crop_info = {crop_info}")

        cropped = image_2[y_edge1:y_edge2, x_edge1:x_edge2].copy()

        cv2.imwrite(self.tmp_cropped_path, cropped)

        marker_width = int(0.005 * width)

        color = (0, 255, 128)

        # Draw the center reticle
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        cv2.line(
            gray_bgr,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0 + 50, y_edge1_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge1_0),
            (x_edge1_0, y_edge1_0 + 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0 - 50, y_edge1_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge1_0),
            (x_edge2_0, y_edge1_0 + 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0 + 50, y_edge2_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge1_0, y_edge2_0),
            (x_edge1_0, y_edge2_0 - 50),
            color,
            marker_width,
        )

        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0 - 50, y_edge2_0),
            color,
            marker_width,
        )
        cv2.line(
            gray_bgr,
            (x_edge2_0, y_edge2_0),
            (x_edge2_0, y_edge2_0 - 50),
            color,
            marker_width,
        )

        for p in pickup_points:
            cv2.circle(
                gray_bgr,
                (int(p[0]), int(p[1])),
                int(p[2]),
                color,
                int(marker_width * 0.5),
            )

        cv2.imwrite(self.tmp_preview_path, gray_bgr)

        return crop_info

    def houghScan(self, image_inverted, blurSize, param2):
        log.info(f"  Hough search: blurSize = {blurSize}")

        blur = cv2.blur(image_inverted, (blurSize, blurSize))

        height, width = image_inverted.shape

        deg = math.atan(1) / 45.0

        while True:
            if param2 > 80 or param2 < 10:
                msg = "failure in detection"
                raise Exception(msg)

            _ret, image_4 = cv2.threshold(
                blur, thresh=120, maxval=255, type=cv2.THRESH_TOZERO
            )

            # detect circle
            circles = cv2.HoughCircles(
                image=image_4,
                method=cv2.HOUGH_GRADIENT,
                dp=1.0,
                minDist=min(width, height) * 0.12,
                param1=200,
                param2=param2,
                minRadius=int(min(width, height) * 0.005),
                maxRadius=int(min(width, height) * 0.04),
            )

            pickup_cands = []

            for i in circles[0, :]:
                # check if center is in middle of picture
                if (
                    i[0] < width * 0.05
                    or i[0] > width * 0.95
                    or i[1] < height * 0.05
                    or i[1] > height * 0.95
                ):
                    continue

                # draw the outer circle
                cv2.circle(image_4, (int(i[0]), int(i[1])), int(i[2]), (0, 0, 0), 2)

                # draw the center of the circle
                cv2.circle(image_4, (int(i[0]), int(i[1])), 2, (0, 0, 0), 3)

                pickup_cands += [i]

            log.info(f"param2 = {param2}: #pickup_cands = {len( pickup_cands )}")

            pickup_points = set()

            for i in range(len(pickup_cands)):
                for j in range(i + 1, len(pickup_cands)):
                    for k in range(j + 1, len(pickup_cands)):
                        p1 = pickup_cands[i]
                        p2 = pickup_cands[j]
                        p3 = pickup_cands[k]

                        l3 = [abs(p1[0] - p2[0]), abs(p1[1] - p2[1]), p1, p2, p3]
                        l1 = [abs(p2[0] - p3[0]), abs(p2[1] - p3[1]), p2, p3, p1]
                        l2 = [abs(p3[0] - p1[0]), abs(p3[1] - p1[1]), p3, p1, p2]

                        triangle = [
                            {
                                "v1": [line[2][0], line[2][1]],
                                "v2": [line[3][0], line[3][1]],
                                "v3": [line[4][0], line[4][1]],
                                "dx": line[0],
                                "dy": line[1],
                                "length": math.hypot(line[0], line[1]),
                                "angle": math.atan(line[1] / (line[0] + 1.0e-7)),
                            }
                            for line in [l1, l2, l3]
                        ]

                        horLines = [
                            edge for edge in triangle if edge.get("angle") < 2 * deg
                        ]

                        if len(horLines) != 1:
                            continue

                        horIndex = triangle.index(horLines[0])

                        horLine = triangle[horIndex]

                        # log.info( pprint.pformat( horLine ) )

                        # the horizontal line should come at the bottom
                        if horLine.get("v3")[1] < horLine.get("v1")[1]:
                            continue

                        horLength = triangle[horIndex].get("length")

                        others_ratio = [
                            edge.get("length") / horLength
                            for edge in triangle
                            if edge != horLines[0]
                        ]

                        if not all(
                            0.95 * math.sqrt(5.0) / 2.0
                            < ratio
                            < 1.05 * math.sqrt(5.0) / 2.0
                            for ratio in others_ratio
                        ):
                            continue

                        pickup_points.add((p1[0], p1[1], p1[2]))
                        pickup_points.add((p2[0], p2[1], p2[2]))
                        pickup_points.add((p3[0], p3[1], p3[2]))

                        log.info("")
                        log.info("------------------")
                        for p in pickup_points:
                            log.info(
                                f"    Pickup point: center: ({p[0]:.2f}, {p[1]:.2f}), radius: {p[2]:.2f}"
                            )

                        horY = statistics.mean(
                            [horLine.get("v1")[1], horLine.get("v2")[1]]
                        )
                        centerY = statistics.mean([horY, horLine.get("v3")[1]])
                        centerX = statistics.mean(
                            [horLine.get("v1")[0], horLine.get("v2")[0]]
                        )
                        center = [centerX, centerY]
                        gauge_std = horLength / 54.0  # [ pixels/mm ]

                        return gauge_std, center, pickup_points

            if param2 > 80 or param2 < 10:
                msg = "failure in detection"
                raise Exception(msg)

            param2 -= 1
            # end if while loop

        return None
