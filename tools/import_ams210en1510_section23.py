from pathlib import Path
import sqlite3
import sys
import shutil
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/images/mechanisms/juki/ams210en/pdf-page-46.jpg")
IMAGE_DB = "images/mechanisms/juki/ams210en/pdf-page-46.jpg"
SOURCE = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

MACHINE_ID = 15
DOC_ID = 136
TITLE = "23. PEDAL COMPONENTS"
ROWS = [
    (1, "#01", "400-33831", "PK78 PEDAL SWITCH ASM.", 1, "1"),
    (2, "#02", "GPK-470010AB", "3-PEDAL ASM.", 1, "1"),
    (3, "#02", "400-33875", "PK47 RELAY CABLE ASM.", 1, "1"),
]

if not DB.is_file():
    raise SystemExit("ERROR: database tidak ditemukan.")
if not IMAGE.is_file():
    raise SystemExit("ERROR: gambar halaman 46 tidak ditemukan.")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

machine = con.execute(
    "SELECT id, model FROM machines WHERE id=?",
    (MACHINE_ID,)
).fetchone()
doc = con.execute("""
    SELECT id, title, source_url
    FROM documents
    WHERE id=? AND machine_id=?
""", (DOC_ID, MACHINE_ID)).fetchone()

print("=== PREFLIGHT SECTION 23 ===")
print("Machine:", dict(machine) if machine else None)
print("Dokumen:", dict(doc) if doc else None)
print("Judul:", TITLE)
print("REF katalog:", len(ROWS))
print("Gambar:", IMAGE, "| Ada:", IMAGE.is_file())

if not machine or machine["model"] != "AMS-210EN-1510":
    raise SystemExit("STOP: machine tidak sesuai.")
if not doc or doc["source_url"] != SOURCE:
    raise SystemExit("STOP: dokumen tidak sesuai.")

existing_component = con.execute("""
    SELECT id, component_name
    FROM components
    WHERE machine_id=? AND catalog_ref='23'
""", (MACHINE_ID,)).fetchall()
if existing_component:
    print("Komponen lama:", [dict(x) for x in existing_component])
    raise SystemExit("STOP: catalog_ref 23 sudah digunakan.")

for ref, marker, pn, name, qty, qty_raw in ROWS:
    matches = con.execute("""
        SELECT id, part_name, quantity, quantity_raw,
               catalog_ref, note, notes
        FROM parts
        WHERE machine_id=? AND part_number=?
    """, (MACHINE_ID, pn)).fetchall()

    print(
        f"REF{ref} | {pn} | {name} | Qty {qty_raw} | "
        f"{marker} | Existing: {len(matches)}"
    )
    if matches:
        for x in matches:
            print("  ", dict(x))
        raise SystemExit(
            f"STOP: part number {pn} ternyata sudah ada."
        )

if "--apply" not in sys.argv:
    print("\nDRY-RUN: belum ada perubahan database.")
    con.close()
    raise SystemExit(0)

backup = Path(
    "database/garment-before-ams210en1510-section23-"
    + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)
con.close()
shutil.copy2(DB, backup)
print("\nBackup:", backup)

con = sqlite3.connect(DB)
try:
    con.execute("BEGIN IMMEDIATE")

    if con.execute("""
        SELECT 1 FROM components
        WHERE machine_id=? AND catalog_ref='23'
    """, (MACHINE_ID,)).fetchone():
        raise RuntimeError("Komponen catalog_ref 23 sudah dibuat.")

    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, function, notes,
            image_path, source_url, catalog_ref, diagram_page
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        MACHINE_ID, TITLE, "Pedal components",
        "Section 23 dari JUKI AMS-210EN Series Parts List.",
        IMAGE_DB, SOURCE, "23", 41
    ))
    component_id = cur.lastrowid

    for ref, marker, pn, name, qty, qty_raw in ROWS:
        if con.execute("""
            SELECT 1 FROM parts
            WHERE machine_id=? AND part_number=?
        """, (MACHINE_ID, pn)).fetchone():
            raise RuntimeError(f"Part number muncul saat apply: {pn}")

        pcur = con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number,
                part_name, quantity, quantity_raw, catalog_ref,
                diagram_page, note, source_url, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, DOC_ID, pn, name, qty, qty_raw,
            str(ref), 41, marker, SOURCE, None
        ))

        con.execute("""
            INSERT INTO component_parts (
                component_id, part_id, relation_type, notes
            ) VALUES (?, ?, ?, ?)
        """, (
            component_id, pcur.lastrowid,
            "catalog_component_part", f"REF {ref}"
        ))

    con.commit()
    print("\nAPPLY BERHASIL")
    print("Component ID:", component_id)
    print("Part baru:", len(ROWS))
    print("Relasi baru:", len(ROWS))
    print("Backup:", backup)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
