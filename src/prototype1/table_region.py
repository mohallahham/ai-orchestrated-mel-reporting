import cv2
import numpy as np


def detect_table_region(image, debug=False):
    """
    Detect the largest table-like region in a full attendance/sign-in sheet.

    Returns:
        cropped_image, bbox
    where bbox = (x, y, w, h)
    """

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Light smoothing
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Binary inverse to emphasize dark lines/writing
    binary = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        10,
    )

    h, w = binary.shape

    # Detect horizontal and vertical line structures
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, w // 8), 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, h // 8)))

    horiz = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    vert = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

    table_mask = cv2.add(horiz, vert)

    # Dilate to connect nearby table structures
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    table_mask = cv2.dilate(table_mask, dilate_kernel, iterations=2)

    contours, _ = cv2.findContours(
        table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        if debug:
            print("No table contours found. Returning original image.")
        return image, (0, 0, image.shape[1], image.shape[0])

    # Choose the largest plausible table contour
    best_contour = None
    best_area = 0

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch

        # Ignore tiny regions
        if area < 0.1 * (w * h):
            continue

        # Prefer wide, tall table-like regions
        if area > best_area:
            best_area = area
            best_contour = cnt

    if best_contour is None:
        if debug:
            print("No plausible large table region found. Returning original image.")
        return image, (0, 0, image.shape[1], image.shape[0])

    x, y, cw, ch = cv2.boundingRect(best_contour)

    # Small padding
    pad = 10
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(image.shape[1], x + cw + pad)
    y2 = min(image.shape[0], y + ch + pad)

    cropped = image[y1:y2, x1:x2]

    if debug:
        print(f"Detected table region: x={x1}, y={y1}, w={x2 - x1}, h={y2 - y1}")

    return cropped, (x1, y1, x2 - x1, y2 - y1)


def draw_table_bbox(image, bbox):
    """
    Draw the detected table region on the original image for debugging.
    """
    x, y, w, h = bbox

    if len(image.shape) == 2:
        overlay = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        overlay = image.copy()

    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 3)
    return overlay
