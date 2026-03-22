from pathlib import Path
from typing import List

from src.prototype1.interfaces import ExtractionEngine
from src.schemas import AttendanceRecord, RunMetadata
from src.storage import create_run_id, create_run_folder, save_run_metadata
from src.utils import timestamp_string

from src.prototype1.output_writer import (
    save_records_csv,
    save_records_json,
    build_summary,
    save_summary_json,
    save_debug_image,
)

from src.prototype1.crop_exporter import export_row_and_cell_crops
from src.prototype1.preprocessing import (
    load_image,
    upscale_image,
    convert_to_gray,
    preprocess_for_line_detection,
)

from src.prototype1.row_detection import detect_row_boundaries
from src.prototype1.validation import validate_record

from src.prototype1.table_region import detect_table_region, draw_table_bbox
from src.prototype1.field_region import crop_age_gender_region, draw_field_bbox

from src.prototype1.vision.orchestrator import (
    extract_with_orchestration,
    FAST_MODEL,
)
from src.prototype1.vision.ollama_vision import call_vision_model


class VisionExtractionEngine(ExtractionEngine):
    def extract_rows(
        self,
        image_path: str,
        split_ratio=0.55,
        debug=False,
        save_outputs=True,
        fast_mode=False,
        max_rows=None,
    ):
        # --------------------------------------------------
        # Load full sheet
        # --------------------------------------------------
        original_img = load_image(image_path)

        # --------------------------------------------------
        # Stage 1: detect full table region
        # --------------------------------------------------
        cropped_img, table_bbox = detect_table_region(original_img, debug=debug)

        # --------------------------------------------------
        # Stage 2: crop age + gender field region
        # --------------------------------------------------
        field_img, field_bbox = crop_age_gender_region(cropped_img, debug=debug)

        # --------------------------------------------------
        # Continue with focused field image
        # --------------------------------------------------
        img = upscale_image(field_img, scale=1.5 if fast_mode else 2.0)
        gray = convert_to_gray(img)
        binary = preprocess_for_line_detection(gray)
        rows, horiz, centers = detect_row_boundaries(binary)

        if max_rows is not None:
            rows = rows[:max_rows]

        if debug:
            print(f"Loaded image: {image_path}")
            print(f"Detected rows: {len(rows)}")
            print(f"Fast mode: {fast_mode}")

        run_path = None

        if not rows:
            if save_outputs:
                run_id = create_run_id(prefix="vision_run")
                run_path = create_run_folder(run_id)

                metadata = RunMetadata(
                    run_id=run_id,
                    prototype_name="prototype1_vision_extraction_hybrid",
                    timestamp=timestamp_string(),
                    input_files=[image_path],
                    notes="Vision pipeline run with full-sheet table detection and field crop | no rows detected",
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

        # --------------------------------------------------
        # Create run folder
        # --------------------------------------------------
        if save_outputs:
            run_id = create_run_id(prefix="vision_run")
            run_path = create_run_folder(run_id)

            metadata = RunMetadata(
                run_id=run_id,
                prototype_name="prototype1_vision_extraction_hybrid" if not fast_mode else "prototype1_vision_extraction_fast",
                timestamp=timestamp_string(),
                input_files=[image_path],
                notes=f"Prototype 1 vision extraction with full-sheet table detection and field crop | fast_mode={fast_mode}",
            )
            save_run_metadata(run_path, metadata.to_dict())
        else:
            temp_run_id = create_run_id(prefix="vision_temp")
            run_path = create_run_folder(temp_run_id)

        # --------------------------------------------------
        # Export row crops from focused region
        # --------------------------------------------------
        split_x = int(gray.shape[1] * split_ratio)
        crop_paths = export_row_and_cell_crops(
            gray_image=gray,
            rows=rows,
            split_x=split_x,
            run_path=run_path,
            resize_for_vision=True,
        )

        # Save shared debug artefacts
        table_overlay = draw_table_bbox(original_img, table_bbox)
        field_overlay = draw_field_bbox(cropped_img, field_bbox)

        save_debug_image(table_overlay, run_path / "debug_table_region.png")
        save_debug_image(cropped_img, run_path / "debug_cropped_table.png")
        save_debug_image(field_overlay, run_path / "debug_field_region.png")
        save_debug_image(field_img, run_path / "debug_field_crop.png")
        save_debug_image(binary, run_path / "debug_binary.png")

        # --------------------------------------------------
        # Vision extraction
        # --------------------------------------------------
        records: List[AttendanceRecord] = []

        for item in crop_paths:
            row_id = item["row"]
            row_path = Path(item["row_path"])

            if fast_mode:
                result = call_vision_model(row_path, model=FAST_MODEL)
                model_used = "fast"
            else:
                result, model_used = extract_with_orchestration(row_path, debug=debug)

            gender = result.get("gender", "Unknown")
            age = result.get("age", None)
            notes = result.get("notes", "")

            record = AttendanceRecord(
                row_id=row_id,
                gender_raw=f"VISION({model_used}):{result}",
                gender_label=gender if gender in {"Male", "Female", "Unknown"} else "Unknown",
                gender_confidence=1.0,
                age_raw=str(age) if isinstance(age, int) else "",
                age_value=age if isinstance(age, int) else None,
                age_confidence=1.0 if isinstance(age, int) else 0.0,
            )

            record.validation_flags = validate_record(record)

            if notes:
                record.validation_flags.append(f"vision_note:{notes}")

            records.append(record)

            if debug:
                print(f"Row {row_id}: {record.to_dict()}")

        summary = build_summary(records)

        # --------------------------------------------------
        # Save outputs
        # --------------------------------------------------
        if save_outputs and run_path:
            save_records_csv(records, run_path / "attendance_records.csv")
            save_records_json(records, run_path / "attendance_records.json")
            save_summary_json(summary, run_path / "attendance_summary.json")

            if debug:
                print(f"Saved outputs to: {run_path}")

        return {
            "records": records,
            "summary": summary,
            "run_path": str(run_path) if run_path else None,
        }
