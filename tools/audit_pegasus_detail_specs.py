import csv
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SRC = Path("tools/preview_pegasus_specs_candidates.csv")
OUT = Path("tools/pegasus_detail_specs_audit.csv")

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            self.cell = tag
            self.parts = []

    def handle_data(self, data):
        if self.cell:
            value = " ".join(data.split())
            if value:
                self.parts.append(value)

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell == tag:
            self.row.append(" ".join(self.parts).strip())
            self.cell = None
            self.parts = []
        elif tag == "tr" and self.row is not None:
            if len(self.row) >= 2:
                self.rows.append(self.row)
            self.row = None


def detail_url(model, variant):
    if model in ("M922", "M932", "M952"):
        return f"https://www.pegasus.co.jp/en/machine/detail/series/s106/{variant}"
    if model in ("EX3200", "EX5200"):
        slug = variant.replace("/", "_")
        return f"https://www.pegasus.co.jp/en/machine/detail/series/s102/{slug}"
    if model == "W562P":
        return f"https://www.pegasus.co.jp/en/machine/detail/series/s205/{variant}"
    return ""


def clean_label(value):
    return " ".join(value.lower().replace("ｔ", "t").split())


def main():
    if not SRC.exists():
        raise SystemExit(f"CSV kandidat tidak ditemukan: {SRC}")
    with SRC.open(newline="", encoding="utf-8-sig") as f:
        candidates = list(csv.DictReader(f))
    if not candidates:
        raise SystemExit("CSV kandidat kosong; tidak ada audit dijalankan.")
    out_rows = []
    for item in candidates:
        model = item.get("model", "").strip()
        variant = item.get("variant", "").strip()
        url = detail_url(model, variant)
        record = {
            "model": model, "variant": variant, "url": url,
            "http": "SKIP" if not url else "", "page_title": "",
            "speed": "", "needles": "", "threads": "",
            "needle_space": "", "overedge_width": "",
            "fabric_weight": "", "seam": "", "note": ""
        }
        if not url:
            record["note"] = "Pola URL detail belum ditemukan; perlu audit terpisah"
        else:
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0 GarmentTech-ReadOnly-Audit/1.0"}
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    html = response.read().decode("utf-8", errors="replace")
                    record["http"] = str(response.status)
                title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                if title:
                    record["page_title"] = " ".join(
                        re.sub(r"<[^>]+>", " ", title.group(1)).split()
                    )
                parser = TableParser()
                parser.feed(html)
                for row in parser.rows:
                    label = clean_label(row[0])
                    value = " ".join(row[1].split())
                    if "max. machine speed" in label:
                        record["speed"] = value
                    elif "no. of needles" in label:
                        record["needles"] = value
                    elif "no. of threads" in label:
                        record["threads"] = value
                    elif "needle space" in label:
                        record["needle_space"] = value
                    elif "overedge width" in label:
                        record["overedge_width"] = value
                    elif "fabric weight" in label:
                        record["fabric_weight"] = value
                    elif "seam" in label:
                        record["seam"] = value
                record["note"] = (
                    "OK" if record["speed"] and record["needles"] and record["threads"]
                    else "Periksa tabel HTML; sebagian nilai tidak terbaca otomatis"
                )
            except Exception as exc:
                record["http"] = "ERROR"
                record["note"] = f"{type(exc).__name__}: {exc}"
        out_rows.append(record)
        print(
            f"{variant:18} HTTP={record['http']:5} "
            f"speed={record['speed'] or '-':18} "
            f"jarum={record['needles'] or '-':5} "
            f"benang={record['threads'] or '-':5} {record['note']}"
        )
        if url:
            time.sleep(0.2)
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"\nSelesai. Hasil audit: {OUT}")
    print("Database tidak diubah; CSV kandidat sumber tidak diubah.")

if __name__ == "__main__":
    main()
