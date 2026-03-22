"""Prepare uploaded files in a run-scoped directory structure."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any, Iterable


def _safe_filename(name: str) -> str:
    return Path(name).name.replace(" ", "_")


def _write_uploaded_files(files: Iterable[Any], target_dir: Path) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[str] = []

    for uploaded_file in files:
        if uploaded_file is None:
            continue

        filename = _safe_filename(getattr(uploaded_file, "name", "uploaded_file"))
        output_path = target_dir / filename

        file_bytes = uploaded_file.getbuffer()
        output_path.write_bytes(file_bytes)

        saved_paths.append(str(output_path))

    return saved_paths


def _write_uploaded_texts(files: Iterable[Any], target_dir: Path) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[str] = []

    for uploaded_file in files:
        if uploaded_file is None:
            continue

        original_name = _safe_filename(getattr(uploaded_file, "name", "uploaded_text.txt"))
        stem = Path(original_name).stem
        output_name = f"{stem}.txt"
        output_path = target_dir / output_name

        raw = uploaded_file.getvalue()

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")

        output_path.write_text(text, encoding="utf-8")
        saved_paths.append(str(output_path))

    return saved_paths


def prepare_uploaded_inputs(
    run_id: str,
    form_files: Iterable[Any] | None = None,
    narrative_files: Iterable[Any] | None = None,
    audio_files: Iterable[Any] | None = None,
    clear_existing: bool = True,
) -> dict:
    """
    Save uploaded files into run-scoped input folders.

    Args:
        run_id: orchestration run id
        form_files: uploaded image files for Prototype 1
        narrative_files: uploaded text files for Prototype 2
        audio_files: uploaded audio files for Prototype 3

    Returns:
        dict containing prepared directory paths and saved file lists
    """
    base_dir = Path("data/inputs/uploads") / run_id

    if clear_existing and base_dir.exists():
        shutil.rmtree(base_dir)

    forms_dir = base_dir / "forms"
    narratives_dir = base_dir / "narratives"
    audio_dir = base_dir / "audio"

    saved_forms = _write_uploaded_files(form_files or [], forms_dir) if form_files else []
    saved_narratives = (
        _write_uploaded_texts(narrative_files or [], narratives_dir)
        if narrative_files else []
    )
    saved_audio = _write_uploaded_files(audio_files or [], audio_dir) if audio_files else []

    return {
        "base_dir": str(base_dir),
        "document_input_dir": str(forms_dir) if saved_forms else None,
        "narrative_input_dir": str(narratives_dir) if saved_narratives else None,
        "audio_input_dir": str(audio_dir) if saved_audio else None,
        "saved_files": {
            "forms": saved_forms,
            "narratives": saved_narratives,
            "audio": saved_audio,
        },
    }
