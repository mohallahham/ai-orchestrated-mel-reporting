"""Coordinate the prototype pipelines and build an integrated MEL output."""

from typing import Optional, Dict, Any

from src.pipeline_contracts import build_pipeline_result
from src.prototype1.pipeline import (
    run_prototype1_pipeline,
    run_prototype1_vision_pipeline,
)
from src.prototype2.pipeline import run_prototype2_pipeline
from src.prototype3.pipeline import run_prototype3_pipeline

from src.orchestration.output_writer import save_orchestration_output
from src.orchestration.adapters.narrative_adapter import create_narrative_input_from_texts
from src.orchestration.adapters.attendance_adapter import extract_attendance_summary
from src.orchestration.mel_draft_builder import build_integrated_mel_draft


def run_orchestrated_pipeline(
    document_input_dir: Optional[str] = None,
    narrative_input_dir: Optional[str] = None,
    audio_input_dir: Optional[str] = None,
    run_id: Optional[str] = None,
    p1_mode: str = "ocr",
) -> Dict[str, Any]:
    """Run the orchestration workflow across the available modalities."""

    artifacts: Dict[str, Any] = {}

    # --------------------------------------------------
    # Prototype 3 → optional transcript generation
    # --------------------------------------------------
    generated_narrative_input_dir: Optional[str] = None

    if audio_input_dir:
        p3_output = run_prototype3_pipeline(
            input_dir=audio_input_dir,
        )
        artifacts["prototype3"] = p3_output

        transcripts = p3_output.get("transcripts", [])
        transcript_texts = []

        for t in transcripts:
            if hasattr(t, "full_text") and t.full_text:
                transcript_texts.append(t.full_text)

        if transcript_texts:
            generated_dir = f"data/inputs/generated_from_audio_{run_id or 'temp'}"
            generated_narrative_input_dir = create_narrative_input_from_texts(
                texts=transcript_texts,
                output_dir=generated_dir,
            )

    # --------------------------------------------------
    # Prototype 1 → OCR or Vision
    # --------------------------------------------------
    if document_input_dir:
        if p1_mode == "vision":
            p1_output = run_prototype1_vision_pipeline(
                input_dir=document_input_dir,
            )
        else:
            p1_output = run_prototype1_pipeline(
                input_dir=document_input_dir,
            )

        artifacts["prototype1"] = p1_output

        # Structured attendance summary applies only to OCR mode
        if p1_mode == "ocr":
            attendance_summary = extract_attendance_summary(p1_output)
            artifacts["attendance_summary"] = attendance_summary

    # --------------------------------------------------
    # Prototype 2 → Narrative synthesis
    # Priority:
    # 1. explicit narrative_input_dir from user upload/input
    # 2. generated transcript-derived narrative dir
    # --------------------------------------------------
    effective_narrative_input_dir = narrative_input_dir or generated_narrative_input_dir

    if effective_narrative_input_dir:
        p2_output = run_prototype2_pipeline(
            input_dir=effective_narrative_input_dir,
        )
        artifacts["prototype2"] = p2_output

    # --------------------------------------------------
    # Build integrated MEL draft
    # --------------------------------------------------
    mel_draft = build_integrated_mel_draft(artifacts)
    artifacts["mel_draft"] = mel_draft

    included_modalities = [
        name for name in ["prototype1", "prototype2", "prototype3"]
        if name in artifacts
    ]

    metadata = {
        "prototype": "orchestration",
        "run_id": run_id,
        "p1_mode": p1_mode,
        "included_modalities": included_modalities,
    }

    # --------------------------------------------------
    # Save orchestration output
    # --------------------------------------------------
    if run_id:
        save_orchestration_output(run_id, artifacts)

    return build_pipeline_result(
        metadata,
        artifacts=artifacts,
        included_modalities=included_modalities,
        has_attendance_summary="attendance_summary" in artifacts,
        has_mel_draft=bool(mel_draft.get("mel_draft_text")),
    )
