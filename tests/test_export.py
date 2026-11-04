"""Tests for transcript export formats."""

import json
import tempfile
import unittest
from pathlib import Path

from capture.export import export_session, read_timestamped_sentences


class TestTranscriptExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.timestamped = self.root / "timestamped_transcript.txt"
        self.timestamped.write_text(
            "[14:05:03] First sentence.\n[14:05:08] Second sentence.\n",
            encoding="utf-8",
        )
        self.metadata = {
            "session_id": "2026-11-04_14-05-00_123456",
            "name": "Test session",
            "started_at": "2026-11-04T14:05:00-05:00",
            "ended_at": "2026-11-04T14:05:12-05:00",
            "duration_seconds": 12.0,
            "status": "completed",
            "_directory": str(self.root),
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def export_file(self, extension):
        destination = self.root / f"export.{extension}"
        export_session(
            destination, extension, "First sentence.\n\nSecond sentence.",
            self.metadata, self.timestamped,
        )
        return destination.read_text(encoding="utf-8")

    def test_reads_timestamped_sentence_records(self):
        records = read_timestamped_sentences(self.timestamped)
        self.assertEqual(records, [
            {"time": "14:05:03", "text": "First sentence."},
            {"time": "14:05:08", "text": "Second sentence."},
        ])

    def test_txt_export_preserves_transcript(self):
        self.assertEqual(self.export_file("txt"), "First sentence.\n\nSecond sentence.")

    def test_markdown_export_includes_session_and_timestamps(self):
        content = self.export_file("md")
        self.assertIn("# Test session", content)
        self.assertIn("## Transcript", content)
        self.assertIn("`14:05:03`", content)

    def test_json_export_includes_metadata_and_timestamped_sentences(self):
        content = json.loads(self.export_file("json"))
        self.assertEqual(content["session"]["name"], "Test session")
        self.assertEqual(len(content["timestamped_sentences"]), 2)
        self.assertNotIn("_directory", content["session"])

    def test_srt_export_creates_subtitle_cues(self):
        content = self.export_file("srt")
        self.assertIn("00:00:03,000 --> 00:00:08,000", content)
        self.assertIn("First sentence.", content)
        self.assertIn("Second sentence.", content)

    def test_srt_requires_timestamped_sentences(self):
        empty = self.root / "empty.txt"
        empty.write_text("", encoding="utf-8")
        with self.assertRaises(ValueError):
            export_session(self.root / "empty.srt", "srt", "Text", self.metadata, empty)


if __name__ == "__main__":
    unittest.main()
