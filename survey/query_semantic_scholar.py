"""Build the preregistered Semantic Scholar citation corpus.

No API key is required, but SEMANTIC_SCHOLAR_API_KEY is honored when present.
The script preserves every raw citation-page response before filtering.
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


API = "https://api.semanticscholar.org/graph/v1"
SEEDS = (
    {
        "label": "Liu et al. 2017",
        "arxiv": "1611.02770",
        "api_id": "99e5a8c10cf92749d4a7c2949691c3a6046e499a",
    },
    {
        "label": "Papernot et al. 2017",
        "arxiv": "1602.02697",
        "api_id": "DOI:10.1145/3052973.3053009",
    },
)
FIELDS = (
    "paperId,title,abstract,year,venue,citationCount,externalIds,url,"
    "publicationDate,openAccessPdf,authors"
)
YEAR_MIN = 2018
YEAR_MAX = 2026
TOP_N = 80
TRANSFER = re.compile(r"transfer", re.IGNORECASE)
QUALIFIER = re.compile(r"adversarial|black[- ]?box|surrogate", re.IGNORECASE)


def get_json(url: str) -> dict:
    headers = {"User-Agent": "transferability-survey-corpus/1.0"}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    delay = 3.0
    for attempt in range(10):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 9:
                raise
            retry_after = error.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after else delay)
            delay = min(delay * 2, 60)
    raise RuntimeError("unreachable")


def citation_pages(api_id: str) -> list[dict]:
    pages: list[dict] = []
    offset = 0
    while True:
        params = urllib.parse.urlencode(
            {"fields": FIELDS, "limit": 1000, "offset": offset}
        )
        encoded_id = urllib.parse.quote(api_id, safe=":")
        page = get_json(f"{API}/paper/{encoded_id}/citations?{params}")
        pages.append(page)
        if not page.get("next"):
            return pages
        offset = int(page["next"])
        time.sleep(3)


def matches(paper: dict) -> bool:
    year = paper.get("year")
    text = f"{paper.get('title') or ''}\n{paper.get('abstract') or ''}"
    return (
        isinstance(year, int)
        and YEAR_MIN <= year <= YEAR_MAX
        and bool(TRANSFER.search(text))
        and bool(QUALIFIER.search(text))
    )


def main() -> None:
    root = Path(__file__).resolve().parent
    run_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    raw = {
        "run_at_utc": run_at,
        "api": API,
        "query": {
            "relationship": "papers citing either seed paper",
            "seed_arxiv_ids": [seed["arxiv"] for seed in SEEDS],
            "year_min_inclusive": YEAR_MIN,
            "year_max_inclusive": YEAR_MAX,
            "text_rule": (
                "case-insensitive title-or-abstract contains 'transfer' and at "
                "least one of 'adversarial', 'black-box'/'black box', 'surrogate'"
            ),
            "sort": "citationCount descending, then year descending, then title",
            "limit": TOP_N,
            "fields": FIELDS.split(","),
        },
        "seeds": [],
    }

    papers: dict[str, dict] = {}
    for seed in SEEDS:
        pages = citation_pages(seed["api_id"])
        raw["seeds"].append({**seed, "citation_pages": pages})
        for page in pages:
            for edge in page.get("data", []):
                paper = edge.get("citingPaper") or {}
                paper_id = paper.get("paperId")
                if not paper_id:
                    continue
                entry = papers.setdefault(paper_id, {**paper, "cites_seed_arxiv": []})
                if seed["arxiv"] not in entry["cites_seed_arxiv"]:
                    entry["cites_seed_arxiv"].append(seed["arxiv"])

    selected = [paper for paper in papers.values() if matches(paper)]
    selected.sort(
        key=lambda paper: (
            -(paper.get("citationCount") or 0),
            -(paper.get("year") or 0),
            (paper.get("title") or "").casefold(),
            paper["paperId"],
        )
    )
    selected = selected[:TOP_N]

    (root / "semantic_scholar_raw.json").write_text(
        json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (root / "query.json").write_text(
        json.dumps(
            {
                "run_at_utc": run_at,
                **raw["query"],
                "unique_citing_papers_retrieved": len(papers),
                "matching_papers_before_top_n": sum(matches(p) for p in papers.values()),
                "papers_selected": len(selected),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    columns = (
        "rank",
        "paper_id",
        "title",
        "year",
        "venue",
        "citations",
        "url",
        "doi",
        "arxiv",
        "cites_seed_arxiv",
    )
    with (root / "corpus.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for rank, paper in enumerate(selected, 1):
            external = paper.get("externalIds") or {}
            writer.writerow(
                {
                    "rank": rank,
                    "paper_id": paper["paperId"],
                    "title": paper.get("title") or "",
                    "year": paper.get("year") or "",
                    "venue": paper.get("venue") or "",
                    "citations": paper.get("citationCount") or 0,
                    "url": paper.get("url") or "",
                    "doi": external.get("DOI") or "",
                    "arxiv": external.get("ArXiv") or "",
                    "cites_seed_arxiv": ";".join(sorted(paper["cites_seed_arxiv"])),
                }
            )


if __name__ == "__main__":
    main()
