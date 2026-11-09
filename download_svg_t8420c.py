#!/usr/bin/env python3
"""Download SVG diagram T-8420C dari Brother Parts Book."""
import urllib.request, time
from pathlib import Path

BASE = "http://partsbook.brother.co.jp/public/img/files"
OUT = Path("static/images/mechanisms/brother/t8420c")
OUT.mkdir(parents=True, exist_ok=True)

# Mapping section_ref -> kode huruf SVG
# Dari thumbnail: t_8420c_a.svg (section A), dst.
# section_ref -> huruf
SECTIONS = {
    1: "a", 2: "b", 3: "c", 4: "d", 5: "e", 6: "f", 7: "g",
    8: "h1", 9: "h2", 10: "j", 11: "k", 12: "l", 13: "m",
    14: "n", 15: "z1", 16: "z2", 17: "wa", 18: "sp",
}

for ref, code in SECTIONS.items():
    url = f"{BASE}/t_8420c_{code}.svg"
    out = OUT / f"section-{ref:02d}.svg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        out.write_bytes(data)
        print(f"[OK] section {ref:>2} -> {out.name} ({len(data)} bytes)")
    except Exception as e:
        print(f"[ERROR] section {ref}: {e}")
    time.sleep(0.5)

print(f"\n[SELESAI] {OUT}")
