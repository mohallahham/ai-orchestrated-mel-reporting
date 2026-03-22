from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

from src.prototype2.loader import LoadedNarrativeDocument


@dataclass
class NarrativeChunk:
    chunk_id: str
    document_id: str
    source_name: str
    source_path: str
    chunk_index: int
    text: str
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _split_into_paragraphs(text: str) -> List[str]:
    parts = [part.strip() for part in text.split("\n\n")]
    return [part for part in parts if part]


def chunk_document_by_paragraph(
    document: LoadedNarrativeDocument,
    min_chars: int = 20
) -> List[NarrativeChunk]:
    paragraphs = _split_into_paragraphs(document.text)

    chunks: List[NarrativeChunk] = []
    for idx, paragraph in enumerate(paragraphs, start=1):
        if len(paragraph.strip()) < min_chars:
            continue

        chunk = NarrativeChunk(
            chunk_id=f"{document.document_id}_chunk_{idx:02d}",
            document_id=document.document_id,
            source_name=document.source_name,
            source_path=document.source_path,
            chunk_index=idx,
            text=paragraph,
            metadata={
                "char_count": len(paragraph),
                "word_count": len(paragraph.split()),
            },
        )
        chunks.append(chunk)

    return chunks


def chunk_documents_by_paragraph(
    documents: List[LoadedNarrativeDocument],
    min_chars: int = 20
) -> List[NarrativeChunk]:
    all_chunks: List[NarrativeChunk] = []

    for document in documents:
        document_chunks = chunk_document_by_paragraph(document, min_chars=min_chars)
        all_chunks.extend(document_chunks)

    return all_chunks
