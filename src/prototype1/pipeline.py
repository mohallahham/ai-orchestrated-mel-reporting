from pathlib import Path
import cv2

from src.prototype1.table_region import detect_table_region, draw_table_bbox
from src.prototype1.field_region import crop_age_gender_region, draw_field_bbox
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

from src.pipeline_contracts import build_pipeline_result
from src.utils import timestamp_string


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def run_extraction_pipeline(
    image_path: str,
    split_ratio: float = 0.55,
    debug: bool = False,
    save_outputs: bool = True,
):
    original_img = load_image(image_path)

    # --------------------------------------------
    # Stage 1: detect full table region
    # --------------------------------------------
    cropped_img, table_bbox = detect_table_region(original_img, debug=debug)

    # --------------------------------------------
    # Stage 2: crop only age + gender columns
    # --------------------------------------------
    field_img, field_bbox = crop_age_gender_region(cropped_img, debug=debug)

    # Continue extraction on focused region only
    img = upscale_image(field_img)
    gray = convert_to_gray(img)

    binary = preprocess_for_line_detection(gray)
    rows, horiz_img, centers = detect_row_boundaries(binary)

    if debug:
        print(f"Loaded image: {image_path}")
        print(f"Detected rows: {len(rows)}")

    run_path = None

    # --------------------------------------------
    # Early return if row detection fails
    # --------------------------------------------
    if not rows:
        if save_outputs:
            run_id = create_run_id(prefix="run")
            run_path = create_run_folder(run_id)

            metadata = RunMetadata(
                run_id=run_id,
                prototype_name="prototype1_document_extraction",
                timestamp=timestamp_string(),
                input_files=[image_path],
                notes="OCR pipeline run with full-sheet table detection and field crop | no rows detected",
            )

            save_run_metadata(run_path, metadata.to_dict())

            table_overlay = draw_table_bbox(original_img, table_bbox)
            field_overlay = draw_field_bbox(cropped_img, field_bbox)

            save_debug_image(table_overlay, run_path / "debug_table_region.png")
            save_debug_image(cropped_img, run_path / "debug_cropped_table.png")
            save_debug_image(field_overlay, run_path / "debug_field_region.png")
            save_debug_image(field_img, run_path / "debug_field_crop.png")
            save_debug_image(binary, run_path / "debug_binary.png")

            if debug:
                print(f"No rows detected. Saved debug outputs to: {run_path}")

        return {
            "records": [],
            "summary": {},
            "run_path": str(run_path) if run_path else None,
        }

    # --------------------------------------------
    # OCR engine
    # --------------------------------------------
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

    # --------------------------------------------
    # Process each row
    # --------------------------------------------
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

    # --------------------------------------------
    # Build summary
    # --------------------------------------------
    summary = build_summary(records)

    # --------------------------------------------
    # Save outputs
    # --------------------------------------------
    if save_outputs:
        run_id = create_run_id(prefix="run")
        run_path = create_run_folder(run_id)

        metadata = RunMetadata(
            run_id=run_id,
            prototype_name="prototype1_document_extraction",
            timestamp=timestamp_string(),
            input_files=[image_path],
            notes="OCR pipeline run with full-sheet table detection and field crop",
        )

        save_run_metadata(run_path, metadata.to_dict())

        save_records_csv(records, run_path / "attendance_records.csv")
        save_records_json(records, run_path / "attendance_records.json")
        save_summary_json(summary, run_path / "attendance_summary.json")

        save_debug_image(binary, run_path / "debug_binary.png")
        save_debug_image(overlay, run_path / "debug_row_overlay.png")

        table_overlay = draw_table_bbox(original_img, table_bbox)
        field_overlay = draw_field_bbox(cropped_img, field_bbox)

        save_debug_image(table_overlay, run_path / "debug_table_region.png")
        save_debug_image(cropped_img, run_path / "debug_cropped_table.png")
        save_debug_image(field_overlay, run_path / "debug_field_region.png")
        save_debug_image(field_img, run_path / "debug_field_crop.png")

        save_row_debug_images(debug_items, run_path / "debug")

        if debug:
            print(f"Saved outputs to: {run_path}")

    return {
        "records": records,
        "summary": summary,
        "run_path": str(run_path) if run_path else None,
    }


def _list_input_images(input_dir: str | Path) -> list[Path]:
    input_path = Path(input_dir)

    return sorted(
        [
            path for path in input_path.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ]
    )


def _build_batch_summary(
    prototype: str,
    image_files: list[Path],
    runs: list[dict],
    output_files: list[str],
) -> dict:
    successful_forms = len([run for run in runs if run.get("run_path")])
    total_records = sum(run.get("record_count", 0) for run in runs)
    run_paths = [run["run_path"] for run in runs if run.get("run_path")]

    metadata = {
        "prototype": prototype,
        "form_count": len(image_files),
        "successful_forms": successful_forms,
        "total_records": total_records,
        "run_paths": run_paths,
        "output_files": output_files,
    }

    return build_pipeline_result(
        metadata,
        artifacts={"runs": runs},
        runs=runs,
    )


def run_prototype1_pipeline(input_dir):
    """Process all input images with the OCR extraction pipeline."""
    image_files = _list_input_images(input_dir)

    runs = []

    for img_path in image_files:
        result = run_extraction_pipeline(str(img_path))

        runs.append(
            {
                "image_name": img_path.name,
                "record_count": len(result["records"]),
                "summary": result["summary"],
                "run_path": result["run_path"],
            }
        )

    return _build_batch_summary(
        prototype="prototype1",
        image_files=image_files,
        runs=runs,
        output_files=[
            "attendance_records.csv",
            "attendance_records.json",
            "attendance_summary.json",
            "debug images",
            "crops",
        ],
    )


def run_prototype1_vision_pipeline(input_dir):
    """Process all input images with the Prototype 1 vision pipeline."""
    from src.prototype1.vision.pipeline import VisionExtractionEngine

    image_files = _list_input_images(input_dir)

    engine = VisionExtractionEngine()
    runs = []

    for img_path in image_files:
        result = engine.extract_rows(image_path=str(img_path))

        runs.append(
            {
                "image_name": img_path.name,
                "record_count": len(result.get("records", [])),
                "summary": result.get("summary", {}),
                "run_path": result.get("run_path"),
            }
        )

    return _build_batch_summary(
        prototype="prototype1_vision",
        image_files=image_files,
        runs=runs,
        output_files=[
            "attendance_records.csv",
            "attendance_records.json",
            "attendance_summary.json",
            "vision debug outputs",
        ],
    )
