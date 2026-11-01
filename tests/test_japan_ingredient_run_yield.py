import json
import sys
import tempfile
import time
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

    def test_navigation_pages_are_counted_without_false_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.permitted = lambda url: True
            collector.request = lambda url: "<html><body><h1>Product catalogue</h1></body></html>"
            collector.run(["https://www.sbfoods.co.jp/products/"], max_pages=1, minutes=1)
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["pages_processed"], 1)
            self.assertEqual(summary["current_run"]["new_accepted"], 0)
            self.assertEqual(summary["current_run"]["top_rejection_reasons"], {})
            self.assertEqual(summary["current_run"]["page_outcomes"],
                             {"discovery_navigation_page": 1})

    def test_queued_product_precedes_seed_navigation(self):
        # A large seed list must never starve unprocessed official product pages.
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            product = "https://www.sbfoods.co.jp/products/detail/123.html"
            catalogue = "https://www.sbfoods.co.jp/products/"
            collector.enqueue([product])
            collector.permitted = lambda url: True
            collector.request = lambda url: (
                "<html><h1>テストスパイス</h1>"
                "<dl><dt>原材料名</dt><dd>食塩、こしょう</dd></dl></html>"
            )
            collector.run([catalogue], max_pages=1, minutes=1)
            observed = collector.db.execute(
                "SELECT url,reason FROM observations ORDER BY rowid LIMIT 1"
            ).fetchone()
            self.assertEqual(observed, (product, "accepted_new_product"))
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["new_accepted"], 1)

    def test_navigation_fallback_rotates_official_hosts_without_skipping_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            urls = [
                "https://www.sbfoods.co.jp/products/",
                "https://www.sbfoods.co.jp/products/category/",
                "https://www.myojofoods.co.jp/products/",
                "https://www.myojofoods.co.jp/products/list/",
            ]
            collector.enqueue(urls)
            collector.permitted = lambda url: True
            collector.request = lambda url: "<html><body><h1>Product catalogue</h1></body></html>"
            collector.run([], max_pages=4, minutes=1)
            processed = [row[0] for row in collector.db.execute(
                "SELECT url FROM observations ORDER BY rowid"
            )]
            self.assertEqual(processed, [urls[0], urls[2], urls[1], urls[3]])
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["pages_processed"], 4)
            self.assertEqual(summary["current_run"]["new_accepted"], 0)
            self.assertEqual(summary["current_run"]["page_outcomes"],
                             {"discovery_navigation_page": 4})

    def test_host_cooldown_explains_zero_yield_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            product = "https://www.sbfoods.co.jp/products/detail/123.html"
            collector.enqueue([product])
            collector.db.execute(
                "INSERT INTO host_state(host,next_try,reason) VALUES(?,?,?)",
                ("www.sbfoods.co.jp", time.time() + 3600, "HTTPError:503"),
            )
            collector.db.commit()
            collector.run([], max_pages=1, minutes=1)
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["new_accepted"], 0)
            self.assertEqual(summary["current_run"]["stop_reason"],
                             "no_eligible_pending_urls")
            self.assertEqual(summary["current_run"]["pages_processed"], 0)
            self.assertEqual(summary["current_run"]["active_host_cooldowns"][0]["host"],
                             "www.sbfoods.co.jp")

    def test_page_budget_stop_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.run([], max_pages=0, minutes=1)
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["current_run"]["stop_reason"], "page_budget")

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
