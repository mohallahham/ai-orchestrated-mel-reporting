import cv2
import numpy as np


def detect_row_boundaries(binary_img, min_row_height=20, threshold_ratio=0.3):
    h, w = binary_img.shape

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(40, w // 3), 1)
    )

    horiz = cv2.erode(binary_img, kernel, iterations=1)
    horiz = cv2.dilate(horiz, kernel, iterations=2)

    projection = horiz.sum(axis=1)
    threshold = projection.max() * threshold_ratio

    ys = np.where(projection > threshold)[0]

    if len(ys) < 2:
        return [], horiz, []

    centers = []
    start = ys[0]
    prev = ys[0]

    for y in ys[1:]:
        if y == prev + 1:
            prev = y
        else:
            centers.append((start + prev) // 2)
            start = y
            prev = y

    centers.append((start + prev) // 2)
    centers = sorted(centers)

    rows = []
    for i in range(len(centers) - 1):
        y1 = centers[i]
        y2 = centers[i + 1]

        if (y2 - y1) >= min_row_height:
            rows.append((y1, y2))

    return rows, horiz, centers