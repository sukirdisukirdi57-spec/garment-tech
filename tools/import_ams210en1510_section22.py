from pathlib import Path
import sqlite3
import shutil
import sys
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/images/mechanisms/juki/ams210en/pdf-page-44.jpg")
IMAGE_DB = "images/mechanisms/juki/ams210en/pdf-page-44.jpg"
SOURCE = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

MACHINE_ID = 15
TITLE = "22. WIRING DIAGRAM"
CATALOG_REF = "22"
DIAGRAM_PAGE = 39

if not DB.is_file():
    raise SystemExit("ERROR: database tidak ditemukan.")
if not IMAGE.is_file():
    raise SystemExit(f"ERROR: gambar tidak ditemukan: {IMAGE}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

machine = con.execute(
    "SELECT id, model FROM machines WHERE id=?",
    (MACHINE_ID,)
).fetchone()

document = con.execute("""
    SELECT id, title, source_url
    FROM documents
    WHERE id=136 AND machine_id=?
""", (MACHINE_ID,)).fetchone()

existing = con.execute("""
    SELECT id, component_name, catalog_ref, diagram_page, image_path
    FROM components
    WHERE machine_id=? AND component_name=?
""", (MACHINE_ID, TITLE)).fetchall()

print("=== PREFLIGHT SECTION 22 ===")
print("Machine:", dict(machine) if machine else None)
print("Dokumen:", dict(document) if document else None)
print("Judul:", TITLE)
print("Catalog ref:", CATALOG_REF)
print("Diagram page:", DIAGRAM_PAGE)
print("Image:", IMAGE, "| Ada:", IMAGE.is_file())
print("Komponen dengan judul sama:", [dict(x) for x in existing])

if not machine or machine["model"] != "AMS-210EN-1510":
    raise SystemExit("STOP: machine tidak sesuai.")
if not document or document["source_url"] != SOURCE:
    raise SystemExit("STOP: dokumen atau source URL tidak sesuai.")
if existing:
    raise SystemExit("STOP: komponen dengan judul ini sudah ada.")

if "--apply" not in sys.argv:
    print("\nDRY-RUN: belum ada perubahan database.")
    con.close()
    raise SystemExit(0)

backup = Path(
    "database/garment-before-ams210en1510-section22-"
    + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)
con.close()
shutil.copy2(DB, backup)
print("\nBackup:", backup)

con = sqlite3.connect(DB)
try:
    con.execute("BEGIN IMMEDIATE")

    # Periksa ulang setelah backup sebelum insert.
    duplicate = con.execute("""
        SELECT id FROM components
        WHERE machine_id=? AND component_name=?
    """, (MACHINE_ID, TITLE)).fetchone()

    if duplicate:
        raise RuntimeError(
            f"Komponen sudah dibuat oleh proses lain: ID {duplicate[0]}"
        )

    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, part_number, location,
            function, notes, image_path, source_url,
            catalog_ref, diagram_page
        )
        VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?)
    """, (
        MACHINE_ID,
        TITLE,
        "Wiring diagram",
        "Diagram kelistrikan; tidak memiliki tabel REF part.",
        IMAGE_DB,
        SOURCE,
        CATALOG_REF,
        DIAGRAM_PAGE
    ))

    component_id = cur.lastrowid
    con.commit()

    print("\nAPPLY BERHASIL")
    print("Component ID:", component_id)
    print("Part baru: 0")
    print("Relasi baru: 0")
    print("Backup:", backup)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
