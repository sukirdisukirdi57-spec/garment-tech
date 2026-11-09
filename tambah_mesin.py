#!/usr/bin/env python3
"""Script tambah mesin baru + backup otomatis + verifikasi."""
import sqlite3, shutil, sys, os
from datetime import datetime

DB = "database/garment.db"

def backup(db_path, label):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = f"{db_path}.backup-{label}-{ts}"
    shutil.copy2(db_path, dst)
    print(f"[BACKUP] {dst}")
    return dst

def get_or_create_brand(cur, name, country=None, website=None):
    cur.execute("SELECT id FROM brands WHERE name = ?", (name,))
    row = cur.fetchone()
    if row: return row[0]
    cur.execute("INSERT INTO brands(name,country,official_website) VALUES(?,?,?)",
                (name, country, website))
    print(f"[BRAND BARU] {name} (id={cur.lastrowid})")
    return cur.lastrowid

def get_machine_type_id(cur, name):
    cur.execute("SELECT id FROM machine_types WHERE name = ?", (name,))
    row = cur.fetchone()
    return row[0] if row else None

def tambah_mesin(data):
    db = DB
    backup(db, data["model"].replace("/", "-").lower())

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        brand_id = get_or_create_brand(cur, data["brand"])
        type_id = get_machine_type_id(cur, data.get("machine_type"))

        cur.execute("""INSERT INTO machines(brand_id, machine_type_id, model, function, description, notes)
                       VALUES(?,?,?,?,?,?)""",
                    (brand_id, type_id, data["model"], data.get("function"),
                     data.get("description"), data.get("notes")))
        mid = cur.lastrowid
        print(f"[MESIN] id={mid} {data['brand']} {data['model']}")

        # Spesifikasi
        for s in data.get("specs", []):
            cur.execute("""INSERT INTO specifications(machine_id, specification, value, notes, description)
                           VALUES(?,?,?,?,?)""",
                        (mid, s["spec"], s.get("value"), s.get("notes"), s.get("description")))
        print(f"[SPEC] {len(data.get('specs', []))} baris")

        # Parts
        for p in data.get("parts", []):
            cur.execute("""INSERT INTO parts(machine_id, part_number, part_name, quantity,
                           catalog_ref, diagram_page, note, source_url)
                           VALUES(?,?,?,?,?,?,?,?)""",
                        (mid, p["part_number"], p["part_name"], p.get("qty"),
                         p.get("catalog_ref"), p.get("diagram_page"),
                         p.get("note"), p.get("source_url")))
        print(f"[PARTS] {len(data.get('parts', []))} baris")

        # Troubleshooting
        for t in data.get("troubleshooting", []):
            cur.execute("""INSERT INTO troubleshooting(machine_id, problem, symptoms,
                           possible_cause, solution, safety_notes, source, code)
                           VALUES(?,?,?,?,?,?,?,?)""",
                        (mid, t["problem"], t.get("symptoms"), t.get("possible_cause"),
                         t.get("solution"), t.get("safety_notes"), t.get("source"), t.get("code")))
        print(f"[TROUBLE] {len(data.get('troubleshooting', []))} baris")

        # Alarms
        for a in data.get("alarms", []):
            cur.execute("""INSERT INTO machine_alarms(machine_id, alarm_code, alarm_name,
                           possible_cause, solution, manual_title, manual_version,
                           manual_chapter, manual_page, source_url, source_note)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (mid, a["code"], a["name"], a.get("possible_cause"), a.get("solution"),
                         a["manual_title"], a.get("manual_version"), a.get("manual_chapter"),
                         a.get("manual_page"), a.get("source_url"), a.get("source_note")))
        print(f"[ALARM] {len(data.get('alarms', []))} baris")

        conn.commit()
        print(f"\n✅ SUKSES — machine_id = {mid}")
        return mid
    except Exception as e:
        conn.rollback()
        print(f"\n❌ GAGAL: {e}\nRollback. Database tidak berubah.")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Script siap. Import: from tambah_mesin import tambah_mesin")
