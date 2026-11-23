import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import import_off_japan_ingredients as off
import stage_off_ingredient_batch as stage


def product(code, name, ingredients):
    return {
        "code": code,
        "product_name_ja": name,
        "ingredients_text_ja": ingredients,
        "brands": "テスト食品",
    }


class OpenFoodFactsCollectorTests(unittest.TestCase):
    def test_jan_checksum_and_japanese_fields_are_required(self):
        self.assertTrue(off.valid_ean("4902102154826"))
        self.assertTrue(off.valid_ean("4902102140553"))
        self.assertFalse(off.valid_ean("4902102154827"))
        self.assertFalse(off.is_japanese_ingredient_candidate(
            "4902102154826", "Green Tea", "緑茶、ビタミンC"
        ))
        self.assertTrue(off.is_japanese_ingredient_candidate(
            "4902102154826", "綾鷹", "緑茶、ビタミンC"
        ))

    def test_search_url_uses_japan_and_bounded_category_pages(self):
        url = off.build_search_url("beverages", 99, 500)
        parsed = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/api/v2/search")
        self.assertEqual(query["countries_tags"], ["en:japan"])
        self.assertEqual(query["categories_tags_en"], ["beverages"])
        self.assertEqual(query["page"], ["10"])
        self.assertEqual(query["page_size"], ["100"])
        with self.assertRaises(ValueError):
            off.build_search_url("unreviewed-category", 1, 100)

    def test_category_collection_deduplicates_barcodes_and_keeps_review_metadata(self):
        rows_by_category_page = {
            ("beverages", 1): {
                "count": 150, "page_count": 100,
                "products": [
                    product("4902102154826", "綾鷹", "緑茶、ビタミンC"),
                    product("4902102140553", "コカ・コーラ ゼロ", "炭酸、カラメル色素、香料"),
                ],
            },
            ("beverages", 2): {
                "count": 150, "page_count": 50,
                "products": [
                    product("4902102140553", "コカ・コーラ ゼロ", "炭酸、カラメル色素、香料"),
                    product("4901777411760", "午後の紅茶", "紅茶、香料、ビタミンC"),
                ],
            },
            ("snacks", 1): {
                "count": 1, "page_count": 1,
                "products": [
                    product("4901777411760", "午後の紅茶", "紅茶、香料、ビタミンC"),
                    product("4901085003800", "チョコレート", "砂糖、カカオマス、乳化剤"),
                ],
            },
        }
        calls = []

        def fake_fetch(url):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            key = (query["categories_tags_en"][0], int(query["page"][0]))
            calls.append(key)
            return rows_by_category_page[key]

        rows, stats = off.collect_candidates(
            ("beverages", "snacks"),
            pages_per_category=10,
            page_size=100,
            fetcher=fake_fetch,
            sleeper=lambda _: None,
            delay=0,
        )
        self.assertEqual(len(rows), 4)
        self.assertEqual(stats["pages_requested"], 3)
        self.assertEqual(stats["duplicate_barcodes"], 2)
        self.assertEqual(calls, [("beverages", 1), ("beverages", 2), ("snacks", 1)])
        self.assertEqual(rows[0]["source_license"], off.SOURCE_LICENSE)
        self.assertEqual(rows[0]["source_attribution"], "Open Food Facts contributors")
        self.assertEqual(rows[0]["verification_status"], off.VERIFICATION_STATUS)
        self.assertFalse(rows[0]["halal_certified"])
        self.assertTrue(rows[0]["source_url"].startswith(off.OFF_PRODUCT))

    def test_page_limit_is_ten_even_if_caller_requests_more(self):
        calls = []

        def fake_fetch(url):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            calls.append(int(query["page"][0]))
            return {"count": 5000, "page_count": 100, "products": []}

        off.collect_candidates(
            ("beverages",),
            pages_per_category=99,
            page_size=100,
            fetcher=fake_fetch,
            sleeper=lambda _: None,
            delay=0,
        )
        self.assertEqual(calls, list(range(1, 11)))

    def test_permanent_http_error_skips_only_the_failed_category(self):
        import urllib.error
        calls = []

        def fake_fetch(url):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            category = query["categories_tags_en"][0]
            calls.append(category)
            if category == "beverages":
                raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, None)
            return {
                "count": 1, "page_count": 1,
                "products": [product("4902102154826", "綾鷹", "緑茶、ビタミンC")],
            }

        rows, stats = off.collect_candidates(
            ("beverages", "snacks"),
            pages_per_category=10,
            page_size=100,
            fetcher=fake_fetch,
            sleeper=lambda _: None,
            delay=0,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(stats["failed_pages"], 1)
        self.assertEqual(stats["failed_categories"], ["beverages"])
        self.assertEqual(calls, ["beverages", "snacks"])


class OpenFoodFactsReviewQueueTests(unittest.TestCase):
    def test_stage_payload_preserves_metadata_and_never_certifies(self):
        rows, _ = off.collect_candidates(
            ("beverages",),
            pages_per_category=1,
            page_size=100,
            fetcher=lambda url: {
                "count": 1, "page_count": 1,
                "products": [product("4902102154826", "綾鷹", "緑茶、ビタミンC")],
            },
            sleeper=lambda _: None,
            delay=0,
        )
        payload = stage.to_queue_row(rows[0])
        self.assertEqual(payload["jan_code"], "4902102154826")
        self.assertEqual(payload["product_name"], "綾鷹")
        self.assertEqual(payload["ingredients_text"], "緑茶、ビタミンC")
        self.assertEqual(payload["source_url"], off.OFF_PRODUCT + "4902102154826")
        self.assertTrue(payload["collected_at"])
        self.assertEqual(payload["verification_status"], off.VERIFICATION_STATUS)
        self.assertEqual(payload["source_license"], off.SOURCE_LICENSE)
        self.assertEqual(payload["status"], "needs_review")
        self.assertEqual(payload["evidence_level"], "third_party_unverified_odbl_dbcl_pending_review")
        self.assertFalse(payload["halal_certified"])

    def test_loader_rejects_bad_ean_wrong_license_and_wrong_source_url(self):
        rows, _ = off.collect_candidates(
            ("beverages",),
            pages_per_category=1,
            page_size=100,
            fetcher=lambda url: {
                "count": 1, "page_count": 1,
                "products": [product("4902102154826", "綾鷹", "緑茶、ビタミンC")],
            },
            sleeper=lambda _: None,
            delay=0,
        )
        good = rows[0]
        bad_ean = dict(good, barcode="4902102154827", source_url=off.OFF_PRODUCT + "4902102154827")
        bad_license = dict(good, source_license="unknown")
        bad_url = dict(good, source_url="https://example.com/product/4902102154826")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.jsonl"
            path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in (good, bad_ean, bad_license, bad_url)), encoding="utf8")
            loaded = stage.load_candidates(path)
        self.assertEqual(list(loaded), ["4902102154826"])


if __name__ == "__main__":
    unittest.main()
