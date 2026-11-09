import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
DB = ROOT / "database/garment.db"
SOURCE = ROOT / "tmp/ams221en-visual-audit"
DEST = ROOT / "static/component_images"

mapping = {
    403: 8,
    409: 20,
    410: 20,
    411: 22,
    415: 24,
    416: 24,
    418: 30,
    423: 38,
    424: 39,
    425: 40,
    426: 40,
    427: 42,
    428: 42,
    429: 42,
    430: 42,
    431: 42,
    432: 46,
}

pages_to_copy = [8, 20, 22, 24, 30, 38, 39, 40]

if not DB.is_file():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

for page in pages_to_copy:
    src = SOURCE / f"page-{page}.jpg"
    if not src.is_file():
        raise SystemExit(f"Gambar sumber tidak ditemukan: {src}")

DEST.mkdir(parents=True, exist_ok=True)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = DB.parent / f"garment-before-ams221en-image-install-{stamp}.db"

con = sqlite3.connect(DB)

try:
    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()
    print("BACKUP:", backup)

    for page in pages_to_copy:
        src = SOURCE / f"page-{page}.jpg"
        dst = DEST / f"ams221en_page{page}.jpg"

        if dst.exists():
            raise FileExistsError(f"File tujuan sudah ada: {dst}")

    for page in pages_to_copy:
        src = SOURCE / f"page-{page}.jpg"
        dst = DEST / f"ams221en_page{page}.jpg"
        shutil.copy2(src, dst)
        print("COPY:", dst)

    for page in set(mapping.values()):
        image = DEST / f"ams221en_page{page}.jpg"
        if not image.is_file():
            raise FileNotFoundError(image)

    con.execute("BEGIN IMMEDIATE")

    for component_id, page in mapping.items():
        image_path = f"component_images/ams221en_page{page}.jpg"
        cur = con.execute("""
            UPDATE components
            SET diagram_page = ?, image_path = ?
            WHERE id = ? AND machine_id = 45
        """, (page, image_path, component_id))

        if cur.rowcount != 1:
            raise RuntimeError(f"Komponen ID {component_id} tidak ditemukan")

    con.commit()
    print("\nBerhasil memperbarui", len(mapping), "komponen.")

except Exception:
    con.rollback()
    raise
finally:
    con.close()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

print("\n=== HASIL PEMASANGAN ===")
for row in con.execute("""
    SELECT id, component_name, diagram_page, image_path
    FROM components
    WHERE machine_id = 45 AND id IN (
        403,409,410,411,415,416,418,423,424,
        425,426,427,428,429,430,431,432
    )
    ORDER BY id
"""):
    print(dict(row))

con.close()
