import csv
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

class Extractor(HTMLParser):
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

src = Path("tools/preview_pegasus_specs_candidates.csv")
out = Path("tools/pegasus_technical_values.txt")

with src.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

terms = re.compile(
    r"maximum speed|max\. machine speed|sti/min|"
    r"no\. of needles|no\. of threads|needle space|"
    r"overedge width|seam|needle gauge|fabric weight|"
    r"stitch length adjustment|differential feed|lubrica|"
    r"presser foot lift|needle stroke",
    re.I,
)

with out.open("w", encoding="utf-8") as report:
    for row in rows:
        variant = row["variant"]
        url = row["source_url"]
        report.write(f"\n{'=' * 70}\n{row['model']} | {variant}\n{url}\n")

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 GarmentTech-Audit/1.0"}
            )
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read().decode("utf-8", errors="replace")
                report.write(f"HTTP: {response.status}\n")

            parser = Extractor()
            parser.feed(raw)
            text = "\n".join(parser.parts)
            lines = [re.sub(r"\s+", " ", x).strip()
                     for x in text.splitlines()]
            lines = [x for x in lines if x]

            hits = []
            for i, line in enumerate(lines):
                if terms.search(line):
                    # Ambil beberapa baris sesudah label untuk menangkap nilainya.
                    context = " | ".join(lines[i:i+3])
                    if context not in hits:
                        hits.append(context)

            if hits:
                for hit in hits[:25]:
                    report.write("- " + hit + "\n")
            else:
                report.write("Tidak ditemukan label spesifikasi teknis dalam teks.\n")

        except Exception as e:
            report.write(f"GAGAL: {type(e).__name__}: {e}\n")

        time.sleep(0.25)

print("Laporan teknis:", out.resolve())
print("Varian diproses:", len(rows))
print("Database diubah: TIDAK")
print("CSV kandidat diubah: TIDAK")
