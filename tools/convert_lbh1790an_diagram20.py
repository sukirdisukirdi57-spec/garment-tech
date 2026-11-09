import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")
IMAGE = "component_images/lbh1790an_diagram20.png"

MACHINE_ID = 6
DOCUMENT_ID = 119
DIAGRAM_PAGE = 37
COMPONENT_ID = 241
COMPONENT_NAME = "20. EXCHANGING PARTS"
EXPECTED_OLD_PART = "B2702-047-L00-A"

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
        WHERE machine_id=?
          AND source_document_id=?
          AND diagram_page=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

    print("=== PREFLIGHT DIAGRAM 20 ===")
    print("Jumlah part:", len(parts))

    refs = [int(p["catalog_ref"]) for p in parts]
    if refs != list(range(1, 33)):
        raise RuntimeError(f"REF tidak lengkap: {refs}")

    for p in parts:
        print(
            f'REF {p["catalog_ref"]:>2} | '
            f'{p["part_number"]:<20} | {p["part_name"]}'
        )

    component = db.execute("""
        SELECT *
        FROM components
        WHERE id=? AND machine_id=? AND diagram_page=?
    """, (COMPONENT_ID, MACHINE_ID, DIAGRAM_PAGE)).fetchone()

    if not component:
        raise RuntimeError("Komponen lama ID 241 tidak ditemukan.")

    if component["part_number"] != EXPECTED_OLD_PART:
        raise RuntimeError(
            "Part number komponen lama tidak sesuai: "
            f'{component["part_number"]}'
        )

    if component["component_name"] != "Knife 1/2":
        raise RuntimeError(
            "Nama komponen lama berubah: "
            f'{component["component_name"]}'
        )

    ref4 = next(
        (p for p in parts if int(p["catalog_ref"]) == 4),
        None
    )
    if not ref4 or ref4["part_number"] != EXPECTED_OLD_PART:
        raise RuntimeError("REF 4 tidak cocok dengan komponen lama.")

    old_relations = db.execute("""
        SELECT part_id, notes
        FROM component_parts
        WHERE component_id=?
    """, (COMPONENT_ID,)).fetchall()

    if old_relations:
        raise RuntimeError(
            f"Komponen 241 sudah memiliki relasi: "
            f"{[dict(x) for x in old_relations]}"
        )

    other_relations = db.execute("""
        SELECT p.catalog_ref, p.part_number,
               cp.component_id, c.component_name
        FROM parts p
        JOIN component_parts cp ON cp.part_id=p.id
        JOIN components c ON c.id=cp.component_id
        WHERE p.machine_id=?
          AND p.source_document_id=?
          AND p.diagram_page=?
    """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

    if other_relations:
        raise RuntimeError(
            f"Part sudah terhubung ke komponen lain: "
            f"{[dict(x) for x in other_relations]}"
        )

    image_path = Path("static") / IMAGE
    if not image_path.is_file():
        raise RuntimeError(f"Gambar tidak ditemukan: {image_path}")

    print("\nValidasi REF 1-32: LULUS")
    print("Validasi komponen lama ID 241: LULUS")
    print("Validasi kecocokan REF 4: LULUS")
    print("Validasi relasi lama: LULUS")
    print("Validasi gambar: LULUS")

    if not args.apply:
        print("\nDRY-RUN: database belum diubah.")
        raise SystemExit(0)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / (
        f"garment-before-lbh1790an-diagram20-{timestamp}.db"
    )
    shutil.copy2(DB, backup)
    print("\nBackup:", backup)

    try:
        db.execute("BEGIN IMMEDIATE")

        old_notes = component["notes"] or ""
        history = (
            "Riwayat entri lama: Knife 1/2; "
            "part number B2702-047-L00-A; "
            "location: Area cloth cutting; "
            "function: Memotong material pada mekanisme pemotong. "
            "Dikonversi menjadi komponen katalog Diagram 20."
        )
        new_notes = (
            old_notes + "\n" + history
            if old_notes else history
        )

        db.execute("""
            UPDATE components
            SET component_name=?,
                catalog_ref=?,
                image_path=?,
                notes=?
            WHERE id=?
        """, (
            COMPONENT_NAME,
            "1-32",
            IMAGE,
            new_notes,
            COMPONENT_ID
        ))

        for p in parts:
            db.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, ?, ?)
            """, (
                COMPONENT_ID,
                p["id"],
                "catalog_component_part",
                f'REF {p["catalog_ref"]}'
            ))

        db.commit()

        print("\nKONVERSI BERHASIL")
        print("Component ID dipertahankan:", COMPONENT_ID)
        print("Nama baru:", COMPONENT_NAME)
        print("Relasi dibuat:", len(parts))

    except Exception:
        db.rollback()
        raise

    backups = sorted(
        BACKUP_DIR.glob("garment-before-lbh1790an-diagram20-*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for old in backups[10:]:
        old.unlink()

    print("Backup dipertahankan: 10")

finally:
    db.close()
