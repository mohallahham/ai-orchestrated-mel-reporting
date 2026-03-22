"""Build a practical integrated MEL report from orchestration outputs."""

from __future__ import annotations

from typing import Any, Dict, List


def _build_heading(title: str) -> str:
    return f"{title}\n{'-' * len(title)}"


def _coerce_attendance_summary(results: Dict[str, Any]) -> Dict[str, Any] | None:
    attendance_summary = results.get("attendance_summary")
    if attendance_summary:
        return attendance_summary

    prototype1_output = results.get("prototype1")
    if not prototype1_output:
        return None

    metadata = prototype1_output.get("metadata", {})
    runs = prototype1_output.get("runs", [])

    if not metadata and not runs:
        return None

    return {
        "form_count": metadata.get("form_count", len(runs)),
        "successful_forms": metadata.get(
            "successful_forms",
            len([run for run in runs if run.get("run_path")]),
        ),
        "total_records": metadata.get(
            "total_records",
            sum(run.get("record_count", 0) for run in runs),
        ),
        "per_form_summaries": runs,
        "source_mode": metadata.get("prototype", "prototype1"),
    }


def _safe_get_attendance_summary(attendance_summary: Dict[str, Any] | None) -> Dict[str, Any]:
    if not attendance_summary:
        return {
            "available": False,
            "form_count": 0,
            "successful_forms": 0,
            "total_records": 0,
            "per_form": [],
            "source_mode": "none",
            "quality_note": "Attendance evidence was not available for this run.",
            "text": "Attendance evidence was not available for this run.",
        }

    form_count = attendance_summary.get("form_count", 0)
    successful_forms = attendance_summary.get("successful_forms", 0)
    total_records = attendance_summary.get("total_records", 0)
    per_form = attendance_summary.get("per_form_summaries", [])
    source_mode = attendance_summary.get("source_mode", "prototype1")

    if successful_forms == 0:
        quality_note = (
            "Attendance processing completed, but no forms produced usable structured output."
        )
    elif total_records == 0:
        quality_note = (
            "Attendance processing detected forms, but no participant rows were recovered."
        )
    elif source_mode == "prototype1_vision":
        quality_note = (
            "Attendance figures were generated through the vision-based Prototype 1 path and should be treated as draft evidence pending manual verification."
        )
    else:
        quality_note = (
            "Attendance figures were generated through the OCR-based Prototype 1 path and should be checked before external reporting."
        )

    lines = [
        (
            f"Attendance records were extracted from {successful_forms} successful form(s) "
            f"out of {form_count} processed form(s), with a total of {total_records} participant record(s) detected."
        )
    ]
    lines.append(quality_note)

    if per_form:
        for item in per_form:
            image_name = item.get("image_name", "unknown_form")
            record_count = item.get("record_count", 0)
            lines.append(f"- {image_name}: {record_count} extracted participant record(s).")

    return {
        "available": True,
        "form_count": form_count,
        "successful_forms": successful_forms,
        "total_records": total_records,
        "per_form": per_form,
        "source_mode": source_mode,
        "quality_note": quality_note,
        "text": "\n".join(lines),
    }


def _safe_get_narrative_sections(prototype2_output: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    if not prototype2_output:
        return []

    ui_summary = prototype2_output.get("ui_summary", {})
    return ui_summary.get("sections", [])


def _safe_get_narrative_summary(prototype2_output: Dict[str, Any] | None) -> Dict[str, Any]:
    sections = _safe_get_narrative_sections(prototype2_output)

    if not sections:
        return {
            "available": False,
            "sections": [],
            "grounded_sections": 0,
            "quality_note": "Narrative evidence was not available for this run.",
            "text": "Narrative evidence was not available for this run.",
        }

    ordered_categories = [
        "activities",
        "outcomes",
        "challenges",
        "lessons_learned",
    ]

    section_map = {section.get("category"): section for section in sections}

    lines: List[str] = []
    ordered_sections: List[Dict[str, Any]] = []

    for category in ordered_categories:
        section = section_map.get(category)
        if not section:
            continue

        title = section.get("title", category.replace("_", " ").title())
        text = section.get("narrative_text", "").strip()
        evidence_count = section.get("evidence_count", 0)
        source_documents = section.get("source_documents", [])
        grounded = bool(section.get("grounded"))

        ordered_sections.append(section)

        lines.append(title)
        lines.append(text if text else "No grounded narrative text available.")

        if source_documents:
            joined_docs = ", ".join(source_documents)
            lines.append(
                f"Evidence base: {evidence_count} supporting evidence item(s) from {joined_docs}."
            )
        else:
            lines.append(
                f"Evidence base: {evidence_count} supporting evidence item(s)."
            )

        lines.append("")

    grounded_sections = sum(1 for section in ordered_sections if section.get("grounded"))
    quality_note = (
        f"{grounded_sections} grounded section(s) were produced from uploaded narrative evidence."
    )

    return {
        "available": True,
        "sections": ordered_sections,
        "grounded_sections": grounded_sections,
        "quality_note": quality_note,
        "text": "\n".join(lines).strip(),
    }


def _safe_get_transcript_summary(prototype3_output: Dict[str, Any] | None) -> Dict[str, Any]:
    if not prototype3_output:
        return {
            "available": False,
            "document_count": 0,
            "preview": "",
            "quality_note": "Transcript-derived evidence was not available for this run.",
            "text": "Transcript-derived evidence was not available for this run.",
        }

    ui_summary = prototype3_output.get("ui_summary", {})
    transcript_preview = (ui_summary.get("transcript_preview") or "").strip()
    document_count = ui_summary.get("document_count", 0)

    if not transcript_preview:
        return {
            "available": document_count > 0,
            "document_count": document_count,
            "preview": "",
            "quality_note": (
                "Speech processing completed, but no transcript preview was available for interpretation."
            ),
            "text": (
                f"Transcript processing ran on {document_count} audio document(s), "
                "but no transcript preview was available in the orchestration summary."
            ),
        }

    return {
        "available": True,
        "document_count": document_count,
        "preview": transcript_preview,
        "quality_note": (
            f"Speech processing added contextual evidence from {document_count} audio document(s)."
        ),
        "text": "\n".join(
            [
                (
                    f"Speech-to-text processing was completed for {document_count} audio document(s). "
                    "The following transcript preview provides additional contextual evidence:"
                ),
                transcript_preview,
            ]
        ),
    }


def _build_data_coverage_block(
    attendance: Dict[str, Any],
    narrative: Dict[str, Any],
    transcript: Dict[str, Any],
    included_modalities: List[str],
) -> str:
    coverage_lines = [
        f"Included modalities: {', '.join(included_modalities) if included_modalities else 'none'}."
    ]

    if attendance["available"]:
        coverage_lines.append(
            f"Attendance coverage: {attendance['successful_forms']} successful form(s), {attendance['total_records']} participant record(s)."
        )
    else:
        coverage_lines.append("Attendance coverage: no attendance evidence was available.")

    if narrative["available"]:
        coverage_lines.append(
            f"Narrative coverage: {narrative['grounded_sections']} grounded narrative section(s) were produced."
        )
    else:
        coverage_lines.append("Narrative coverage: no narrative evidence was available.")

    if transcript["available"]:
        coverage_lines.append(
            f"Speech coverage: {transcript['document_count']} audio transcript(s) were processed."
        )
    else:
        coverage_lines.append("Speech coverage: no transcript evidence was available.")

    return "\n".join(coverage_lines)


def _build_key_findings(
    attendance: Dict[str, Any],
    narrative: Dict[str, Any],
    transcript: Dict[str, Any],
) -> str:
    findings: List[str] = []

    if narrative["available"]:
        findings.append(
            f"- Narrative evidence produced {narrative['grounded_sections']} grounded reporting section(s), making this the strongest evidence stream in the current run."
        )

    if attendance["available"]:
        findings.append(
            f"- Attendance processing detected {attendance['total_records']} participant row(s) across {attendance['successful_forms']} successful form(s), but these figures should be treated as draft counts until manually checked."
        )

    if transcript["available"]:
        findings.append(
            f"- Audio processing added contextual support from {transcript['document_count']} transcript(s), which may help explain activities or field conditions not fully described in narrative reports."
        )

    if not findings:
        findings.append("- No strong evidence streams were available for this run.")

    return "\n".join(findings)


def _build_executive_summary(
    attendance: Dict[str, Any],
    narrative: Dict[str, Any],
    transcript: Dict[str, Any],
) -> str:
    summary_lines: List[str] = []

    if narrative["available"]:
        summary_lines.append(
            f"Narrative synthesis generated {narrative['grounded_sections']} grounded reporting section(s) based on uploaded text evidence."
        )

    if attendance["available"]:
        summary_lines.append(
            f"Attendance processing identified {attendance['total_records']} participant record(s) across {attendance['successful_forms']} successfully processed form(s), subject to manual verification."
        )

    if transcript["available"]:
        summary_lines.append(
            f"Speech transcription contributed contextual evidence from {transcript['document_count']} audio document(s)."
        )

    if not summary_lines:
        return "No usable evidence was available to generate an integrated MEL summary for this run."

    return " ".join(summary_lines)


def _build_limitations_block(
    attendance: Dict[str, Any],
    narrative: Dict[str, Any],
    transcript: Dict[str, Any],
) -> str:
    limitations: List[str] = []

    if attendance["available"]:
        limitations.append(
            "- Attendance figures were generated automatically and should be treated as provisional unless verified against the original forms."
        )
    else:
        limitations.append(
            "- No attendance evidence was available, so participation reporting is incomplete."
        )

    if not narrative["available"]:
        limitations.append(
            "- No narrative evidence was available, limiting the report's ability to explain activities, outcomes, and challenges."
        )

    if transcript["available"]:
        limitations.append(
            "- Transcript excerpts provide context, but transcription quality may vary with recording quality and should not be treated as fully authoritative without review."
        )

    return "\n".join(limitations)


def _build_follow_up_actions(
    attendance: Dict[str, Any],
    narrative: Dict[str, Any],
    transcript: Dict[str, Any],
) -> str:
    actions: List[str] = []

    if attendance["available"]:
        actions.append(
            "- Verify attendance counts, ages, and gender labels against the original sign-in sheets before using them in donor-facing reporting."
        )

    if narrative["available"]:
        actions.append(
            "- Review the narrative sections to confirm that the generated wording matches programme intent and organisational terminology."
        )

    if transcript["available"]:
        actions.append(
            "- Use transcript excerpts as supporting context and confirm any important factual details against the source audio if they will be quoted or relied upon."
        )

    if not actions:
        actions.append("- Collect at least one usable evidence source before generating a final MEL draft.")

    return "\n".join(actions)


def _build_report_sections(
    attendance: Dict[str, Any],
    narrative: Dict[str, Any],
    transcript: Dict[str, Any],
    included_modalities: List[str],
) -> List[Dict[str, str]]:
    return [
        {
            "title": "Executive Summary",
            "body": _build_executive_summary(attendance, narrative, transcript),
        },
        {
            "title": "Key Findings",
            "body": _build_key_findings(attendance, narrative, transcript),
        },
        {
            "title": "Participation and Attendance",
            "body": attendance["text"],
        },
        {
            "title": "Narrative Findings",
            "body": narrative["text"],
        },
        {
            "title": "Audio and Field Context",
            "body": transcript["text"],
        },
        {
            "title": "Data Quality and Limitations",
            "body": _build_limitations_block(attendance, narrative, transcript),
        },
        {
            "title": "Suggested Follow-up Actions",
            "body": _build_follow_up_actions(attendance, narrative, transcript),
        },
        {
            "title": "Data Coverage Note",
            "body": _build_data_coverage_block(
                attendance,
                narrative,
                transcript,
                included_modalities,
            ),
        },
    ]


def build_integrated_mel_draft(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an integrated MEL-style draft from orchestration results.

    Returns:
        dict with:
        - title
        - mel_draft_text
        - included_modalities
        - report_sections
    """
    attendance_summary = _coerce_attendance_summary(results)
    prototype2_output = results.get("prototype2")
    prototype3_output = results.get("prototype3")

    included_modalities: List[str] = []

    if attendance_summary:
        included_modalities.append("attendance")
    if prototype2_output:
        included_modalities.append("narrative")
    if prototype3_output:
        included_modalities.append("speech")

    attendance = _safe_get_attendance_summary(attendance_summary)
    narrative = _safe_get_narrative_summary(prototype2_output)
    transcript = _safe_get_transcript_summary(prototype3_output)

    report_sections = _build_report_sections(
        attendance,
        narrative,
        transcript,
        included_modalities,
    )

    mel_draft_text = "\n\n".join(
        [
            "Integrated MEL Report",
            *[
                f"{_build_heading(section['title'])}\n{section['body']}"
                for section in report_sections
            ],
        ]
    ).strip()

    return {
        "title": "Integrated MEL Report",
        "included_modalities": included_modalities,
        "report_sections": report_sections,
        "mel_draft_text": mel_draft_text,
    }
