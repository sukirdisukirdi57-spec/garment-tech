#!/usr/bin/env python3
"""Scrape parts T-8421C dari Brother Parts Book -> CSV."""
import re, csv, time, urllib.request
from pathlib import Path

BASE = "http://partsbook.brother.co.jp/pub/machine/detail/en/30"
OUT = Path("audit-kelengkapan/parts_t8421c_hasil_scrape.csv")

# section_id -> (section_name, urutan)
SECTIONS = {
    772: ("A. Machine body", 1),
    773: ("B. Upper shaft mechanism", 2),
    774: ("C. Needle bar rocking mechanism", 3),
    775: ("D. Presser foot mechanism", 4),
    776: ("E. Feed mechanism", 5),
    777: ("F. Quick reverse mechanism", 6),
    778: ("G. Feed shaft mechanism", 7),
    779: ("H. Gauge parts", 8),
    780: ("J1. Rotary hook mechanism (T-8421C)", 9),
    782: ("J3. Rotary hook mechanism", 10),
    783: ("K. Lower shaft mechanism", 11),
    784: ("L. Lubrication", 12),
    785: ("M. Threading mechanism", 13),
    786: ("N. Bobbin winder mechanism", 14),
    787: ("P. Thread trimmer mechanism", 15),
    790: ("S1. Control box and motor mechanism", 16),
    791: ("S2. Control box", 17),
    792: ("S3. Control box", 18),
    793: ("T. Quick reverse switch mechanism", 19),
    794: ("U. Power supply equipment", 20),
    795: ("Z1. Accessories", 21),
    796: ("Z2. Accessories", 22),
    797: ("Wa1. Warning labels", 23),
    798: ("Wa2. Warning labels", 24),
    799: ("Sp1. Different parts list", 25),
    800: ("Sp2. Different parts list", 26),
}

ROW_PATTERN = re.compile(
    r'<tr[^>]*num="(\d+)"[^>]*>.*?'
    r'<td[^>]*>(\d+)</td>.*?'
    r'<td[^>]*>(\d+(?:\.\d+)?)</td>.*?'
    r'<td class="align_c">.*?</td>.*?'
    r'<td[^>]*>([A-Z0-9][A-Z0-9\-]*)</td>.*?'
    r'<td>([^<]*)</td>',
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
    print(f"[section {order:>2}] {name:<45} {count} parts")
    time.sleep(1)

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["section_id","section_ref","section_name","catalog_ref","part_number","part_name","quantity"])
    w.writeheader()
    w.writerows(rows)

print(f"\n[TOTAL] {len(rows)} parts")
print(f"[CSV] {OUT}")
