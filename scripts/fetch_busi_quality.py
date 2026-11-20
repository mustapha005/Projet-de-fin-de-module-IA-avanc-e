"""Acquire the published BUSI duplicate-pair facts, with source attribution."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC10293973/table/tbl0004/"


class TableText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == "table":
            self.depth -= 1

    def handle_data(self, value):
        if self.depth:
            self.text.append(value)


def main():
    request = urllib.request.Request(URL, headers={"User-Agent": "SAN1-academic-reproducibility/0.1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read()
    html = body.decode("utf-8")
    if "Table B1" not in html:
        raise ValueError("Expected published duplicate table was not returned")
    parser = TableText()
    parser.feed(html)
    pairs = sorted(set(tuple(sorted(map(int, values))) for values in
                       re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", " ".join(parser.text))))
    if len(pairs) < 100 or any(a == b or not 1 <= a < b <= 780 for a, b in pairs):
        raise ValueError(f"Unexpected published pair table: {len(pairs)} pairs")
    report = {"source_url": URL, "doi": "10.1016/j.dib.2023.109247",
              "authors": "Anna Pawlowska, Piotr Karwat, Norbert Zolek",
              "table": "B1", "license": "CC BY 4.0", "source_html_sha256": hashlib.sha256(body).hexdigest(),
              "accessed_at_utc": datetime.now(timezone.utc).isoformat(),
              "id_mapping": "1..437 benign; 438..647 malignant (subtract 437); 648..780 normal (subtract 647)",
              "pair_count": len(pairs), "pairs": pairs}
    path = ROOT / "configs" / "busi_published_pairs.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(pairs)} published duplicate pairs to {path}")


if __name__ == "__main__":
    main()
