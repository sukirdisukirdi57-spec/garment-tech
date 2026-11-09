import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
SOURCE = Path("tmp/ams221en-diagram-check")
TARGET = Path("static/component_images")

MACHINE_ID = 45

items = {
    406: (14, "ams221en_page14.jpg", "page-14.jpg"),
    408: (18, "ams221en_page18.jpg", "page-18.jpg"),
    429: (42, "ams221en_page42.jpg", "page-42.jpg"),
    431: (42, "ams221en_page42.jpg", "page-42.jpg"),
    432: (46, "ams221en_page46.jpg", "page-46.jpg"),
}

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

for cid, (page, filename, source_name) in items.items():
    src = SOURCE / source_name
    if not src.is_file():
        raise SystemExit(f"Gambar sumber tidak ditemukan: {src}")

TARGET.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    # Validasi komponen dan relasi main-part sebelum perubahan.
    for cid, (page, filename, source_name) in items.items():
        component = con.execute("""
            SELECT id, machine_id, component_name
            FROM components
            WHERE id = ? AND machine_id = ?
        """, (cid, MACHINE_ID)).fetchone()

        if not component:
            raise RuntimeError(
                f"Komponen {cid} tidak ditemukan pada machine_id {MACHINE_ID}"
            )

        relation = con.execute("""
            SELECT id FROM component_parts
            WHERE component_id = ? AND relation_type = 'main-part'
        """, (cid,)).fetchone()

        if not relation:
            raise RuntimeError(f"Relasi main-part komponen {cid} tidak ditemukan")

        print(f"VALID: {cid} | {component['component_name']} | page {page}")

    # Backup database sebelum mengubah data.
    backup = DB.with_name(
        f"garment-before-fix-ams221en-diagrams-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    shutil.copy2(DB, backup)
    print(f"\nBACKUP: {backup}")

    # Salin gambar diagram ke static.
    for cid, (page, filename, source_name) in items.items():
        src = SOURCE / source_name
        dst = TARGET / filename
        shutil.copy2(src, dst)
        print(f"GAMBAR: {src} -> {dst}")

    # Perbarui hanya kolom diagram komponen.
    con.execute("BEGIN")
    for cid, (page, filename, source_name) in items.items():
        con.execute("""
            UPDATE components
            SET diagram_page = ?, image_path = ?
            WHERE id = ? AND machine_id = ?
        """, (page, f"component_images/{filename}", cid, MACHINE_ID))

    con.commit()

    print("\n=== HASIL VERIFIKASI ===")
    for cid in items:
        row = con.execute("""
            SELECT id, component_name, diagram_page, image_path
            FROM components
            WHERE id = ? AND machine_id = ?
        """, (cid, MACHINE_ID)).fetchone()
        print(dict(row))

    print("\nBERHASIL: 5 komponen diperbarui.")
    print("parts.diagram_page dan component_parts tidak diubah.")

except Exception:
    con.rollback()
    raise
finally:
    con.close()
