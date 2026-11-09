#!/usr/bin/env python3
"""Download SVG diagram T-8422C (prefix t_8421c_)."""
import urllib.request, time
from pathlib import Path

BASE = "http://partsbook.brother.co.jp/public/img/files"
OUT = Path("static/images/mechanisms/brother/t8422c")
OUT.mkdir(parents=True, exist_ok=True)

# section_ref -> kode SVG (prefix t_8421c_)
SECTIONS = {
    1: "a", 2: "b", 3: "c", 4: "d", 5: "e", 6: "f", 7: "g", 8: "h",
    9: "j2",   # khusus 8422C
    10: "j3", 11: "k", 12: "l", 13: "m", 14: "n", 15: "p",
    16: "q",   # khusus 8422C
    17: "r",   # khusus 8422C
    18: "s1", 19: "s2", 20: "s3", 21: "t", 22: "u",
    23: "z1", 24: "z2", 25: "wa1", 26: "wa2",
    27: "sp1", 28: "sp2",  # khusus 8422C (prefix t_8422c_)
}

for ref, code in SECTIONS.items():
    # sp1/sp2 pakai prefix t_8422c_, sisanya t_8421c_
    prefix = "t_8422c" if code.startswith("sp") else "t_8421c"
    url = f"{BASE}/{prefix}_{code}.svg"
    out = OUT / f"section-{ref:02d}.svg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        # Cek apakah HTML error
        if data[:15] == b"<!DOCTYPE html>" or b"<html" in data[:200]:
            print(f"[ERROR HTML] section {ref} ({url})")
            continue
        out.write_bytes(data)
        print(f"[OK] section {ref:>2} -> {out.name} ({len(data)} bytes)")
    except Exception as e:
        print(f"[ERROR] section {ref} ({url}): {e}")
    time.sleep(0.5)

print(f"\n[SELESAI] {OUT}")
