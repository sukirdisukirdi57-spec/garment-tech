import csv
import time
import urllib.request
import urllib.error
import html
import re
from pathlib import Path

src = Path("tools/preview_pegasus_specs_candidates.csv")
out = Path("tools/audit_pegasus_candidate_urls.csv")

with src.open(newline="", encoding="utf-8-sig") as f:
    candidates = list(csv.DictReader(f))

results = []

for row in candidates:
    url = row["source_url"]
    variant = row["variant"]
    status_code = ""
    found = False
    page_title = ""
    error = ""

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 GarmentTech-Source-Audit/1.0"}
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            status_code = response.status
            content = response.read().decode("utf-8", errors="replace")

        content = html.unescape(content)
        found = variant.casefold() in content.casefold()

        match = re.search(
            r"<title[^>]*>(.*?)</title>",
            content,
            flags=re.I | re.S
        )
        if match:
            page_title = re.sub(r"\s+", " ", match.group(1)).strip()

    except urllib.error.HTTPError as e:
        status_code = e.code
        error = f"HTTPError: {e}"
    except Exception as e:
        error = f"{type(e).__name__}: {e}"

    if status_code == 200 and found:
        result = "HTTP OK - VARIAN DITEMUKAN"
    elif status_code == 200:
        result = "HTTP OK - VARIAN TIDAK DITEMUKAN"
    elif status_code:
        result = f"HTTP {status_code}"
    else:
        result = "GAGAL DIAKSES"

    results.append({
        "model": row["model"],
        "variant": variant,
        "source_url": url,
        "http_status": status_code,
        "variant_found": "YA" if found else "TIDAK",
        "page_title": page_title,
        "result": result,
        "error": error,
    })

    print(f'{variant:20} | {result}')
    time.sleep(0.3)

fields = [
    "model", "variant", "source_url", "http_status",
    "variant_found", "page_title", "result", "error"
]
with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

print("\n===== RINGKASAN =====")
print("Total kandidat:", len(results))
print("HTTP OK dan varian ditemukan:",
      sum(r["result"] == "HTTP OK - VARIAN DITEMUKAN" for r in results))
print("HTTP OK tetapi varian tidak ditemukan:",
      sum(r["result"] == "HTTP OK - VARIAN TIDAK DITEMUKAN" for r in results))
print("Laporan:", out.resolve())
print("Database diubah: TIDAK")
