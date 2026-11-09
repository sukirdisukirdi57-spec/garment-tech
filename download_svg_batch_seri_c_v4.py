#!/usr/bin/env python3
"""Download SVG batch seri C (v4 - pakai curl subprocess)."""
import subprocess, time, sqlite3, re
from pathlib import Path

DB = Path("database/garment.db")
BASE = "http://partsbook.brother.co.jp/public/img/files"

MACHINES = [
    (95, "T-8450C"), (91, "T-8452C"), (96, "T-8720C"),
    (92, "T-8722C"), (97, "T-8750C"), (93, "T-8752C"),
]

def fetch_curl(url, out_file):
    """Download via curl, return True jika berhasil (bukan HTML)."""
    tmp = "tmp/_dl.svg"
    r = subprocess.run(
        ["curl", "-s", "-A", "Mozilla/5.0", "-o", tmp, "-w", "%{http_code}", url],
        capture_output=True, text=True, timeout=60
    )
    if r.stdout.strip() != "200":
        return False
    data = Path(tmp).read_bytes()
    if data[:15] == b"<!DOCTYPE html>" or b"<html" in data[:200]:
        return False
    Path(out_file).write_bytes(data)
    return True

conn = sqlite3.connect(DB)
cur = conn.cursor()

for db_id, model in MACHINES:
    print(f"\n=== {model} ===")
    cur.execute("SELECT id, catalog_ref, component_name FROM components WHERE machine_id=? ORDER BY CAST(catalog_ref AS INTEGER)", (db_id,))
    comps = cur.fetchall()
    
    prefix = model.lower().replace("-", "")
    out_dir = Path(f"static/images/mechanisms/brother/{prefix}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    ok = 0
    skip = []
    for comp_id, ref, name in comps:
        m = re.match(r'^([A-Za-z]+\d*(?:-\d+)?)\s*\.', name)
        if not m:
            skip.append(name); continue
        code = m.group(1).lower()
        out = out_dir / f"section-{int(ref):02d}.svg"
        
        # Coba prefix sendiri, lalu fallback
        if fetch_curl(f"{BASE}/{prefix}_{code}.svg", out):
            ok += 1
        elif fetch_curl(f"{BASE}/t_8421c_{code}.svg", out):
            ok += 1
        elif fetch_curl(f"{BASE}/t_8422c_{code}.svg", out):
            ok += 1
        else:
            skip.append(f"{name} ({code})")
        time.sleep(0.4)
    
    print(f"  {ok}/{len(comps)} SVG berhasil")
    if skip:
        print(f"  SKIP: {', '.join(skip)}")

conn.close()
print("\n[SELESAI]")
