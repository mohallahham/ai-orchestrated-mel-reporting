from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class AttendanceRecord:
    row_id: int
    gender_raw: str
    gender_label: str
    gender_confidence: float
    age_raw: str
    age_value: Optional[int]
    age_confidence: float
    validation_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NarrativeEvidenceItem:
    label: str
    source: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TranscriptSegment:
    start: Optional[float]
    end: Optional[float]
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunMetadata:
    run_id: str
    prototype_name: str
    timestamp: str
    input_files: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)