"""Normalize Prototype 1 outputs into an orchestration-friendly summary."""

from typing import Dict, Any


def extract_attendance_summary(p1_output: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a normalized attendance summary from Prototype 1 output."""

    metadata = p1_output.get("metadata", {})
    runs = p1_output.get("runs", [])

    total_records = metadata.get("total_records", 0)
    form_count = metadata.get("form_count", 0)
    successful_forms = metadata.get("successful_forms", 0)

    summaries = []

    for run in runs:
        summaries.append({
            "image_name": run.get("image_name"),
            "record_count": run.get("record_count"),
            "summary": run.get("summary"),
        })

    return {
        "form_count": form_count,
        "successful_forms": successful_forms,
        "total_records": total_records,
        "per_form_summaries": summaries,
    }
