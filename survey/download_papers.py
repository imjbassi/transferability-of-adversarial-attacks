"""Download openly accessible corpus PDFs and extract text for coding.

The cache directory is intentionally external to the repository.  Failures are
recorded in a manifest and remain eligible for manual retrieval.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import fitz
import requests


FALLBACK_URLS = {
    9: "https://arxiv.org/pdf/1809.02861",
    31: "https://openaccess.thecvf.com/content_CVPR_2019/papers/Inkawhich_Feature_Space_Perturbations_Yield_More_Transferable_Adversarial_Examples_CVPR_2019_paper.pdf",
    38: "https://openaccess.thecvf.com/content_CVPR_2020/papers/Wu_Boosting_the_Transferability_of_Adversarial_Samples_via_Attention_CVPR_2020_paper.pdf",
    40: "https://ojs.aaai.org/index.php/AAAI/article/download/5432/5288",
    61: "https://openaccess.thecvf.com/content_CVPR_2020/papers/Li_Towards_Transferable_Targeted_Attack_CVPR_2020_paper.pdf",
    70: "https://openaccess.thecvf.com/content/CVPR2021/papers/Wu_Improving_the_Transferability_of_Adversarial_Samples_With_Adversarial_Transformations_CVPR_2021_paper.pdf",
}


def raw_papers(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for seed in payload["seeds"]:
        for page in seed["citation_pages"]:
            for edge in page.get("data", []):
                paper = edge.get("citingPaper") or {}
                if paper.get("paperId"):
                    result[paper["paperId"]] = paper
    return result


def candidates(row: dict[str, str], paper: dict) -> list[str]:
    urls: list[str] = []
    if int(row["rank"]) in FALLBACK_URLS:
        urls.append(FALLBACK_URLS[int(row["rank"])])
    if row.get("arxiv"):
        urls.append(f"https://arxiv.org/pdf/{row['arxiv']}")
    open_pdf = paper.get("openAccessPdf") or {}
    if open_pdf.get("url"):
        urls.append(open_pdf["url"])
    return list(dict.fromkeys(urls))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cache", type=Path)
    args = parser.parse_args()
    survey = Path(__file__).resolve().parent
    args.cache.mkdir(parents=True, exist_ok=True)
    papers = raw_papers(survey / "semantic_scholar_raw.json")
    rows = list(csv.DictReader((survey / "corpus.csv").open(encoding="utf-8")))
    session = requests.Session()
    session.headers["User-Agent"] = "transferability-survey-coding/1.0"
    manifest: list[dict] = []
    for row in rows:
        stem = f"{int(row['rank']):02d}_{row['paper_id']}"
        pdf_path = args.cache / f"{stem}.pdf"
        text_path = args.cache / f"{stem}.txt"
        item = {
            "rank": int(row["rank"]),
            "paper_id": row["paper_id"],
            "title": row["title"],
            "pdf": str(pdf_path),
            "text": str(text_path),
            "status": "failed",
            "source_url": "",
            "attempts": [],
        }
        if pdf_path.exists() and text_path.exists():
            if "=== PAGE " not in text_path.read_text(encoding="utf-8", errors="replace")[:100]:
                document = fitz.open(pdf_path)
                text_path.write_text(
                    "\n\n".join(
                        f"=== PAGE {number} ===\n{page.get_text('text')}"
                        for number, page in enumerate(document, 1)
                    ),
                    encoding="utf-8",
                )
            item["status"] = "cached"
            manifest.append(item)
            continue
        for url in candidates(row, papers.get(row["paper_id"], {})):
            try:
                response = session.get(url, timeout=90, allow_redirects=True)
                item["attempts"].append(
                    {"url": url, "status": response.status_code, "bytes": len(response.content)}
                )
                if response.status_code != 200 or not response.content.startswith(b"%PDF"):
                    continue
                pdf_path.write_bytes(response.content)
                document = fitz.open(pdf_path)
                text_path.write_text(
                    "\n\n".join(
                        f"=== PAGE {number} ===\n{page.get_text('text')}"
                        for number, page in enumerate(document, 1)
                    ),
                    encoding="utf-8",
                )
                item["status"] = "downloaded"
                item["source_url"] = response.url
                break
            except Exception as error:  # Preserve the failure for audit.
                item["attempts"].append({"url": url, "error": repr(error)})
            finally:
                time.sleep(0.5)
        manifest.append(item)
        print(f"{row['rank']:>2} {item['status']}: {row['title']}", flush=True)
    (args.cache / "download_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
