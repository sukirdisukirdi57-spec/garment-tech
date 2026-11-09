import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")

# Component ID, nomor katalog resmi, Part ID, halaman PDF
TARGETS = [
    (410, "400-14963", 8835, 21),
    (415, "400-72228", 8963, 25),
    (416, "401-03968", 9002, 25),
    (418, "401-04419", 9136, 31),
    (428, "400-82758", 9511, 43),
    (430, "400-05401", 9517, 43),
]

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

# Backup database sebelum perubahan
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = DB.with_name(f"garment-before-ams221en-fix-{timestamp}.db")
shutil.copy2(DB, BACKUP)
print(f"BACKUP: {BACKUP}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    con.execute("BEGIN IMMEDIATE")

    # Validasi semua pasangan sebelum mengubah apa pun
    for cid, pn, pid, page in TARGETS:
        component = con.execute("""
            SELECT id, machine_id, part_number
            FROM components
            WHERE id = ?
        """, (cid,)).fetchone()

        part = con.execute("""
            SELECT id, machine_id, part_number, catalog_ref
            FROM parts
            WHERE id = ?
        """, (pid,)).fetchone()

        if not component or component["machine_id"] != 45:
            raise ValueError(f"Komponen {cid} tidak valid")

        if not part or part["machine_id"] != 45:
            raise ValueError(f"Part {pid} tidak valid")

        if part["part_number"] != pn:
            raise ValueError(f"Nomor part tidak cocok: {pid}")

        if con.execute("""
            SELECT 1 FROM component_parts
            WHERE component_id = ? AND part_id = ?
        """, (cid, pid)).fetchone():
            raise ValueError(f"Relasi sudah ada: component {cid}, part {pid}")

    # Terapkan koreksi metadata dan relasi
    for cid, pn, pid, page in TARGETS:
        con.execute("""
            UPDATE components
            SET part_number = ?, diagram_page = ?
            WHERE id = ? AND machine_id = 45
        """, (pn, page, cid))

        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
            VALUES (?, ?, 'main-part', ?)
        """, (
            cid,
            pid,
            "Verified against JUKI AMS-221EN Parts List."
        ))

    con.commit()

    print("\nKOREKSI BERHASIL:")
    for cid, pn, pid, page in TARGETS:
        print(
            f"Component {cid} -> Part {pid} | "
            f"{pn} | PDF page {page}"
        )

except Exception:
    con.rollback()
    print("\nKOREKSI DIBATALKAN. Transaksi di-rollback.")
    raise

finally:
    con.close()

print(f"\nBackup tersedia: {BACKUP}")
