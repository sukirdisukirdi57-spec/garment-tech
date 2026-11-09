#!/usr/bin/env python3
"""Scrape parts T-8420C dari Brother Parts Book -> CSV."""
import re, csv, time, urllib.request
from pathlib import Path

BASE = "http://partsbook.brother.co.jp/pub/machine/detail/en/27"
OUT = Path("audit-kelengkapan/parts_t8420c_hasil_scrape.csv")

# section_id -> (section_name, urutan)
SECTIONS = {
    662: ("A. Machine body", 1),
    663: ("B. Upper shaft mechanism", 2),
    664: ("C. Needle bar rocking mechanism", 3),
    665: ("D. Presser foot mechanism", 4),
    666: ("E. Feed mechanism", 5),
    667: ("F. Feed shaft mechanism", 6),
    668: ("G. Gauge parts", 7),
    669: ("H1. Rotary hook mechanism", 8),
    670: ("H2. Rotary hook mechanism", 9),
    671: ("J. Lower shaft mechanism", 10),
    672: ("K. Lubrication", 11),
    673: ("L. Threading mechanism", 12),
    674: ("M. Bobbin winder mechanism", 13),
    675: ("N. Power supply equipment", 14),
    676: ("Z1. Accessories", 15),
    677: ("Z2. Accessories", 16),
    678: ("Wa. Warning labels", 17),
    679: ("Sp. Different parts list", 18),
    # Ga-1 s/d Ga-6: gauge parts list (tabel ukuran, bukan parts standar) — skip dulu
}

# Regex untuk baris tabel: <tr ... num="REF"><td>REF</td><td>QTY</td><td>...<td>CODE</td><td>NAME</td>
ROW_PATTERN = re.compile(
    r'<tr[^>]*num="(\d+)"[^>]*>.*?'
    r'<td[^>]*>(\d+)</td>.*?'         # REF-NO
    r'<td[^>]*>(\d+(?:\.\d+)?)</td>.*?'  # QTY
    r'<td class="align_c">.*?</td>.*?'    # RM
    r'<td[^>]*>([A-Z0-9][A-Z0-9\-]*)</td>.*?'  # CODE
    r'<td>([^<]*)</td>',               # NAME
    re.DOTALL
)

rows = []
for sid, (name, order) in SECTIONS.items():
    url = f"{BASE}/{sid}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"[ERROR] section {sid}: {e}")
        continue

    # Cari diagram page? (bisa dari thumbnail, tapi sementara pakai urutan)
    matches = ROW_PATTERN.findall(html)
    seen = set()
    count = 0
    for num, ref, qty, code, pname in matches:
        key = (ref, code)
        if key in seen: continue
        seen.add(key)
        rows.append({
            "section_id": sid,
            "section_ref": order,
            "section_name": name,
            "catalog_ref": ref,
            "part_number": code,
            "part_name": pname.strip(),
            "quantity": qty,
        })
        count += 1
    print(f"[section {order:>2}] {name:<40} {count} parts (id={sid})")
    time.sleep(1)  # hormati server

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["section_id","section_ref","section_name","catalog_ref","part_number","part_name","quantity"])
    w.writeheader()
    w.writerows(rows)

print(f"\n[TOTAL] {len(rows)} parts")
print(f"[CSV] {OUT}")
