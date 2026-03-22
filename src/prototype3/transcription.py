from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

from faster_whisper import WhisperModel

from src.prototype3.audio_loader import AudioDocument


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    document_id: str
    source_name: str
    source_path: str
    full_text: str
    segments: List[TranscriptSegment]
    model_name: str

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "source_name": self.source_name,
            "source_path": self.source_path,
            "full_text": self.full_text,
            "segments": [asdict(s) for s in self.segments],
            "model_name": self.model_name,
        }


def load_whisper_model(model_size: str = "base") -> WhisperModel:
    """
    Loads a Whisper model.

    model_size options:
    - tiny
    - base
    - small
    - medium
    - large
    """
    return WhisperModel(model_size, compute_type="auto")


def transcribe_audio(
    audio_doc: AudioDocument,
    model: WhisperModel,
) -> TranscriptResult:
    segments, info = model.transcribe(audio_doc.source_path)

    segment_list: List[TranscriptSegment] = []
    full_text_parts: List[str] = []

    for segment in segments:
        seg = TranscriptSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text.strip(),
        )
        segment_list.append(seg)
        full_text_parts.append(seg.text)

    full_text = " ".join(full_text_parts)

    return TranscriptResult(
        document_id=audio_doc.document_id,
        source_name=audio_doc.source_name,
        source_path=audio_doc.source_path,
        full_text=full_text,
        segments=segment_list,
        model_name=str(model),
    )
