import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")
IMAGE = "component_images/lbh1790an_diagram18.png"

MACHINE_ID = 6
DOCUMENT_ID = 119
DIAGRAM_PAGE = 33
COMPONENT_NAME = "18. SPECIAL SPECIFICATIONS COMPONENTS (1)"

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

try:
    db.execute("PRAGMA foreign_keys=ON")

    parts = db.execute("""
        SELECT id, catalog_ref, part_number, part_name
        FROM parts
        WHERE machine_id=? AND source_document_id=? AND diagram_page=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

    print("=== PREFLIGHT DIAGRAM 18 ===")
    print("Jumlah part:", len(parts))

    refs = [int(p["catalog_ref"]) for p in parts]
    expected = list(range(1, 42))

    if refs != expected:
        raise RuntimeError(
            f"REF tidak lengkap/berurutan. Ditemukan: {refs}"
        )

    for p in parts:
        print(
            f'REF {p["catalog_ref"]:>2} | '
            f'{p["part_number"]:<20} | {p["part_name"]}'
        )

    existing = db.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND diagram_page=?
    """, (MACHINE_ID, DIAGRAM_PAGE)).fetchall()

    if existing:
        raise RuntimeError(
            f"Komponen diagram sudah ada: {[dict(x) for x in existing]}"
        )

    related = db.execute("""
        SELECT p.catalog_ref, p.part_number, cp.component_id
        FROM component_parts cp
        JOIN parts p ON p.id=cp.part_id
        WHERE p.machine_id=?
          AND p.source_document_id=?
          AND p.diagram_page=?
    """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

    if related:
        raise RuntimeError(
            f"Sebagian part sudah memiliki relasi: {[dict(x) for x in related]}"
        )

    image_path = Path("static") / IMAGE
    if not image_path.is_file():
        raise RuntimeError(f"Gambar tidak ditemukan: {image_path}")

    print("\nValidasi REF 1-41: LULUS")
    print("Validasi komponen lama: LULUS")
    print("Validasi relasi lama: LULUS")
    print("Validasi gambar: LULUS")

    if not args.apply:
        print("\nDRY-RUN: database belum diubah.")
        raise SystemExit(0)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"garment-before-lbh1790an-diagram18-{timestamp}.db"
    shutil.copy2(DB, backup)
    print("\nBackup:", backup)

    try:
        db.execute("BEGIN IMMEDIATE")

        cur = db.execute("""
            INSERT INTO components (
                machine_id, component_name, catalog_ref,
                diagram_page, image_path
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
            "1-41",
            DIAGRAM_PAGE,
            IMAGE
        ))

        component_id = cur.lastrowid

        for p in parts:
            db.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, ?, ?)
            """, (
                component_id,
                p["id"],
                "catalog_component_part",
                f'REF {p["catalog_ref"]}'
            ))

        db.commit()
        print("\nIMPORT BERHASIL")
        print("Component ID:", component_id)
        print("Relasi dibuat:", len(parts))

    except Exception:
        db.rollback()
        raise

    backups = sorted(
        BACKUP_DIR.glob("garment-before-lbh1790an-diagram18-*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for old in backups[10:]:
        old.unlink()

    print("Backup dipertahankan: 10")

finally:
    db.close()
