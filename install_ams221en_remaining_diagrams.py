import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
SOURCE_DIR = Path("tmp/ams221en-remaining-audit")
DEST_DIR = Path("static/component_images")

# Component ID: (diagram page, official image filename)
TARGETS = {
    404: 23,
    407: 16,
    419: 26,
    420: 26,
    421: 38,
    422: 38,
}

# Page 38 was installed previously; reuse it.
PAGES = sorted(set(TARGETS.values()))

if not DB.is_file():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

DEST_DIR.mkdir(parents=True, exist_ok=True)

# Validate source images and existing destinations before any DB changes.
for page in PAGES:
    dest = DEST_DIR / f"ams221en_page{page}.jpg"

    if dest.exists():
        if page == 38:
            print(f"[REUSE] {dest}")
            continue
        raise SystemExit(
            f"ABORT: file tujuan sudah ada: {dest}. "
            "Tidak ada file atau database yang diubah."
        )

    source = SOURCE_DIR / f"page-{page}.jpg"
    if not source.is_file() or source.stat().st_size == 0:
        raise SystemExit(f"ABORT: gambar sumber tidak valid: {source}")

# Confirm all target component IDs exist for machine 45.
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

rows = con.execute(
    """
    SELECT id, machine_id, component_name, diagram_page, image_path
    FROM components
    WHERE machine_id = 45
      AND id IN (404, 407, 419, 420, 421, 422)
    ORDER BY id
    """
).fetchall()

found = {row["id"] for row in rows}
if found != set(TARGETS):
    con.close()
    raise SystemExit(
        f"ABORT: ID komponen tidak cocok. Ditemukan: {sorted(found)}"
    )

print("\n=== TARGET UPDATE ===")
for row in rows:
    print(
        f'{row["id"]}: {row["component_name"]} '
        f'| halaman lama={row["diagram_page"]} '
        f'| halaman baru={TARGETS[row["id"]]}'
    )

# Create a timestamped SQLite backup before copying/updating.
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = DB.with_name(f"garment-before-remaining-diagrams-{stamp}.db")

backup_con = sqlite3.connect(backup)
con.backup(backup_con)
backup_con.close()

print(f"\n[BACKUP] {backup}")

copied = []
try:
    for page in PAGES:
        if page == 38:
            continue

        source = SOURCE_DIR / f"page-{page}.jpg"
        dest = DEST_DIR / f"ams221en_page{page}.jpg"
        shutil.copy2(source, dest)
        copied.append(dest)
        print(f"[COPY] {source} -> {dest}")

    for component_id, page in TARGETS.items():
        image_path = f"component_images/ams221en_page{page}.jpg"
        con.execute(
            """
            UPDATE components
            SET diagram_page = ?, image_path = ?
            WHERE id = ? AND machine_id = 45
            """,
            (page, image_path, component_id)
        )

    con.commit()

except Exception:
    con.rollback()
    for path in copied:
        path.unlink(missing_ok=True)
    con.close()
    raise

con.close()

print("\n[OK] Enam komponen berhasil diperbarui.")
print("ID 405 dan 417 tidak diubah.")
print("Relasi component_parts dan data parts tidak diubah.")
