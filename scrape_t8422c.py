#!/usr/bin/env python3
"""Scrape parts T-8422C dari Brother Parts Book -> CSV."""
import re, csv, time, urllib.request
from pathlib import Path

BASE = "http://partsbook.brother.co.jp/pub/machine/detail/en/33"
OUT = Path("audit-kelengkapan/parts_t8422c_hasil_scrape.csv")

SECTIONS = {
    897: ("A. Machine body", 1),
    898: ("B. Upper shaft mechanism", 2),
    899: ("C. Needle bar rocking mechanism", 3),
    900: ("D. Presser foot mechanism", 4),
    901: ("E. Feed mechanism", 5),
    902: ("F. Quick reverse mechanism", 6),
    903: ("G. Feed shaft mechanism", 7),
    904: ("H. Gauge parts", 8),
    906: ("J2. Rotary hook mechanism (T-8422C)", 9),
    907: ("J3. Rotary hook mechanism", 10),
    908: ("K. Lower shaft mechanism", 11),
    909: ("L. Lubrication", 12),
    910: ("M. Threading mechanism", 13),
    911: ("N. Bobbin winder mechanism", 14),
    912: ("P. Thread trimmer mechanism", 15),
    913: ("Q. Tension release mechanism (T-8422C)", 16),
    914: ("R. Thread wiper mechanism (T-8422C)", 17),
    915: ("S1. Control box and motor mechanism", 18),
    916: ("S2. Control box", 19),
    917: ("S3. Control box", 20),
    918: ("T. Quick reverse switch mechanism", 21),
    919: ("U. Power supply equipment", 22),
    920: ("Z1. Accessories", 23),
    921: ("Z2. Accessories", 24),
    922: ("Wa1. Warning labels", 25),
    923: ("Wa2. Warning labels", 26),
    924: ("Sp1. Different parts list", 27),
    925: ("Sp2. Different parts list", 28),
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
