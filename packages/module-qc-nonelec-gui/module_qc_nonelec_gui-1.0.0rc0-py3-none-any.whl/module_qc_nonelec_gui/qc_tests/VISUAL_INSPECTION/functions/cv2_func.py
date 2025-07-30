from __future__ import annotations

import math

import cv2


def read_img(path):
    img = cv2.imread(path, 1)
    h, w, d = img.shape
    return img, h, w, d


def img_cvt_rgb(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, d = img_rgb.shape
    return img_rgb, h, w, d


def img_rotate(img):
    img_rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    h, w, d = img_rotated.shape
    return img_rotated, h, w, d


def write_img(img, path):
    cv2.imwrite(path, img)
    return 0


def rotate_img(img, h, w, dx, dy):
    theta = math.atan2(dy, dx)
    degree = math.degrees(theta)
    mat = cv2.getRotationMatrix2D((w / 2, h / 2), degree, 1)
    affine_img = cv2.warpAffine(img, mat, (w, h))

    return affine_img, mat
