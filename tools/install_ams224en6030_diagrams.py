import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
DB = ROOT / "database/garment.db"
SOURCE = ROOT / "tmp/ams224en6030-diagram-check"

TARGET = ROOT / "static/component_images"
TARGET.mkdir(parents=True, exist_ok=True)

items = [
    {
        "id": 598,
        "page": 12,
        "source": SOURCE / "frame-6030.png",
        "filename": "ams224en6030_frame_6030_page12.png",
        "expected_relations": 91,
    },
    {
        "id": 599,
        "page": 32,
        "source": SOURCE / "xy-6030.png",
        "filename": "ams224en6030_xy_6030_page32.png",
        "expected_relations": 96,
    },
]

# Pemeriksaan awal file
for item in items:
    path = item["source"]
    if not path.is_file():
        raise SystemExit(f"FILE SUMBER TIDAK ADA: {path}")
    if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"FILE BUKAN PNG VALID: {path}")

if not DB.is_file():
    raise SystemExit(f"DATABASE TIDAK DITEMUKAN: {DB}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    print("=== PREFLIGHT DATABASE ===")

    for item in items:
        row = con.execute("""
            SELECT id, machine_id, component_name,
                   diagram_page, image_path
            FROM components
            WHERE id = ?
        """, (item["id"],)).fetchone()

        if not row:
            raise RuntimeError(f"Component ID {item['id']} tidak ditemukan")

        if row["machine_id"] != 47:
            raise RuntimeError(
                f"Machine ID tidak cocok untuk component {item['id']}"
            )

        count = con.execute("""
            SELECT COUNT(*)
            FROM component_parts
            WHERE component_id = ?
        """, (item["id"],)).fetchone()[0]

        if count != item["expected_relations"]:
            raise RuntimeError(
                f"Relasi ID {item['id']} berubah: "
                f"{count}, seharusnya {item['expected_relations']}"
            )

        print(dict(row))
        print("Relasi:", count)

    # Backup database sebelum perubahan
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.parent / f"garment-before-ams224-diagrams-{stamp}.db"

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()

    print("\nBACKUP:", backup)

    # Salin gambar diagram asli
    for item in items:
        destination = TARGET / item["filename"]
        shutil.copy2(item["source"], destination)
        print("GAMBAR:", destination)

    # Update database dalam satu transaksi
    try:
        con.execute("BEGIN IMMEDIATE")

        for item in items:
            image_path = f"component_images/{item['filename']}"

            con.execute("""
                UPDATE components
                SET diagram_page = ?,
                    image_path = ?
                WHERE id = ?
                  AND machine_id = 47
            """, (
                item["page"],
                image_path,
                item["id"],
            ))

        con.commit()

    except Exception:
        con.rollback()
        raise

    print("\n=== VERIFIKASI AKHIR ===")

    for item in items:
        row = con.execute("""
            SELECT id, machine_id, component_name,
                   diagram_page, image_path
            FROM components
            WHERE id = ?
        """, (item["id"],)).fetchone()

        count = con.execute("""
            SELECT COUNT(*)
            FROM component_parts
            WHERE component_id = ?
        """, (item["id"],)).fetchone()[0]

        image_file = ROOT / "static" / row["image_path"]

        assert row["diagram_page"] == item["page"]
        assert image_file.is_file()
        assert count == item["expected_relations"]

        print(dict(row))
        print("Relasi:", count)
        print("File gambar tersedia:", image_file.is_file())

    print("\nAUDIT LULUS — 2 DIAGRAM TERPASANG")
    print("187 RELASI PART TETAP UTUH")

finally:
    con.close()
