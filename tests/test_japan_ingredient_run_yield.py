import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import Collector


class CrawlerRunYieldDiagnostics(unittest.TestCase):
    def test_empty_bounded_run_reports_zero_yield(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.run([], max_pages=0, minutes=0)
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["new_accepted"], 0)
            self.assertEqual(summary["current_run"]["pages_processed"], 0)
            self.assertEqual(summary["current_run"]["top_rejection_reasons"], {})

    def test_rejection_histogram_is_run_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.run([], max_pages=0, minutes=0)
            collector.db.execute(
                "INSERT INTO observations VALUES(?,?,?)",
                ("https://example.invalid/test", "missing_or_ambiguous_ingredients",
                 datetime.now(timezone.utc).isoformat()),
            )
            collector.db.commit()
            collector.checkpoint()
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["pages_processed"], 1)
            self.assertEqual(summary["current_run"]["top_rejection_reasons"],
                             {"missing_or_ambiguous_ingredients": 1})

    def test_finalizer_preserves_last_run_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.run([], max_pages=0, minutes=0)
            finalizer = Collector(directory, 100)
            finalizer.checkpoint()
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["new_accepted"], 0)
            self.assertEqual(summary["current_run"]["pages_processed"], 0)

    def test_checkpoint_only_does_not_claim_a_new_run(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.checkpoint()
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertNotIn("current_run", summary)


if __name__ == "__main__":
    unittest.main()
