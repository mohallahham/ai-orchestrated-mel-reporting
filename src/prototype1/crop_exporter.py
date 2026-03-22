import cv2
from pathlib import Path

from src.utils import ensure_directory


def _resize_for_vision(image, max_width=900, max_height=300):
    h, w = image.shape[:2]

    scale_w = max_width / w
    scale_h = max_height / h
    scale = min(scale_w, scale_h, 1.0)

    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    if scale < 1.0:
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return image


def export_row_and_cell_crops(
    gray_image,
    rows,
    split_x,
    run_path: Path,
    resize_for_vision=True,
):
    crop_dir = ensure_directory(run_path / "crops")

    saved_paths = []

    for idx, (y1, y2) in enumerate(rows, start=1):
        y1 = int(y1)
        y2 = int(y2)

        row_img = gray_image[y1:y2, :]
        gender_cell = row_img[:, :split_x]
        age_cell = row_img[:, split_x:]

        if resize_for_vision:
            row_img = _resize_for_vision(row_img, max_width=900, max_height=300)
            gender_cell = _resize_for_vision(gender_cell, max_width=650, max_height=300)
            age_cell = _resize_for_vision(age_cell, max_width=250, max_height=300)

        row_path = crop_dir / f"row_{idx:02d}.png"
        gender_path = crop_dir / f"row_{idx:02d}_gender.png"
        age_path = crop_dir / f"row_{idx:02d}_age.png"

        cv2.imwrite(str(row_path), row_img)
        cv2.imwrite(str(gender_path), gender_cell)
        cv2.imwrite(str(age_path), age_cell)

        saved_paths.append(
            {
                "row": idx,
                "row_path": str(row_path),
                "gender_path": str(gender_path),
                "age_path": str(age_path),
            }
        )

    return saved_paths