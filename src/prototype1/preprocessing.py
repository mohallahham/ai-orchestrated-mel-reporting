import cv2
import numpy as np


def load_image(path: str):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img


def upscale_image(img, scale=2.0):
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)


def convert_to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def preprocess_for_line_detection(gray):
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    binary_inv = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        10
    )

    return binary_inv


def preprocess_cell_for_ocr(cell_img, mode="text"):

    g = cv2.GaussianBlur(cell_img, (3, 3), 0)

    if mode == "text":
        return cv2.adaptiveThreshold(
            g,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            8
        )

    if mode == "digits":
        return cv2.adaptiveThreshold(
            g,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            31,
            10
        )

    return g