import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram16.png")
TITLE = "16. ACCESSORIE PARTS COMPONENTS"
SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

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
    # Validasi sumber dan seluruh REF.
    rows = db.execute("""
        SELECT id, catalog_ref, part_number, part_name
        FROM parts
        WHERE machine_id = 6
          AND source_document_id = 119
          AND diagram_page = 29
        ORDER BY CAST(catalog_ref AS INTEGER)
    """).fetchall()

    refs = [int(r["catalog_ref"]) for r in rows]

    if len(rows) != 34 or refs != list(range(1, 35)):
        raise SystemExit(
            f"ERROR: REF tidak lengkap. Jumlah={len(rows)}, REF={refs}"
        )

    # Pastikan komponen belum dibuat.
    existing = db.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id = 6
          AND diagram_page = 29
    """).fetchall()

    if existing:
        raise SystemExit(
            "ERROR: Sudah ada komponen pada Diagram 16: "
            + str([dict(r) for r in existing])
        )

    # Pastikan 34 part belum memiliki relasi.
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

    print("=== PREFLIGHT DIAGRAM 16 ===")
    print("Komponen :", TITLE)
    print("Machine  : 6")
    print("Dokumen  : 119")
    print("Halaman  : 29")
    print("REF      : 1-34")
    print("Jumlah   :", len(rows))
    print("Gambar   :", IMAGE)
    print("Relasi lama: 0")
    print("\nDaftar REF:")
    for r in rows:
        print(
            f'{int(r["catalog_ref"]):02} | '
            f'{r["part_number"]} | {r["part_name"]}'
        )

    if not args.apply:
        print("\nDRY-RUN: database belum diubah.")
        print("Jika hasil benar, jalankan dengan --apply.")
        raise SystemExit(0)

    # Backup sebelum perubahan.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.parent / f"garment-before-lbh1790an-diagram16-{stamp}.db"
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
            "Catalog Diagram 16",
            "Catalog component and assembly grouping.",
            "Main component for all REF entries in Diagram 16.",
            "component_images/lbh1790an_diagram16.png",
            SOURCE_URL,
            "1-34",
            29
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

    # Pertahankan maksimal 10 backup terbaru.
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
