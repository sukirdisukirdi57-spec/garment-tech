import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db = Path("database/garment.db")
backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"garment-before-repair-section8-{stamp}.db"

# Backup sebelum perubahan
shutil.copy2(db, backup)
print("BACKUP:", backup)

con = sqlite3.connect(db)
try:
    con.execute("BEGIN IMMEDIATE")

    marker = "AMS-210EN catalog staging; section 8"

    rows = con.execute("""
        SELECT catalog_ref, part_number, note
        FROM parts
        WHERE machine_id=44 AND notes=?
    """, (marker,)).fetchall()

    refs = [r[0] for r in rows]
    if len(rows) != 44 or len(set(refs)) != 44:
        raise RuntimeError(
            f"Kondisi awal berubah: {len(rows)} baris, "
            f"{len(set(refs))} REF unik. Dibatalkan."
        )

    expected_missing = {34, 35, 36, 41, 49}
    actual_missing = set(range(1, 50)) - set(refs)
    if actual_missing != expected_missing:
        raise RuntimeError(
            f"REF kosong tidak sesuai: {sorted(actual_missing)}. Dibatalkan."
        )

    # Pastikan REF 33 cocok sebelum koreksi NOTE
    ref33 = con.execute("""
        SELECT part_number, note
        FROM parts
        WHERE machine_id=44 AND notes=? AND catalog_ref=33
    """, (marker,)).fetchone()

    if ref33 != ("SB-3080010-0A", "COMMON"):
        raise RuntimeError(f"Data REF 33 tidak sesuai: {ref33}. Dibatalkan.")

    new_rows = [
        (34, "#01", "SB-3080010-0B", "BEARING", 2, "2"),
        (35, "#01", "SB-3080010-0C", "BEARING", 2, "2"),
        (36, "#01", "SB-3080010-0D", "BEARING", 2, "2"),
        (41, "#03", "400-61991", "SHUTTLE(H)", 1, "1"),
        (49, "#02", "400-14964", "SHUTTLE", 1, "1"),
    ]

    for ref, note, pn, name, qty, raw in new_rows:
        con.execute("""
            INSERT INTO parts (
                machine_id, part_number, part_name, quantity,
                catalog_ref, note, notes, quantity_raw
            ) VALUES (44, ?, ?, ?, ?, ?, ?, ?)
        """, (pn, name, qty, ref, note, marker, raw))

    con.execute("""
        UPDATE parts
        SET note='#01'
        WHERE machine_id=44 AND notes=? AND catalog_ref=33
          AND part_number='SB-3080010-0A'
    """, (marker,))

    # Verifikasi sebelum commit
    result = con.execute("""
        SELECT COUNT(*), COUNT(DISTINCT catalog_ref),
               MIN(catalog_ref), MAX(catalog_ref)
        FROM parts
        WHERE machine_id=44 AND notes=?
    """, (marker,)).fetchone()

    final_rows = con.execute("""
        SELECT catalog_ref, part_number, note
        FROM parts
        WHERE machine_id=44 AND notes=?
        ORDER BY catalog_ref
    """, (marker,)).fetchall()

    if result != (49, 49, 1, 49):
        raise RuntimeError(f"Verifikasi gagal: {result}")

    if final_rows[32] != (33, "SB-3080010-0A", "#01"):
        raise RuntimeError("NOTE REF 33 gagal diverifikasi.")

    con.commit()
    print("\nPERBAIKAN BERHASIL:", result)

except Exception:
    con.rollback()
    raise
finally:
    con.close()

# Hapus backup lama hanya setelah perubahan berhasil.
# Pertahankan 10 backup .db terbaru berdasarkan waktu modifikasi.
files = sorted(
    backup_dir.glob("*.db"),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)

keep = files[:10]
remove = files[10:]

print("\n=== BACKUP DIPERTAHANKAN ===")
for p in keep:
    print(p.name)

print("\n=== BACKUP LAMA DIHAPUS ===")
for p in remove:
    print(p.name)
    p.unlink()

print("\nSelesai. Backup .db tersisa:", len(keep))
