from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List


SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}


@dataclass
class AudioDocument:
    document_id: str
    source_name: str
    source_path: str
    file_size_bytes: int
    extension: str

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_audio_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format: {path.suffix}. "
            f"Supported formats: {sorted(SUPPORTED_AUDIO_EXTENSIONS)}"
        )


def load_audio_file(path: str | Path) -> AudioDocument:
    path = Path(path)

    _validate_audio_file(path)

    return AudioDocument(
        document_id=path.stem,
        source_name=path.name,
        source_path=str(path.resolve()),
        file_size_bytes=path.stat().st_size,
        extension=path.suffix.lower(),
    )


def load_audio_folder(folder_path: str | Path) -> List[AudioDocument]:
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Audio folder not found: {folder}")

    audio_files = sorted(
        [
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ]
    )

    if not audio_files:
        raise ValueError(
            f"No supported audio files found in {folder}. "
            f"Supported formats: {sorted(SUPPORTED_AUDIO_EXTENSIONS)}"
        )

    documents = []

    for path in audio_files:
        doc = load_audio_file(path)
        documents.append(doc)

    return documents


def get_default_audio_input_dir() -> Path:
    return Path("data/inputs/audio")
