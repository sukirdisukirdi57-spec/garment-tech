#!/usr/bin/env python3
"""Download SVG diagram T-8422C dari Brother Parts Book."""
import urllib.request, time
from pathlib import Path

BASE = "http://partsbook.brother.co.jp/public/img/files"
OUT = Path("static/images/mechanisms/brother/t8422c")
OUT.mkdir(parents=True, exist_ok=True)

# section_ref -> kode huruf SVG
SECTIONS = {
    1: "a", 2: "b", 3: "c", 4: "d", 5: "e", 6: "f", 7: "g", 8: "h",
    9: "j2", 10: "j3", 11: "k", 12: "l", 13: "m", 14: "n", 15: "p",
    16: "q", 17: "r", 18: "s1", 19: "s2", 20: "s3", 21: "t",
    22: "u", 23: "z1", 24: "z2", 25: "wa1", 26: "wa2", 27: "sp1", 28: "sp2",
}

for ref, code in SECTIONS.items():
    url = f"{BASE}/t_8422c_{code}.svg"
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
