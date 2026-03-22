from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List
import json

from src.config import DATA_DIR


SUPPORTED_EXTENSIONS = {".txt", ".md"}


@dataclass
class LoadedNarrativeDocument:
    document_id: str
    source_name: str
    source_path: str
    text: str
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_stem(path: Path) -> str:
    return path.stem.strip().replace(" ", "_").replace("-", "_").lower()


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def validate_text_content(text: str, min_chars: int = 20) -> None:
    if not text:
        raise ValueError("Narrative file is empty.")
    if len(text.strip()) < min_chars:
        raise ValueError(
            f"Narrative file content is too short (minimum {min_chars} characters required)."
        )


def load_narrative_file(path: str | Path) -> LoadedNarrativeDocument:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {file_path.suffix}. "
            f"Supported types are: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    text = _read_text_file(file_path)
    validate_text_content(text)

    return LoadedNarrativeDocument(
        document_id=_safe_stem(file_path),
        source_name=file_path.name,
        source_path=str(file_path.resolve()),
        text=text,
        metadata={
            "file_name": file_path.name,
            "extension": file_path.suffix.lower(),
            "char_count": len(text),
            "line_count": len(text.splitlines()),
        },
    )


def load_narrative_folder(folder_path: str | Path) -> List[LoadedNarrativeDocument]:
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    files = sorted(
        [
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    )

    if not files:
        raise ValueError(
            f"No supported narrative files found in {folder}. "
            f"Expected one of: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    documents: List[LoadedNarrativeDocument] = []
    seen_ids = set()

    for file_path in files:
        doc = load_narrative_file(file_path)

        original_id = doc.document_id
        counter = 2
        while doc.document_id in seen_ids:
            doc.document_id = f"{original_id}_{counter}"
            counter += 1

        seen_ids.add(doc.document_id)
        documents.append(doc)

    return documents


def save_loaded_documents_manifest(
    documents: List[LoadedNarrativeDocument],
    output_path: str | Path
) -> Path:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "document_count": len(documents),
        "documents": [doc.to_dict() for doc in documents],
    }

    output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_file


def get_default_narrative_input_dir() -> Path:
    return DATA_DIR / "inputs" / "narratives"
