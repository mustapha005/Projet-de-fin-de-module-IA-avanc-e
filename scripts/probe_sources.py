"""Fetch only public source pages and expose relevant dataset archive links."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
import json
import urllib.request
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    "busi_university": "https://scholar.cu.edu.eg/?q=afahmy/pages/dataset",
    "busi_archive": "https://scholar.cu.edu.eg/Dataset_BUSI.zip",
    "breast_tcia": "https://www.cancerimagingarchive.net/collection/breast-lesions-usg/",
    "busi_mirror_metadata": "https://www.kaggle.com/api/v1/datasets/view/aryashah2k/breast-ultrasound-images-dataset",
}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(v for k, v in attrs if k == "href" and v)


def probe(item):
    name, url = item
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SAN1-academic-reproducibility/0.1"})
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            result = {"name": name, "url": url, "resolved_url": response.url,
                      "status": response.status, "content_type": content_type,
                      "content_length": response.headers.get("Content-Length")}
            if "json" in content_type:
                payload = json.loads(response.read())
                result["metadata"] = {k: payload[k] for k in payload
                                      if any(term in k.lower() for term in
                                             ["title", "license", "version", "size", "url"])}
            elif "html" in content_type:
                body = response.read().decode("utf-8", errors="replace")
                parser = Links()
                parser.feed(body)
                result["links"] = [urljoin(response.url, link) for link in parser.links
                                   if any(x in link.lower() for x in
                                          [".zip", ".xlsx", "license", "creativecommons", "download"])]
            else:
                result["first_bytes_hex"] = response.read(8).hex()
        return result
    except Exception as error:
        return {"name": name, "url": url, "error": f"{type(error).__name__}: {error}"}


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(probe, URLS.items()))
    (ROOT / "docs" / "source_probe.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
