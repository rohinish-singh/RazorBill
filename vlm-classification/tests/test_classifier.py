import json
import io
import sys
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

import classify as classifier_cli
from src.classifier import CandidateClassifier, CandidateError, OUTPUT_FIELDS, StubVisionAdapter, validate_candidate
from src.client import post_incident
from src.ollama_adapter import OllamaVisionAdapter
from src.worker import BoundedClassifierWorker


class FakeAdapter:
    def __init__(self, response=None, error=None, entered=None, release=None):
        self.response = response
        self.error = error
        self.entered = entered
        self.release = release

    def analyze(self, image_paths, prompt):
        if self.entered:
            self.entered.set()
        if self.release:
            self.release.wait(2)
        if self.error:
            raise self.error
        return self.response


class ClassifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.frame = Path(self.temp.name) / "frame.jpg"
        self.frame.write_bytes(b"test image bytes")
        self.candidate = {
            "event_id": "evt-1", "camera_id": "CAM_01", "video_source_id": "video",
            "timestamp_seconds": 2.5, "frame_path": str(self.frame), "frame_paths": [],
            "tracks": [], "trigger": "sampled_frame", "created_at": "2026-10-15T10:00:00Z",
        }

    def test_valid_candidate_and_successful_vlm(self):
        response = json.dumps({"category": "person_down", "summary": "A person is on the floor.",
                               "evidence_notes": "A person-shaped figure is horizontal on the floor."})
        result = CandidateClassifier(FakeAdapter(response)).classify_candidate(self.candidate)
        self.assertEqual(set(result), OUTPUT_FIELDS)
        self.assertEqual(result["category"], "person_down")
        self.assertEqual(result["status"], "classified")
        self.assertIsNone(result["confidence"])

    def test_missing_required_field(self):
        bad = dict(self.candidate)
        del bad["event_id"]
        with self.assertRaisesRegex(CandidateError, "event_id"):
            CandidateClassifier().classify_candidate(bad)

    def test_invalid_event_id_is_rejected(self):
        for event_id in ("", "   ", None, 42):
            with self.subTest(event_id=event_id):
                with self.assertRaises(CandidateError):
                    validate_candidate(dict(self.candidate, event_id=event_id))

    def test_non_finite_timestamps_are_rejected(self):
        for timestamp in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(timestamp=timestamp):
                with self.assertRaisesRegex(CandidateError, "finite"):
                    validate_candidate(dict(self.candidate, timestamp_seconds=timestamp))

    def test_invalid_track_structure_is_rejected(self):
        invalid_tracks = [
            ["person"],
            [{"track_id": 1, "class_name": "person"}],
            [{"track_id": "", "class_name": "person", "bbox_xyxy": [0, 0, 1, 1]}],
            [{"track_id": "   ", "class_name": "person", "bbox_xyxy": [0, 0, 1, 1]}],
            [{"track_id": True, "class_name": "person", "bbox_xyxy": [0, 0, 1, 1]}],
            [{"track_id": 1, "class_name": "person", "bbox_xyxy": [0, 0, float("nan"), 1]}],
        ]
        for tracks in invalid_tracks:
            with self.subTest(tracks=tracks):
                with self.assertRaises(CandidateError):
                    validate_candidate(dict(self.candidate, tracks=tracks))

    def test_valid_track_shape_is_accepted(self):
        valid = dict(self.candidate, tracks=[{
            "track_id": 12, "class_name": "person", "bbox_xyxy": [120, 80, 260, 410],
        }])
        self.assertIs(validate_candidate(valid), valid)

    def test_string_track_id_is_accepted(self):
        valid = dict(self.candidate, tracks=[{
            "track_id": "track-alpha", "class_name": "person", "bbox_xyxy": [120, 80, 260, 410],
        }])
        self.assertIs(validate_candidate(valid), valid)

    def test_person1_synthetic_track_id_is_accepted(self):
        valid = dict(self.candidate, tracks=[{
            "track_id": "synthetic-1", "class_name": "person", "bbox_xyxy": [120, 80, 260, 410],
        }])
        self.assertIs(validate_candidate(valid), valid)

    def test_missing_frame_path_field_is_rejected_even_with_frame_paths(self):
        bad = dict(self.candidate)
        bad.pop("frame_path")
        bad["frame_paths"] = [str(self.frame)]
        with self.assertRaisesRegex(CandidateError, "frame_path"):
            validate_candidate(bad)

    def test_missing_frame(self):
        bad = dict(self.candidate, frame_path=str(Path(self.temp.name) / "missing.jpg"))
        result = CandidateClassifier().classify_candidate(bad)
        self.assertEqual(result["status"], "failed")

    def test_repository_relative_frame_resolves_from_explicit_root_and_is_preserved(self):
        root = Path(self.temp.name)
        relative = Path("data") / "frames" / "frame.jpg"
        target = root / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(b"test image bytes")
        candidate = dict(self.candidate, frame_path=relative.as_posix())
        result = CandidateClassifier(StubVisionAdapter(), frame_root=root).classify_candidate(candidate)
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["frame_path"], relative.as_posix())

    def test_malformed_model_json(self):
        result = CandidateClassifier(FakeAdapter("not json")).classify_candidate(self.candidate)
        self.assertEqual((result["category"], result["status"]), ("unknown", "needs_review"))

    def test_invalid_category(self):
        response = json.dumps({"category": "weapon", "summary": "x", "evidence_notes": "y"})
        result = CandidateClassifier(FakeAdapter(response)).classify_candidate(self.candidate)
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["category"], "unknown")

    def test_unavailable_ollama(self):
        adapter = OllamaVisionAdapter(base_url="http://127.0.0.1:1", timeout_seconds=0.2)
        result = CandidateClassifier(adapter).classify_candidate(self.candidate)
        self.assertEqual(result["status"], "failed")
        self.assertIn("Ollama", result["evidence_notes"])

    def test_oversized_image_returns_failed_record(self):
        adapter = OllamaVisionAdapter(max_total_image_bytes=2)
        result = CandidateClassifier(adapter).classify_candidate(self.candidate)
        self.assertEqual(result["status"], "failed")
        self.assertIn("limit", result["evidence_notes"])

    def test_ollama_request_enables_json_format(self):
        response = io.BytesIO(b'{"message":{"content":"{}"}}')
        adapter = OllamaVisionAdapter()
        with patch("src.ollama_adapter.urlopen", return_value=response) as mocked_urlopen:
            adapter.analyze([self.frame], "return json")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(json.loads(request.data)["format"], "json")

    def test_invalid_candidate_cannot_be_posted_by_cli(self):
        bad_path = Path(self.temp.name) / "invalid.json"
        bad = dict(self.candidate)
        bad.pop("event_id")
        bad_path.write_text(json.dumps(bad), encoding="utf-8")
        with patch.object(sys, "argv", ["classify.py", str(bad_path), "--post"]):
            with patch.object(classifier_cli, "post_incident") as post:
                self.assertEqual(classifier_cli.main(), 2)
                post.assert_not_called()

    def test_post_client_rejects_invalid_incident(self):
        with self.assertRaises(ValueError):
            post_incident({"event_id": "unknown-event"})

    def test_post_client_rejects_empty_incident_id(self):
        incident = CandidateClassifier(StubVisionAdapter()).classify_candidate(self.candidate)
        incident["event_id"] = " "
        with self.assertRaisesRegex(ValueError, "event_id"):
            post_incident(incident)

    def test_timeout(self):
        result = CandidateClassifier(FakeAdapter(error=TimeoutError("timed out"))).classify_candidate(self.candidate)
        self.assertEqual(result["status"], "failed")
        self.assertIn("timed out", result["evidence_notes"])

    def test_overload_is_bounded(self):
        entered, release = Event(), Event()
        classifier = CandidateClassifier(FakeAdapter(
            json.dumps({"category": "other", "summary": "Something is visible.", "evidence_notes": "Visible scene."}),
            entered=entered, release=release,
        ))
        worker = BoundedClassifierWorker(classifier, max_workers=1, max_pending=0)
        self.addCleanup(lambda: worker.shutdown(wait=True))
        first = worker.submit(self.candidate)
        self.assertTrue(entered.wait(1))
        dropped = worker.try_submit(self.candidate)
        self.assertIsNone(dropped)
        self.assertEqual(worker.rejected_count, 1)
        release.set()
        self.assertEqual(first.result(timeout=2)["status"], "classified")

    def test_ambiguous_classification(self):
        response = json.dumps({"category": "unknown", "summary": "The event is unclear.",
                               "evidence_notes": "The frame does not show enough detail."})
        result = CandidateClassifier(FakeAdapter(response)).classify_candidate(self.candidate)
        self.assertEqual(result["status"], "needs_review")

    def test_successful_stub_classification(self):
        result = CandidateClassifier(StubVisionAdapter()).classify_candidate(self.candidate)
        self.assertEqual(result["category"], "unknown")
        self.assertEqual(result["status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
