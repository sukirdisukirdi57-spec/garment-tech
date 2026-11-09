#!/usr/bin/env python3
"""Download SVG diagram T-8421C dari Brother Parts Book."""
import urllib.request, time
from pathlib import Path

BASE = "http://partsbook.brother.co.jp/public/img/files"
OUT = Path("static/images/mechanisms/brother/t8421c")
OUT.mkdir(parents=True, exist_ok=True)

# section_ref -> kode huruf SVG (pola: t_8421c_{code}.svg)
SECTIONS = {
    1: "a", 2: "b", 3: "c", 4: "d", 5: "e", 6: "f", 7: "g",
    8: "h", 9: "j1", 10: "j3", 11: "k", 12: "l", 13: "m",
    14: "n", 15: "p", 16: "s1", 17: "s2", 18: "s3", 19: "t",
    20: "u", 21: "z1", 22: "z2", 23: "wa1", 24: "wa2", 25: "sp1", 26: "sp2",
}

for ref, code in SECTIONS.items():
    url = f"{BASE}/t_8421c_{code}.svg"
    out = OUT / f"section-{ref:02d}.svg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        out.write_bytes(data)
        print(f"[OK] section {ref:>2} -> {out.name} ({len(data)} bytes)")
    except Exception as e:
        print(f"[ERROR] section {ref} ({url}): {e}")
    time.sleep(0.5)

print(f"\n[SELESAI] {OUT}")
