import cv2

from src.schemas import AttendanceRecord, RunMetadata
from src.storage import create_run_id, create_run_folder, save_run_metadata

from src.prototype1.preprocessing import (
    load_image,
    upscale_image,
    convert_to_gray,
    preprocess_for_line_detection,
    preprocess_cell_for_ocr,
)

from src.prototype1.row_detection import detect_row_boundaries
from src.prototype1.ocr_engine import OCREngine
from src.prototype1.parsing import classify_gender, extract_age
from src.prototype1.validation import validate_record

from src.prototype1.output_writer import (
    save_records_csv,
    save_records_json,
    build_summary,
    save_summary_json,
    save_debug_image,
    save_row_debug_images,
)

from src.utils import timestamp_string
from src.prototype1.interfaces import ExtractionEngine


def run_baseline_ocr_pipeline(
    image_path: str,
    split_ratio: float = 0.55,
    debug: bool = False,
    save_outputs: bool = True,
):
    """
    OCR pipeline for already-cropped attendance table / field-region images.

    This version does NOT do:
    - full-sheet table detection
    - field-region cropping

    It assumes the uploaded image is already focused on the relevant
    attendance table area.
    """

    img = load_image(image_path)
    img = upscale_image(img)
    gray = convert_to_gray(img)

    binary = preprocess_for_line_detection(gray)
    rows, horiz_img, centers = detect_row_boundaries(binary)

    if debug:
        print(f"Loaded cropped image: {image_path}")
        print(f"Detected rows: {len(rows)}")

    run_path = None

    if not rows:
        if save_outputs:
            run_id = create_run_id(prefix="baseline_ocr_run")
            run_path = create_run_folder(run_id)

            metadata = RunMetadata(
                run_id=run_id,
                prototype_name="prototype1_baseline_ocr_cropped",
                timestamp=timestamp_string(),
                input_files=[image_path],
                notes="Baseline OCR cropped-image run | no rows detected",
            )

            save_run_metadata(run_path, metadata.to_dict())
            save_debug_image(binary, run_path / "debug_binary.png")

            if debug:
                print(f"No rows detected. Saved debug outputs to: {run_path}")

        return {
            "records": [],
            "summary": {},
            "run_path": str(run_path) if run_path else None,
        }

    ocr = OCREngine()

    h, w = gray.shape
    split_x = int(w * split_ratio)

    records = []
    debug_items = []

    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for y in centers:
        cv2.line(
            overlay,
            (0, int(y)),
            (overlay.shape[1] - 1, int(y)),
            (0, 0, 255),
            2,
        )

    for idx, (y1, y2) in enumerate(rows, start=1):
        pad = 6
        yy1 = max(0, int(y1) + pad)
        yy2 = min(h, int(y2) - pad)

        if yy2 <= yy1:
            continue

        row_band = gray[yy1:yy2, :]
        gender_cell = row_band[:, :split_x]
        age_cell = row_band[:, split_x:]

        gender_proc = preprocess_cell_for_ocr(gender_cell, mode="text")
        age_proc = preprocess_cell_for_ocr(age_cell, mode="digits")

        g_text, g_conf = ocr.read_text(gender_proc)
        a_text, a_conf = ocr.read_text(age_proc)

        gender = classify_gender(g_text)
        age = extract_age(a_text)

        record = AttendanceRecord(
            row_id=idx,
            gender_raw=g_text,
            gender_label=gender,
            gender_confidence=g_conf,
            age_raw=a_text,
            age_value=age,
            age_confidence=a_conf,
        )

        record.validation_flags = validate_record(record)
        records.append(record)

        debug_items.append(
            {
                "row_id": idx,
                "gender_raw_img": gender_cell,
                "gender_proc_img": gender_proc,
                "age_raw_img": age_cell,
                "age_proc_img": age_proc,
            }
        )

        if debug:
            print(f"Row {idx}: {record.to_dict()}")

    summary = build_summary(records)

    if save_outputs:
        run_id = create_run_id(prefix="baseline_ocr_run")
        run_path = create_run_folder(run_id)

        metadata = RunMetadata(
            run_id=run_id,
            prototype_name="prototype1_baseline_ocr_cropped",
            timestamp=timestamp_string(),
            input_files=[image_path],
            notes="Baseline OCR cropped-image run",
        )

        save_run_metadata(run_path, metadata.to_dict())

        save_records_csv(records, run_path / "attendance_records.csv")
        save_records_json(records, run_path / "attendance_records.json")
        save_summary_json(summary, run_path / "attendance_summary.json")

        save_debug_image(binary, run_path / "debug_binary.png")
        save_debug_image(overlay, run_path / "debug_row_overlay.png")
        save_row_debug_images(debug_items, run_path / "debug")

        if debug:
            print(f"Saved outputs to: {run_path}")

    return {
        "records": records,
        "summary": summary,
        "run_path": str(run_path) if run_path else None,
    }


class BaselineOCRExtractionEngine(ExtractionEngine):
    def extract_rows(self, image_path: str, **kwargs):
        return run_baseline_ocr_pipeline(image_path, **kwargs)
