import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram17.png")
TITLE = "17. THREAD STAND COMPONENTS"

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

if not DB.is_file():
    raise SystemExit("ERROR: database/garment.db tidak ditemukan.")
if not IMAGE.is_file():
    raise SystemExit(f"ERROR: gambar tidak ditemukan: {IMAGE}")

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

try:
    rows = db.execute("""
        SELECT id, catalog_ref, part_number, part_name
        FROM parts
        WHERE machine_id = 6
          AND source_document_id = 119
          AND diagram_page = 31
        ORDER BY CAST(catalog_ref AS INTEGER)
    """).fetchall()

    refs = [int(r["catalog_ref"]) for r in rows]

    if len(rows) != 24 or refs != list(range(1, 25)):
        raise SystemExit(
            f"ERROR: REF tidak lengkap. Jumlah={len(rows)}, REF={refs}"
        )

    existing = db.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id = 6 AND diagram_page = 31
    """).fetchall()

    if existing:
        raise SystemExit(
            "ERROR: Komponen Diagram 17 sudah ada: "
            + str([dict(r) for r in existing])
        )

    part_ids = [r["id"] for r in rows]
    placeholders = ",".join("?" for _ in part_ids)

    linked = db.execute(f"""
        SELECT part_id, COUNT(*) AS total
        FROM component_parts
        WHERE part_id IN ({placeholders})
        GROUP BY part_id
    """, part_ids).fetchall()

    if linked:
        raise SystemExit(
            "ERROR: Ada part yang sudah memiliki relasi: "
            + str([dict(r) for r in linked])
        )

    print("=== PREFLIGHT DIAGRAM 17 ===")
    print("Komponen :", TITLE)
    print("Machine  : 6")
    print("Dokumen  : 119")
    print("Halaman  : 31")
    print("REF      : 1-24")
    print("Jumlah   :", len(rows))
    print("Gambar   :", IMAGE)
    print("Relasi lama: 0")

    for r in rows:
        print(
            f'{int(r["catalog_ref"]):02} | '
            f'{r["part_number"]} | {r["part_name"]}'
        )

    if not args.apply:
        print("\nDRY-RUN: database belum diubah.")
        print("Jika hasil benar, jalankan dengan --apply.")
        raise SystemExit(0)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.parent / (
        f"garment-before-lbh1790an-diagram17-{stamp}.db"
    )
    shutil.copy2(DB, backup)
    print("\nBackup:", backup)

    try:
        db.execute("BEGIN IMMEDIATE")

        cur = db.execute("""
            INSERT INTO components (
                machine_id, component_name, location, function,
                notes, image_path, source_url, catalog_ref, diagram_page
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            6,
            TITLE,
            "Catalog Diagram 17",
            "Catalog component and assembly grouping.",
            "Main component for all REF entries in Diagram 17.",
            "component_images/lbh1790an_diagram17.png",
            "",
            "1-24",
            31
        ))

        component_id = cur.lastrowid

        db.executemany("""
            INSERT INTO component_parts (
                component_id, part_id, relation_type, notes
            ) VALUES (?, ?, ?, ?)
        """, [
            (
                component_id,
                r["id"],
                "catalog_component_part",
                f'REF {r["catalog_ref"]}'
            )
            for r in rows
        ])

        db.commit()

        print("\nIMPORT BERHASIL")
        print("Component ID:", component_id)
        print("Relasi dibuat:", len(rows))

    except Exception:
        db.rollback()
        raise

    backups = sorted(
        DB.parent.glob("garment-before-*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    removed = backups[10:]
    for path in removed:
        path.unlink()

    print("Backup dipertahankan:", min(len(backups), 10))
    print("Backup lama dihapus:", len(removed))

finally:
    db.close()
