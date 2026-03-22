from __future__ import annotations

from pathlib import Path
import json

from src.prototype2.loader import (
    get_default_narrative_input_dir,
    load_narrative_folder,
)
from src.prototype2.chunking import chunk_documents_by_paragraph
from src.prototype2.routing import route_chunks
from src.prototype2.evidence_builder import build_evidence_bundle
from src.pipeline_contracts import build_pipeline_result
from src.prototype2.synthesis import synthesize_sections
from src.utils import make_run_dir


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _build_ui_summary_fields(
    run_dir: Path,
    synthesis_payload: dict,
    evidence_payload: dict,
) -> tuple[list[dict], dict[str, str]]:
    section_summaries = []

    for category, section in synthesis_payload["sections"].items():
        section_summaries.append(
            {
                "category": category,
                "title": section["title"],
                "narrative_text": section["narrative_text"],
                "evidence_count": section["evidence_count"],
                "source_chunk_ids": section["source_chunk_ids"],
                "source_documents": section["source_documents"],
                "grounded": section["metadata"]["grounded"],
            }
        )

    output_paths = {
        "metadata_json": str(run_dir / "metadata.json"),
        "loaded_documents_json": str(run_dir / "loaded_documents.json"),
        "chunks_json": str(run_dir / "chunks.json"),
        "routed_chunks_json": str(run_dir / "routed_chunks.json"),
        "evidence_bundle_json": str(run_dir / "evidence_bundle.json"),
        "synthesis_json": str(run_dir / "synthesis.json"),
        "draft_report_txt": str(run_dir / "draft_report.txt"),
    }

    return section_summaries, output_paths


def run_prototype2_pipeline(input_dir: str | Path | None = None) -> dict:
    narrative_input_dir = Path(input_dir) if input_dir else get_default_narrative_input_dir()
    run_dir = Path(make_run_dir(prefix="prototype2_run"))

    documents = load_narrative_folder(narrative_input_dir)
    chunks = chunk_documents_by_paragraph(documents)
    routed_chunks = route_chunks(chunks)
    evidence_bundle = build_evidence_bundle(routed_chunks)
    synthesis_result = synthesize_sections(evidence_bundle)

    documents_payload = {
        "document_count": len(documents),
        "documents": [doc.to_dict() for doc in documents],
    }

    chunks_payload = {
        "chunk_count": len(chunks),
        "chunks": [chunk.to_dict() for chunk in chunks],
    }

    routed_payload = {
        "routed_chunk_count": len(routed_chunks),
        "routed_chunks": [chunk.to_dict() for chunk in routed_chunks],
    }

    evidence_payload = evidence_bundle.to_dict()
    synthesis_payload = synthesis_result.to_dict()

    _write_json(run_dir / "loaded_documents.json", documents_payload)
    _write_json(run_dir / "chunks.json", chunks_payload)
    _write_json(run_dir / "routed_chunks.json", routed_payload)
    _write_json(run_dir / "evidence_bundle.json", evidence_payload)
    _write_json(run_dir / "synthesis.json", synthesis_payload)
    _write_text(run_dir / "draft_report.txt", synthesis_result.draft_text)

    metadata = {
        "prototype": "prototype2",
        "input_dir": str(narrative_input_dir.resolve()),
        "run_dir": str(run_dir.resolve()),
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "routed_chunk_count": len(routed_chunks),
        "section_count": synthesis_result.summary["section_count"],
        "grounded_section_count": synthesis_result.summary["grounded_section_count"],
        "ungrounded_section_count": synthesis_result.summary["ungrounded_section_count"],
        "output_files": [
            "loaded_documents.json",
            "chunks.json",
            "routed_chunks.json",
            "evidence_bundle.json",
            "synthesis.json",
            "draft_report.txt",
            "metadata.json",
        ],
    }

    _write_json(run_dir / "metadata.json", metadata)

    section_summaries, output_paths = _build_ui_summary_fields(
        run_dir=run_dir,
        synthesis_payload=synthesis_payload,
        evidence_payload=evidence_payload,
    )

    return build_pipeline_result(
        metadata,
        run_dir=str(run_dir),
        output_paths=output_paths,
        artifacts={
            "documents": documents,
            "chunks": chunks,
            "routed_chunks": routed_chunks,
            "evidence_bundle": evidence_bundle,
            "synthesis_result": synthesis_result,
        },
        draft_text=synthesis_payload["draft_text"],
        sections=section_summaries,
        evidence_counts_by_category=evidence_payload["summary"]["evidence_counts_by_category"],
    )
