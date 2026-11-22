#!/usr/bin/env python3
"""Status report for the paused public-source discovery workflow.

The previous implementation fetched pages from an unrelated third-party halal guide.
No approved search provider is configured in this workflow, so it must not probe or
scrape unrelated sites. The main ingredient crawler continues to use its reviewed
source registry, robots checks, source-terms gate, and deduplication.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("data/research/agent_reach_public_sources.json")


def build_report(now=None):
    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    return {
        "status": "paused",
        "reason_code": "search_provider_not_configured",
        "reason": (
            "No approved web-search provider is configured for this workflow. "
            "The previous implementation targeted an unrelated third-party site "
            "rather than discovering Japanese food product sources; that access "
            "has been removed."
        ),
        "discovery_only": True,
        "candidate_count": 0,
        "verified_product_records": 0,
        "supabase_imported": 0,
        "sources_accessed": [],
        "generated_at": timestamp,
    }


def main():
    report = build_report()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Public source discovery paused: no approved search provider configured; "
        "no external product websites accessed."
    )


if __name__ == "__main__":
    main()
