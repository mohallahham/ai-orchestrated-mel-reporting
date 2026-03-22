from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from src.prototype2.routing import RoutedChunk, ROUTING_CATEGORIES


@dataclass
class EvidenceItem:
    chunk_id: str
    document_id: str
    source_name: str
    source_path: str
    chunk_index: int
    text: str
    assigned_category: str
    matched_keywords: List[str]
    routing_method: str
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CategoryEvidence:
    category: str
    evidence_items: List[EvidenceItem]
    evidence_count: int

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "evidence_items": [item.to_dict() for item in self.evidence_items],
            "evidence_count": self.evidence_count,
        }


@dataclass
class EvidenceBundle:
    categories: Dict[str, CategoryEvidence]
    summary: dict

    def to_dict(self) -> dict:
        return {
            "categories": {
                category: category_evidence.to_dict()
                for category, category_evidence in self.categories.items()
            },
            "summary": self.summary,
        }


def build_evidence_item(routed_chunk: RoutedChunk) -> EvidenceItem:
    return EvidenceItem(
        chunk_id=routed_chunk.chunk_id,
        document_id=routed_chunk.document_id,
        source_name=routed_chunk.source_name,
        source_path=routed_chunk.source_path,
        chunk_index=routed_chunk.chunk_index,
        text=routed_chunk.text,
        assigned_category=routed_chunk.assigned_category,
        matched_keywords=list(routed_chunk.matched_keywords),
        routing_method=routed_chunk.routing_method,
        metadata=dict(routed_chunk.metadata),
    )


def build_evidence_bundle(routed_chunks: List[RoutedChunk]) -> EvidenceBundle:
    grouped_items: Dict[str, List[EvidenceItem]] = {
        category: [] for category in ROUTING_CATEGORIES
    }

    for routed_chunk in routed_chunks:
        evidence_item = build_evidence_item(routed_chunk)
        category = routed_chunk.assigned_category

        if category not in grouped_items:
            grouped_items[category] = []

        grouped_items[category].append(evidence_item)

    category_map: Dict[str, CategoryEvidence] = {}
    for category, items in grouped_items.items():
        category_map[category] = CategoryEvidence(
            category=category,
            evidence_items=items,
            evidence_count=len(items),
        )

    summary = {
        "total_routed_chunks": len(routed_chunks),
        "categories_with_evidence": sum(
            1 for category_evidence in category_map.values()
            if category_evidence.evidence_count > 0
        ),
        "evidence_counts_by_category": {
            category: category_evidence.evidence_count
            for category, category_evidence in category_map.items()
        },
    }

    return EvidenceBundle(
        categories=category_map,
        summary=summary,
    )
