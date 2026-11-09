import csv
import re
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path

SRC = Path("tools/preview_pegasus_specs_candidates.csv")
OUT = Path("tools/audit_pegasus_spec_context.txt")

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
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.parts.append(text)

def fetch_text(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 GarmentTech-Source-Audit/1.0"}
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read().decode("utf-8", errors="replace")
        code = response.status

    parser = TextExtractor()
    parser.feed(raw)
    text = re.sub(r"[ \t]+", " ", " ".join(parser.parts))
    text = re.sub(r"\s*\n\s*", "\n", text)
    return code, text

with SRC.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

with OUT.open("w", encoding="utf-8") as report:
    report.write("AUDIT KONTEKS SPESIFIKASI PEGASUS\n")
    report.write("Laporan pembacaan halaman; bukan persetujuan impor.\n")

    for row in rows:
        model = row["model"]
        variant = row["variant"]
        url = row["source_url"]

        report.write("\n" + "=" * 78 + "\n")
        report.write(f"MODEL: {model} | VARIAN: {variant}\nURL: {url}\n")

        try:
            code, text = fetch_text(url)
            report.write(f"HTTP: {code}\n")

            # Cari varian dan ambil teks sekitar kemunculannya.
            matches = list(re.finditer(re.escape(variant), text, flags=re.I))
            report.write(f"Jumlah kemunculan kode varian: {len(matches)}\n")

            if not matches:
                report.write("KODE VARIAN TIDAK DITEMUKAN DALAM TEKS HALAMAN.\n")
            else:
                # Ambil paling banyak 3 konteks agar laporan tidak membengkak.
                for i, match in enumerate(matches[:3], start=1):
                    start = max(0, match.start() - 500)
                    end = min(len(text), match.end() + 1100)
                    report.write(f"\n--- KONTEKS {i} ---\n")
                    report.write(text[start:end] + "\n")

            # Cari bagian halaman yang memuat istilah spesifikasi teknis.
            terms = re.compile(
                r"maximum speed|max\. speed|sti/min|rpm|needles?|threads?|"
                r"needle gauge|needle spacing|stitch length|needle distance",
                flags=re.I
            )
            snippets = []
            for m in terms.finditer(text):
                snippets.append(text[max(0, m.start()-100):min(len(text), m.end()+180)])
                if len(snippets) >= 12:
                    break

            report.write("\n--- POTONGAN ISTILAH SPESIFIKASI ---\n")
            if snippets:
                for snippet in snippets:
                    report.write("- " + snippet + "\n")
            else:
                report.write("Istilah spesifikasi tidak terdeteksi otomatis.\n")

        except Exception as exc:
            report.write(f"GAGAL MEMBACA HALAMAN: {type(exc).__name__}: {exc}\n")

        time.sleep(0.25)

print("Laporan dibuat:", OUT.resolve())
print("Jumlah halaman diproses:", len(rows))
print("Database diubah: TIDAK")
print("CSV kandidat diubah: TIDAK")
