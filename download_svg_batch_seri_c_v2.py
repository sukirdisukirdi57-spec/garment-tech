#!/usr/bin/env python3
"""Download SVG batch seri C (v2 - perbaiki ekstraksi kode)."""
import urllib.request, time, sqlite3, re
from pathlib import Path

DB = Path("database/garment.db")
BASE = "http://partsbook.brother.co.jp/public/img/files"

MACHINES = [
    (95, 35, "T-8450C"),
    (91, 38, "T-8452C"),
    (96, 41, "T-8720C"),
    (92, 44, "T-8722C"),
    (97, 46, "T-8750C"),
    (93, 49, "T-8752C"),
]

def try_fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=10).read()
        if data[:15] == b"<!DOCTYPE html>" or b"<html" in data[:200]:
            return None
        return data
    except Exception:
        return None

conn = sqlite3.connect(DB)
cur = conn.cursor()

for db_id, bro_id, model in MACHINES:
    print(f"\n=== {model} ===")
    cur.execute("SELECT id, catalog_ref, component_name FROM components WHERE machine_id=? ORDER BY CAST(catalog_ref AS INTEGER)", (db_id,))
    comps = cur.fetchall()
    
    prefix = model.lower().replace("-", "")
    out_dir = Path(f"static/images/mechanisms/brother/{prefix}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    ok = 0
    skip = []
    for comp_id, ref, name in comps:
        # Ekstrak kode: "A. Machine body" -> "a", "K1. Rotary hook" -> "k1", "Ga1-1." -> "ga1-1"
        m = re.match(r'^([A-Za-z]+\d*(?:-\d+)?)\s*\.', name)
        if not m:
            skip.append(name)
            continue
        code = m.group(1).lower()
        
        url = f"{BASE}/{prefix}_{code}.svg"
        data = try_fetch(url)
        if data:
            out = out_dir / f"section-{int(ref):02d}.svg"
            out.write_bytes(data)
            ok += 1
        else:
            # fallback ke t_8421c / t_8422c
            for alt in ["t_8421c", "t_8422c"]:
                data = try_fetch(f"{BASE}/{alt}_{code}.svg")
                if data:
                    out = out_dir / f"section-{int(ref):02d}.svg"
                    out.write_bytes(data)
                    ok += 1
                    break
            else:
                skip.append(name)
        time.sleep(0.3)
    
    print(f"  {ok}/{len(comps)} SVG berhasil")
    if skip:
        print(f"  SKIP: {', '.join(skip)}")

conn.close()
print("\n[SELESAI]")
