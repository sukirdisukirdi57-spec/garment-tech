import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db = Path("database/garment.db")
backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"garment-before-repair-section10-{stamp}.db"

shutil.copy2(db, backup)
print("BACKUP:", backup)

con = sqlite3.connect(db)
try:
    con.execute("BEGIN IMMEDIATE")

    marker = "AMS-210EN catalog staging; section 10"

    rows = con.execute("""
        SELECT catalog_ref, part_number
        FROM parts
        WHERE machine_id=44 AND notes=?
    """, (marker,)).fetchall()

    refs = [r[0] for r in rows]
    missing = set(range(1, 49)) - set(refs)

    if len(rows) != 44 or len(set(refs)) != 44:
        raise RuntimeError(
            f"Kondisi awal tidak sesuai: {len(rows)} baris, "
            f"{len(set(refs))} REF unik."
        )

    if missing != {32, 33, 42, 46}:
        raise RuntimeError(f"REF kosong tidak sesuai: {sorted(missing)}")

    new_rows = [
        (32, "#02", "400-29411", "THREAD_TENSION_2_ASM._H", 1, "1"),
        (33, "#01", "400-10508", "THREAD_TENSION_2_ASM.", 1, "1"),
        (42, "＊ #02", "400-29412", "THREAD_TAKE-UP_SPRING_H", 1, "1"),
        (46, "＊ #01", "229-21605", "THREAD TAKE-UP SPRING", 1, "1"),
    ]

    for ref, note, pn, name, qty, raw in new_rows:
        con.execute("""
            INSERT INTO parts (
                machine_id, part_number, part_name, quantity,
                catalog_ref, note, notes, quantity_raw
            ) VALUES (44, ?, ?, ?, ?, ?, ?, ?)
        """, (pn, name, qty, ref, note, marker, raw))

    result = con.execute("""
        SELECT COUNT(*), COUNT(DISTINCT catalog_ref),
               MIN(catalog_ref), MAX(catalog_ref)
        FROM parts
        WHERE machine_id=44 AND notes=?
    """, (marker,)).fetchone()

    if result != (48, 48, 1, 48):
        raise RuntimeError(f"Verifikasi gagal: {result}")

    final_rows = con.execute("""
        SELECT catalog_ref, part_number, note, quantity_raw
        FROM parts
        WHERE machine_id=44 AND notes=?
        ORDER BY catalog_ref
    """, (marker,)).fetchall()

    for expected in new_rows:
        ref, note, pn, name, qty, raw = expected
        actual = next((r for r in final_rows if r[0] == ref), None)
        if actual != (ref, pn, note, raw):
            raise RuntimeError(f"Data REF {ref} tidak cocok: {actual}")

    con.commit()
    print("\nPERBAIKAN BERHASIL:", result)
    print("\n=== REF YANG DITAMBAHKAN ===")
    for r in final_rows:
        if r[0] in {32, 33, 42, 46}:
            print(r)

except Exception:
    con.rollback()
    raise
finally:
    con.close()

# Pertahankan 10 backup .db terbaru setelah verifikasi berhasil.
files = sorted(
    backup_dir.glob("*.db"),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)

keep = files[:10]
remove = files[10:]

print("\n=== 10 BACKUP DIPERTAHANKAN ===")
for p in keep:
    print(p.name)

print("\n=== BACKUP LAMA DIHAPUS ===")
for p in remove:
    print(p.name)
    p.unlink()

print("\nBACKUP .db TERSISA:", len(keep))
