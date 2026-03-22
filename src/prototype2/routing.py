from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from src.prototype2.chunking import NarrativeChunk


ROUTING_CATEGORIES = [
    "activities",
    "outcomes",
    "challenges",
    "lessons_learned",
    "other",
]


CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "activities": [
        "activity",
        "activities",
        "session",
        "training",
        "workshop",
        "meeting",
        "outreach",
        "facilitation",
        "event",
    ],
    "outcomes": [
        "result",
        "results",
        "outcome",
        "outcomes",
        "improved",
        "engagement",
        "interest",
        "participation",
        "successfully",
        "attended",
        "requested",
        "effective",
    ],
    "challenges": [
        "challenge",
        "challenges",
        "problem",
        "problems",
        "issue",
        "issues",
        "delay",
        "delays",
        "weak",
        "limited",
        "affected",
        "difficulty",
        "difficulties",
    ],
    "lessons_learned": [
        "learned",
        "lesson",
        "lessons",
        "noted",
        "future",
        "should be retained",
        "should be addressed",
        "more effective",
    ],
}


CATEGORY_PRIORITY = {
    "lessons_learned": 4,
    "challenges": 3,
    "outcomes": 2,
    "activities": 1,
    "other": 0,
}


PRIORITY_PHRASES: Dict[str, List[str]] = {
    "lessons_learned": [
        "the team learned",
        "lessons learned",
        "should be retained",
        "more effective than",
    ],
    "challenges": [
        "key challenge",
        "affected comprehension",
        "limited time",
    ],
}


@dataclass
class RoutedChunk:
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


def _normalise_text(text: str) -> str:
    return text.lower().strip()


def _find_keyword_matches(text: str) -> Dict[str, List[str]]:
    normalised_text = _normalise_text(text)
    matches: Dict[str, List[str]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        matched = [keyword for keyword in keywords if keyword in normalised_text]
        if matched:
            matches[category] = matched

    return matches


def _check_priority_phrase_override(text: str) -> tuple[str | None, List[str]]:
    normalised_text = _normalise_text(text)

    for category, phrases in PRIORITY_PHRASES.items():
        matched_phrases = [phrase for phrase in phrases if phrase in normalised_text]
        if matched_phrases:
            return category, matched_phrases

    return None, []


def _resolve_best_category(matches: Dict[str, List[str]]) -> tuple[str, List[str]]:
    if not matches:
        return "other", []

    ranked_matches = sorted(
        matches.items(),
        key=lambda item: (
            len(item[1]),
            CATEGORY_PRIORITY.get(item[0], 0),
        ),
        reverse=True,
    )
    return ranked_matches[0][0], ranked_matches[0][1]


def route_chunk(chunk: NarrativeChunk) -> RoutedChunk:
    override_category, override_matches = _check_priority_phrase_override(chunk.text)

    if override_category is not None:
        assigned_category = override_category
        matched_keywords = override_matches
        routing_method = "hybrid_keyword_priority_override"
    else:
        matches = _find_keyword_matches(chunk.text)
        assigned_category, matched_keywords = _resolve_best_category(matches)
        routing_method = "hybrid_keyword_scoring"

    return RoutedChunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        source_name=chunk.source_name,
        source_path=chunk.source_path,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        assigned_category=assigned_category,
        matched_keywords=matched_keywords,
        routing_method=routing_method,
        metadata={
            "char_count": chunk.metadata.get("char_count", len(chunk.text)),
            "word_count": chunk.metadata.get("word_count", len(chunk.text.split())),
        },
    )


def route_chunks(chunks: List[NarrativeChunk]) -> List[RoutedChunk]:
    return [route_chunk(chunk) for chunk in chunks]
