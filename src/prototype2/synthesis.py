from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from src.prototype2.evidence_builder import EvidenceBundle, EvidenceItem


SECTION_ORDER = [
    "activities",
    "outcomes",
    "challenges",
    "lessons_learned",
]


SECTION_TITLES = {
    "activities": "Activities Implemented",
    "outcomes": "Observed Outcomes",
    "challenges": "Challenges",
    "lessons_learned": "Lessons Learned",
}


@dataclass
class SynthesizedSection:
    category: str
    title: str
    narrative_text: str
    source_chunk_ids: List[str]
    source_documents: List[str]
    evidence_count: int
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SynthesisResult:
    sections: Dict[str, SynthesizedSection]
    draft_text: str
    summary: dict

    def to_dict(self) -> dict:
        return {
            "sections": {
                category: section.to_dict()
                for category, section in self.sections.items()
            },
            "draft_text": self.draft_text,
            "summary": self.summary,
        }


def _clean_sentence(text: str) -> str:
    return " ".join(text.strip().split())


def _build_section_text(category: str, evidence_items: List[EvidenceItem]) -> str:
    if not evidence_items:
        title = SECTION_TITLES.get(category, category.replace("_", " ").title())
        return f"No clear evidence was identified for the section: {title}."

    sentences = [_clean_sentence(item.text) for item in evidence_items]

    if category == "activities":
        intro = "The reviewed reports describe the following activities:"
    elif category == "outcomes":
        intro = "The reviewed reports indicate the following outcomes:"
    elif category == "challenges":
        intro = "The reviewed reports highlight the following challenges:"
    elif category == "lessons_learned":
        intro = "The reviewed reports suggest the following lessons learned:"
    else:
        intro = "The reviewed reports include the following points:"

    bullet_like_sentences = " ".join(f"- {sentence}" for sentence in sentences)
    return f"{intro} {bullet_like_sentences}"


def _unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    ordered = []

    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)

    return ordered


def synthesize_sections(evidence_bundle: EvidenceBundle) -> SynthesisResult:
    sections: Dict[str, SynthesizedSection] = {}

    for category in SECTION_ORDER:
        category_evidence = evidence_bundle.categories.get(category)
        evidence_items = category_evidence.evidence_items if category_evidence else []

        source_chunk_ids = [item.chunk_id for item in evidence_items]
        source_documents = _unique_preserve_order(
            [item.source_name for item in evidence_items]
        )

        section = SynthesizedSection(
            category=category,
            title=SECTION_TITLES[category],
            narrative_text=_build_section_text(category, evidence_items),
            source_chunk_ids=source_chunk_ids,
            source_documents=source_documents,
            evidence_count=len(evidence_items),
            metadata={
                "generated_from_category": category,
                "grounded": len(evidence_items) > 0,
            },
        )
        sections[category] = section

    draft_parts = []
    for category in SECTION_ORDER:
        section = sections[category]
        draft_parts.append(f"{section.title}\n{section.narrative_text}")

    draft_text = "\n\n".join(draft_parts)

    summary = {
        "section_count": len(sections),
        "grounded_section_count": sum(
            1 for section in sections.values() if section.metadata["grounded"]
        ),
        "ungrounded_section_count": sum(
            1 for section in sections.values() if not section.metadata["grounded"]
        ),
    }

    return SynthesisResult(
        sections=sections,
        draft_text=draft_text,
        summary=summary,
    )
