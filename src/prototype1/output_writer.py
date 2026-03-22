import csv
from pathlib import Path
from typing import List
import cv2

from src.schemas import AttendanceRecord
from src.utils import save_json, ensure_directory


def save_records_csv(records: List[AttendanceRecord], path: Path) -> Path:
    fieldnames = [
        "row_id",
        "gender_raw",
        "gender_label",
        "gender_confidence",
        "age_raw",
        "age_value",
        "age_confidence",
        "validation_flags",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            row = record.to_dict()
            row["validation_flags"] = ", ".join(record.validation_flags)
            writer.writerow(row)

    return path


def save_records_json(records: List[AttendanceRecord], path: Path) -> Path:
    data = [record.to_dict() for record in records]
    save_json(data, path)
    return path


def build_summary(records: List[AttendanceRecord]) -> dict:
    male = sum(1 for r in records if r.gender_label == "Male")
    female = sum(1 for r in records if r.gender_label == "Female")
    unknown = sum(1 for r in records if r.gender_label == "Unknown")

    ages = [r.age_value for r in records if r.age_value is not None]
    flagged_records = sum(1 for r in records if r.validation_flags)

    summary = {
        "total_rows": len(records),
        "male_count": male,
        "female_count": female,
        "unknown_gender_count": unknown,
        "ages_extracted_count": len(ages),
        "flagged_records_count": flagged_records,
        "mean_age": round(sum(ages) / len(ages), 2) if ages else None,
        "min_age": min(ages) if ages else None,
        "max_age": max(ages) if ages else None,
    }

    return summary


def save_summary_json(summary: dict, path: Path) -> Path:
    save_json(summary, path)
    return path


def save_debug_image(img, path: Path) -> Path:
    cv2.imwrite(str(path), img)
    return path


def save_row_debug_images(debug_items: list, debug_dir: Path) -> Path:
    ensure_directory(debug_dir)

    for item in debug_items:
        row_id = item["row_id"]

        cv2.imwrite(str(debug_dir / f"row_{row_id:02d}_gender_raw.png"), item["gender_raw_img"])
        cv2.imwrite(str(debug_dir / f"row_{row_id:02d}_gender_proc.png"), item["gender_proc_img"])
        cv2.imwrite(str(debug_dir / f"row_{row_id:02d}_age_raw.png"), item["age_raw_img"])
        cv2.imwrite(str(debug_dir / f"row_{row_id:02d}_age_proc.png"), item["age_proc_img"])

    return debug_dir