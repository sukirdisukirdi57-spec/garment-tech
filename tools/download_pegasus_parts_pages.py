from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from html.parser import HTMLParser
import csv
import re
import time

BASE = "https://www.pegasus.co.jp/webcatalog/"
ROOT = Path("tools/tmp_audit/parts_catalog_pages")

CATALOGS = {
    "E22L_E32L_E52L": "9B6066000009",
    "E256": "9B6031000009",
}

class OptionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.options = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "option":
            a = dict(attrs)
            self.current = {
                "page": a.get("value", "").strip(),
                "title": "",
            }

    def handle_data(self, data):
        if self.current is not None:
            self.current["title"] += data

    def handle_endtag(self, tag):
        if tag.lower() == "option" and self.current is not None:
            if self.current["page"].isdigit():
                self.current["title"] = re.sub(
                    r"\s+", " ", self.current["title"]
                ).strip()
                self.options.append(self.current)
            self.current = None

def get(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=45) as resp:
        return resp.status, resp.read(), resp.headers.get("Content-Type", "")

ROOT.mkdir(parents=True, exist_ok=True)
manifest = []
errors = []

for model, itemcd in CATALOGS.items():
    print(f"\n========== {model} | {itemcd} ==========")
    folder = ROOT / model
    folder.mkdir(parents=True, exist_ok=True)

    view_url = BASE + "view.php?" + urlencode({
        "itemcd": itemcd, "rev": "00"
    })

    try:
        status, body, content_type = get(view_url)
        if status != 200 or "html" not in content_type.lower():
            raise RuntimeError(
                f"Halaman katalog tidak valid: HTTP {status}, {content_type}"
            )
        parser = OptionParser()
        parser.feed(body.decode("utf-8", "replace"))
        pages = parser.options
        if not pages:
            raise RuntimeError("Nomor halaman tidak ditemukan pada HTML.")

        print("Jumlah halaman pada indeks:", len(pages))
        print("Rentang:", pages[0]["page"], "-", pages[-1]["page"])

        for item in pages:
            page = int(item["page"])
            filename = f"{page:03d}.pdf"
            path = folder / filename
            url = BASE + "file.php?" + urlencode({
                "itemcd": itemcd,
                "rev": "00",
                "pageseq": page,
            })

            try:
                if path.exists() and path.read_bytes().startswith(b"%PDF-"):
                    data = path.read_bytes()
                    result = "SUDAH ADA PDF VALID"
                else:
                    status, data, ctype = get(url)
                    if status != 200 or not data.startswith(b"%PDF-"):
                        raise RuntimeError(
                            f"HTTP {status}; tipe={ctype}; "
                            "respons bukan PDF valid"
                        )
                    path.write_bytes(data)
                    result = "DIUNDUH"

                manifest.append({
                    "model": model,
                    "itemcd": itemcd,
                    "page": page,
                    "title": item["title"],
                    "file": str(path),
                    "bytes": len(data),
                    "status": result,
                    "source_url": url,
                })
                print(f"{page:03d}/{len(pages):03d} {result}: "
                      f"{item['title']} ({len(data)} bytes)")
                time.sleep(0.15)

            except Exception as exc:
                errors.append((model, page, item["title"], repr(exc)))
                print(f"GAGAL halaman {page}: {exc}")

    except Exception as exc:
        errors.append((model, "", "INDEX", repr(exc)))
        print("GAGAL membaca indeks:", repr(exc))

manifest_path = ROOT / "manifest.csv"
with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
    fields = [
        "model", "itemcd", "page", "title", "file",
        "bytes", "status", "source_url"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(manifest)

error_path = ROOT / "errors.csv"
with error_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["model", "page", "title", "error"])
    writer.writerows(errors)

print("\n========== RINGKASAN ==========")
for model in CATALOGS:
    rows = [r for r in manifest if r["model"] == model]
    print(f"{model}: {len(rows)} halaman tersimpan/valid")
print("Manifest:", manifest_path)
print("Daftar kegagalan:", error_path)
print("Jumlah kegagalan:", len(errors))
print("Database diubah: TIDAK")
print("Staging diubah: TIDAK")
print("Deployment: TIDAK")
