import cv2


def crop_age_gender_region(table_image, debug=False):
    """
    Crop the age + gender columns from the detected attendance table.

    Assumes the table follows the current attendance-sheet layout:
    [signature | institution | phone | gender | age | name | number]

    Returns:
        cropped_region, bbox
    where bbox = (x, y, w, h) relative to the table image
    """

    h, w = table_image.shape[:2]

    # Empirical column range for [gender + age]
    # Tuned to the current sheet layout
    x1 = int(w * 0.54)
    x2 = int(w * 0.73)

    y1 = 0
    y2 = h

    cropped = table_image[y1:y2, x1:x2]

    if debug:
        print(f"Age/gender crop: x={x1}, y={y1}, w={x2 - x1}, h={y2 - y1}")

    return cropped, (x1, y1, x2 - x1, y2 - y1)


def draw_field_bbox(table_image, bbox):
    """
    Draw bounding box for the age+gender region on the detected table image.
    """
    x, y, w, h = bbox

    if len(table_image.shape) == 2:
        overlay = cv2.cvtColor(table_image, cv2.COLOR_GRAY2BGR)
    else:
        overlay = table_image.copy()

    cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 0, 0), 3)
    return overlay
