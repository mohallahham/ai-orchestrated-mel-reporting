from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)

if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)


if "cv2" not in sys.modules:
    cv2_stub = types.ModuleType("cv2")
    cv2_stub.COLOR_GRAY2BGR = 0
    cv2_stub.cvtColor = lambda image, _: image
    cv2_stub.line = lambda *args, **kwargs: None
    cv2_stub.imwrite = lambda *args, **kwargs: True
    sys.modules["cv2"] = cv2_stub

if "easyocr" not in sys.modules:
    easyocr_stub = types.ModuleType("easyocr")

    class _Reader:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def readtext(self, *args, **kwargs) -> list:
            return []

    easyocr_stub.Reader = _Reader
    sys.modules["easyocr"] = easyocr_stub

if "faster_whisper" not in sys.modules:
    faster_whisper_stub = types.ModuleType("faster_whisper")

    class _WhisperModel:
        def __init__(self, *args, **kwargs) -> None:
            pass

    faster_whisper_stub.WhisperModel = _WhisperModel
    sys.modules["faster_whisper"] = faster_whisper_stub


from src.orchestration.orchestrator import run_orchestrated_pipeline
from src.prototype1.pipeline import run_prototype1_pipeline
from src.prototype2.pipeline import run_prototype2_pipeline
from src.prototype3.pipeline import run_prototype3_pipeline


class FakeSerializable:
    def __init__(self, payload: dict):
        self.payload = payload

    def to_dict(self) -> dict:
        return dict(self.payload)


class FakeSynthesisResult:
    def __init__(self) -> None:
        self.draft_text = "Draft report text"
        self.summary = {
            "section_count": 2,
            "grounded_section_count": 1,
            "ungrounded_section_count": 1,
        }

    def to_dict(self) -> dict:
        return {
            "sections": {
                "activities": {
                    "title": "Activities Implemented",
                    "narrative_text": "Activity text",
                    "evidence_count": 1,
                    "source_chunk_ids": ["chunk-1"],
                    "source_documents": ["report_01.txt"],
                    "metadata": {"grounded": True},
                },
                "outcomes": {
                    "title": "Observed Outcomes",
                    "narrative_text": "Outcome text",
                    "evidence_count": 0,
                    "source_chunk_ids": [],
                    "source_documents": [],
                    "metadata": {"grounded": False},
                },
            },
            "draft_text": self.draft_text,
            "summary": dict(self.summary),
        }


class PipelineContractTests(unittest.TestCase):
    def test_prototype1_pipeline_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            (input_dir / "form_01.png").write_bytes(b"img")
            (input_dir / "form_02.jpg").write_bytes(b"img")

            with patch(
                "src.prototype1.pipeline.run_extraction_pipeline",
                side_effect=[
                    {"records": [1, 2], "summary": {"count": 2}, "run_path": "run-a"},
                    {"records": [1], "summary": {"count": 1}, "run_path": "run-b"},
                ],
            ):
                result = run_prototype1_pipeline(input_dir)

        self.assertEqual(result["metadata"]["prototype"], "prototype1")
        self.assertEqual(result["metadata"]["form_count"], 2)
        self.assertEqual(result["metadata"]["successful_forms"], 2)
        self.assertEqual(result["metadata"]["total_records"], 3)
        self.assertIn("runs", result)
        self.assertIn("ui_summary", result)
        self.assertEqual(result["ui_summary"]["metadata"], result["metadata"])
        self.assertEqual(result["ui_summary"]["runs"], result["runs"])

    def test_prototype2_pipeline_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "prototype2_run_001"

            fake_documents = [FakeSerializable({"document_id": "doc-1"})]
            fake_chunks = [FakeSerializable({"chunk_id": "chunk-1"})]
            fake_routed_chunks = [FakeSerializable({"chunk_id": "chunk-1", "category": "activities"})]
            fake_bundle = FakeSerializable(
                {
                    "summary": {
                        "evidence_counts_by_category": {
                            "activities": 1,
                            "outcomes": 0,
                            "challenges": 0,
                            "lessons_learned": 0,
                            "other": 0,
                        }
                    }
                }
            )
            fake_synthesis = FakeSynthesisResult()

            with patch("src.prototype2.pipeline.make_run_dir", return_value=str(run_dir)), \
                 patch("src.prototype2.pipeline.load_narrative_folder", return_value=fake_documents), \
                 patch("src.prototype2.pipeline.chunk_documents_by_paragraph", return_value=fake_chunks), \
                 patch("src.prototype2.pipeline.route_chunks", return_value=fake_routed_chunks), \
                 patch("src.prototype2.pipeline.build_evidence_bundle", return_value=fake_bundle), \
                 patch("src.prototype2.pipeline.synthesize_sections", return_value=fake_synthesis):
                result = run_prototype2_pipeline(input_dir=Path(tmpdir))

        self.assertEqual(result["metadata"]["prototype"], "prototype2")
        self.assertEqual(result["run_dir"], str(run_dir))
        self.assertIn("documents", result)
        self.assertIn("ui_summary", result)
        self.assertEqual(result["ui_summary"]["metadata"], result["metadata"])
        self.assertEqual(result["ui_summary"]["run_dir"], result["run_dir"])
        self.assertIn("output_paths", result["ui_summary"])
        self.assertEqual(result["ui_summary"]["draft_text"], "Draft report text")

    def test_prototype3_pipeline_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "prototype3_run_001"
            fake_audio_docs = [FakeSerializable({"document_id": "audio-1"})]
            fake_transcript = FakeSerializable(
                {
                    "document_id": "audio-1",
                    "full_text": "Transcript body",
                }
            )
            fake_transcript.full_text = "Transcript body"

            with patch("src.prototype3.pipeline.make_run_dir", return_value=str(run_dir)), \
                 patch("src.prototype3.pipeline.load_audio_folder", return_value=fake_audio_docs), \
                 patch("src.prototype3.pipeline.load_whisper_model", return_value=object()), \
                 patch("src.prototype3.pipeline.transcribe_audio", return_value=fake_transcript):
                result = run_prototype3_pipeline(input_dir=Path(tmpdir))

        self.assertEqual(result["metadata"]["prototype"], "prototype3")
        self.assertEqual(result["run_dir"], str(run_dir))
        self.assertIn("transcripts", result)
        self.assertEqual(result["ui_summary"]["metadata"], result["metadata"])
        self.assertEqual(result["ui_summary"]["run_dir"], result["run_dir"])
        self.assertEqual(result["ui_summary"]["document_count"], 1)
        self.assertIn("output_paths", result["ui_summary"])

    def test_orchestrated_pipeline_contract(self) -> None:
        p1_output = {
            "metadata": {"prototype": "prototype1"},
            "ui_summary": {"metadata": {"prototype": "prototype1"}},
            "runs": [],
        }
        p2_output = {
            "metadata": {"prototype": "prototype2"},
            "ui_summary": {"metadata": {"prototype": "prototype2"}},
            "run_dir": "run-p2",
        }
        p3_output = {
            "metadata": {"prototype": "prototype3"},
            "ui_summary": {"metadata": {"prototype": "prototype3"}},
            "transcripts": [type("Transcript", (), {"full_text": "transcribed text"})()],
            "run_dir": "run-p3",
        }
        attendance_summary = {"total_records": 4}
        mel_draft = {
            "mel_draft_text": "Integrated MEL Report",
            "report_sections": [
                {"title": "Executive Summary", "body": "Summary body"},
            ],
        }

        with patch("src.orchestration.orchestrator.run_prototype1_pipeline", return_value=p1_output), \
             patch("src.orchestration.orchestrator.run_prototype2_pipeline", return_value=p2_output), \
             patch("src.orchestration.orchestrator.run_prototype3_pipeline", return_value=p3_output), \
             patch("src.orchestration.orchestrator.create_narrative_input_from_texts", return_value="generated-dir"), \
             patch("src.orchestration.orchestrator.extract_attendance_summary", return_value=attendance_summary), \
             patch("src.orchestration.orchestrator.build_integrated_mel_draft", return_value=mel_draft), \
             patch("src.orchestration.orchestrator.save_orchestration_output") as save_output:
            result = run_orchestrated_pipeline(
                document_input_dir="forms",
                narrative_input_dir="narratives",
                audio_input_dir="audio",
                run_id="run-123",
                p1_mode="ocr",
            )

        self.assertEqual(result["metadata"]["prototype"], "orchestration")
        self.assertEqual(result["metadata"]["run_id"], "run-123")
        self.assertEqual(result["ui_summary"]["metadata"], result["metadata"])
        self.assertEqual(result["ui_summary"]["included_modalities"], ["prototype1", "prototype2", "prototype3"])
        self.assertTrue(result["ui_summary"]["has_attendance_summary"])
        self.assertTrue(result["ui_summary"]["has_mel_draft"])
        self.assertEqual(result["prototype1"], p1_output)
        self.assertEqual(result["prototype2"], p2_output)
        self.assertEqual(result["prototype3"], p3_output)
        self.assertEqual(result["attendance_summary"], attendance_summary)
        self.assertEqual(result["mel_draft"], mel_draft)
        save_output.assert_called_once_with("run-123", {
            "prototype3": p3_output,
            "prototype1": p1_output,
            "attendance_summary": attendance_summary,
            "prototype2": p2_output,
            "mel_draft": mel_draft,
        })

    def test_integrated_mel_draft_structure(self) -> None:
        from src.orchestration.mel_draft_builder import build_integrated_mel_draft

        results = {
            "attendance_summary": {
                "form_count": 2,
                "successful_forms": 2,
                "total_records": 15,
                "per_form_summaries": [
                    {"image_name": "form_a.png", "record_count": 10},
                    {"image_name": "form_b.png", "record_count": 5},
                ],
            },
            "prototype2": {
                "ui_summary": {
                    "sections": [
                        {
                            "category": "activities",
                            "title": "Activities Implemented",
                            "narrative_text": "Two field visits were completed.",
                            "evidence_count": 2,
                            "source_documents": ["report_01.txt"],
                            "source_chunk_ids": ["chunk-1"],
                            "grounded": True,
                        },
                        {
                            "category": "outcomes",
                            "title": "Observed Outcomes",
                            "narrative_text": "Community participation improved.",
                            "evidence_count": 1,
                            "source_documents": ["report_02.txt"],
                            "source_chunk_ids": ["chunk-2"],
                            "grounded": True,
                        },
                    ]
                }
            },
            "prototype3": {
                "ui_summary": {
                    "document_count": 1,
                    "transcript_preview": "Participants reported positive feedback.",
                }
            },
        }

        mel_draft = build_integrated_mel_draft(results)

        self.assertEqual(mel_draft["title"], "Integrated MEL Report")
        self.assertEqual(
            mel_draft["included_modalities"],
            ["attendance", "narrative", "speech"],
        )
        self.assertEqual(
            [section["title"] for section in mel_draft["report_sections"]],
            [
                "Executive Summary",
                "Key Findings",
                "Participation and Attendance",
                "Narrative Findings",
                "Audio and Field Context",
                "Data Quality and Limitations",
                "Suggested Follow-up Actions",
                "Data Coverage Note",
            ],
        )
        self.assertIn("15 participant record(s)", mel_draft["mel_draft_text"])
        self.assertIn("Community participation improved.", mel_draft["mel_draft_text"])
        self.assertIn("Participants reported positive feedback.", mel_draft["mel_draft_text"])
        self.assertIn("Verify attendance counts, ages, and gender labels", mel_draft["mel_draft_text"])
        self.assertIn("Included modalities: attendance, narrative, speech.", mel_draft["mel_draft_text"])


if __name__ == "__main__":
    unittest.main()
