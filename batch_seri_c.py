#!/usr/bin/env python3
"""Batch proses 6 mesin seri C Brother: scrape -> rebuild -> SVG -> image_path."""
import re, csv, time, sqlite3, shutil, urllib.request
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BASE = "http://partsbook.brother.co.jp/pub/machine"

MACHINES = [
    (95, 35, "T-8450C"),
    (91, 38, "T-8452C"),
    (96, 41, "T-8720C"),
    (92, 44, "T-8722C"),
    (97, 46, "T-8750C"),
    (93, 49, "T-8752C"),
]

ROW_PATTERN = re.compile(
    r'<tr[^>]*num="(\d+)"[^>]*>.*?'
    r'<td[^>]*>(\d+)</td>.*?'
    r'<td[^>]*>(\d+(?:\.\d+)?)</td>.*?'
    r'<td class="align_c">.*?</td>.*?'
    r'<td[^>]*>([A-Z0-9][A-Z0-9\-]*)</td>.*?'
    r'<td>([^<]*)</td>',
    re.DOTALL
)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read()

def get_sections(brother_id):
    html = fetch(f"{BASE}/index/en/{brother_id}").decode("utf-8", "ignore")
    pattern = r'<td[^>]*>([A-Z][^<]+)</td>.*?detail/en/' + str(brother_id) + r'/(\d+)'
    result = []
    for m in re.finditer(pattern, html, re.DOTALL):
        name = m.group(1).strip()
        sid = int(m.group(2))
        # Skip gauge parts list
        if name.startswith("Ga-"):
            continue
        result.append((sid, name))
    return result

def scrape_section(brother_id, sid, name, order):
    html = fetch(f"{BASE}/detail/en/{brother_id}/{sid}").decode("utf-8", "ignore")
    matches = ROW_PATTERN.findall(html)
    seen = set()
    rows = []
    for num, ref, qty, code, pname in matches:
        key = (ref, code)
        if key in seen: continue
        seen.add(key)
        rows.append({
            "section_ref": order,
            "section_name": name,
            "catalog_ref": int(ref),
            "part_number": code,
            "part_name": pname.strip(),
            "quantity": qty,
        })
    return rows

def process_machine(db_id, brother_id, model):
    print(f"\n{'='*60}")
    print(f"PROSES {model} (DB={db_id}, Brother={brother_id})")
    print(f"{'='*60}")

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = DB.with_name(f"{DB.name}.backup-batch-{model.lower()}-{ts}")
    shutil.copy2(DB, bak)
    print(f"[BACKUP] {bak}")

    # 1. Scrape sections
    sections = get_sections(brother_id)
    print(f"[SECTION] {len(sections)} section ditemukan")

    # 2. Scrape parts
    all_rows = []
    for order, (sid, name) in enumerate(sections, 1):
        try:
            rows = scrape_section(brother_id, sid, name, order)
            all_rows.extend(rows)
            print(f"  [{order:>2}] {name[:45]:<45} {len(rows)} parts")
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
        time.sleep(0.7)

    if not all_rows:
        print(f"[SKIP] {model}: tidak ada parts")
        return

    # 3. Rebuild parts
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT model FROM machines WHERE id=?", (db_id,))
    row = cur.fetchone()
    if not row or row[0] != model:
        print(f"[BATAL] machine_id={db_id} bukan {model}")
        conn.close(); return

    cur.execute("""DELETE FROM component_parts WHERE component_id IN
                   (SELECT id FROM components WHERE machine_id=?)""", (db_id,))
    cur.execute("DELETE FROM parts WHERE machine_id=?", (db_id,))
    cur.execute("DELETE FROM components WHERE machine_id=?", (db_id,))

    section_pages = {i: (2*i - 1) for i in range(1, len(sections)+1)}
    for r in all_rows:
        qty_clean = str(r["quantity"]).strip("()")
        try:
            qty = int(float(qty_clean)) if qty_clean else None
        except ValueError:
            qty = None
        cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                       quantity, catalog_ref, diagram_page, section_ref, section_name)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (db_id, r["part_number"], r["part_name"], qty,
                     r["catalog_ref"], section_pages.get(r["section_ref"]),
                     r["section_ref"], r["section_name"]))
    conn.commit()
    print(f"[PARTS] {len(all_rows)} parts inserted")

    # 4. Buat komponen + relasi
    for order, (sid, name) in enumerate(sections, 1):
        cur.execute("""SELECT part_number FROM parts
                       WHERE machine_id=? AND section_ref=?
                       ORDER BY catalog_ref LIMIT 1""", (db_id, order))
        r = cur.fetchone()
        main_pn = r[0] if r else None
        cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                       location, catalog_ref, diagram_page)
                       VALUES(?,?,?,?,?,?)""",
                    (db_id, name, main_pn, name, str(order), section_pages[order]))
    conn.commit()

    cur.execute("SELECT id, catalog_ref, part_number FROM components WHERE machine_id=?", (db_id,))
    comps = {int(r[1]): (r[0], r[2]) for r in cur.fetchall()}
    total_rel = 0
    for ref, (comp_id, comp_pn) in sorted(comps.items()):
        cur.execute("SELECT id, part_number FROM parts WHERE machine_id=? AND section_ref=?", (db_id, ref))
        parts = cur.fetchall()
        for pid, pn in parts:
            rel = "matched_catalog_part" if pn == comp_pn else "sub-part"
            try:
                cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                               VALUES(?,?,?)""", (comp_id, pid, rel))
                total_rel += 1
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    print(f"[KOMPONEN] {len(comps)} dibuat, {total_rel} relasi")

    conn.close()

if __name__ == "__main__":
    for db_id, brother_id, model in MACHINES:
        process_machine(db_id, brother_id, model)
    print("\n\n[SELESAI BATCH]")
