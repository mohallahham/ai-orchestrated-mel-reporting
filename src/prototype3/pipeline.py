from __future__ import annotations

from pathlib import Path
import json

from src.prototype3.audio_loader import (
    load_audio_folder,
    get_default_audio_input_dir,
)
from src.prototype3.transcription import (
    load_whisper_model,
    transcribe_audio,
)
from src.pipeline_contracts import build_pipeline_result
from src.utils import make_run_dir


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_prototype3_pipeline(input_dir: str | Path | None = None) -> dict:
    input_dir = Path(input_dir) if input_dir else get_default_audio_input_dir()
    run_dir = Path(make_run_dir(prefix="prototype3_run"))

    audio_docs = load_audio_folder(input_dir)

    model = load_whisper_model("base")

    transcript_results = []

    for doc in audio_docs:
        result = transcribe_audio(doc, model)
        transcript_results.append(result)

    transcripts_payload = {
        "document_count": len(transcript_results),
        "transcripts": [t.to_dict() for t in transcript_results],
    }

    # Save outputs
    _write_json(run_dir / "transcripts.json", transcripts_payload)

    full_text_combined = "\n\n".join([t.full_text for t in transcript_results])
    _write_text(run_dir / "transcript.txt", full_text_combined)

    metadata = {
        "prototype": "prototype3",
        "input_dir": str(input_dir.resolve()),
        "run_dir": str(run_dir.resolve()),
        "document_count": len(transcript_results),
        "model": "faster-whisper-base",
        "output_files": [
            "transcripts.json",
            "transcript.txt",
            "metadata.json",
        ],
    }

    _write_json(run_dir / "metadata.json", metadata)

    output_paths = {
            "transcripts_json": str(run_dir / "transcripts.json"),
            "transcript_txt": str(run_dir / "transcript.txt"),
            "metadata_json": str(run_dir / "metadata.json"),
    }

    return build_pipeline_result(
        metadata,
        run_dir=str(run_dir),
        output_paths=output_paths,
        artifacts={"transcripts": transcript_results},
        transcript_preview=full_text_combined[:1000],
        document_count=len(transcript_results),
    )
