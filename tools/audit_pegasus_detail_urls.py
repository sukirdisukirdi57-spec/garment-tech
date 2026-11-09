import csv
import re
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import quote
from html.parser import HTMLParser

SRC = Path("tools/preview_pegasus_specs_candidates.csv")
OUT = Path("tools/pegasus_detail_url_audit.csv")

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip:
            self.skip -= 1
        elif tag in ("p", "div", "li", "tr", "td", "th", "br", "h1", "h2", "h3"):
            if not self.skip:
                self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            s = re.sub(r"\s+", " ", data).strip()
            if s:
                self.parts.append(s)

with SRC.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

results = []

for row in rows:
    model = row["model"]
    variant = row["variant"]
    original = row["source_url"]
    candidates = [original]

    if model in ("M922", "M932", "M952"):
        candidates.insert(
            0, "https://www.pegasus.co.jp/en/machine/detail/series/s106/"
            + quote(variant, safe="")
        )
    elif model in ("EX3200", "EX5200"):
        candidates.insert(
            0, "https://www.pegasus.co.jp/en/machine/detail/series/s102/"
            + quote(variant, safe="")
        )

    seen = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)

        status = ""
        title = ""
        text = ""
        error = ""

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 GarmentTech-Audit/1.0"}
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                status = response.status
                raw = response.read().decode("utf-8", errors="replace")

            parser = TextExtractor()
            parser.feed(raw)
            text = " ".join(parser.parts)
            match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
            if match:
                title = re.sub(r"\s+", " ", match.group(1)).strip()

        except urllib.error.HTTPError as exc:
            status = exc.code
            error = str(exc)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        has_variant = variant.casefold() in text.casefold()
        technical_labels = sum(
            term in text.casefold()
            for term in (
                "max. machine speed", "no. of needles",
                "no. of threads", "needle space"
            )
        )

        results.append({
            "model": model,
            "variant": variant,
            "url_tested": url,
            "is_original_url": "YA" if url == original else "TIDAK",
            "http_status": status,
            "variant_in_text": "YA" if has_variant else "TIDAK",
            "technical_label_count": technical_labels,
            "page_title": title,
            "error": error,
        })

        print(
            f"{variant:20} HTTP={status or '-':4} "
            f"kode={'YA' if has_variant else 'TIDAK':5} "
            f"label_teknis={technical_labels} "
            f"{'DETAIL' if url != original else 'URL ASLI'}"
        )

fields = [
    "model", "variant", "url_tested", "is_original_url",
    "http_status", "variant_in_text", "technical_label_count",
    "page_title", "error"
]
with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

print("\nLaporan:", OUT.resolve())
print("Jumlah pengujian URL:", len(results))
print("Database diubah: TIDAK")
print("CSV kandidat diubah: TIDAK")
