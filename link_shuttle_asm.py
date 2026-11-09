import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

db_path = Path("database/garment.db")
backup_path = Path(
    f"database/garment-before-shuttle-asm-{datetime.now():%Y%m%d-%H%M%S}.db"
)

component_id = 565

targets = [
    (13, 7452, "400-89365", "(1)"),
    (14, 7453, "B1820-210-D00", "(2)"),
    (15, 7454, "B1821-210-D00", "(1)"),
    (16, 7455, "B1822-215-P00", "(2)"),
    (17, 7456, "RE-0300000-K0", "(2)"),
    (18, 7457, "265-01858", "(2)"),
    (19, 7458, "141-04004", "(1)"),
    (20, 7459, "SM-6020460-TP", "(2)"),
    (21, 7460, "141-03907", "(1)"),
    (22, 7461, "400-06577", "(1)"),
    (23, 7462, "SM-4030455-SP", "(2)"),
    (24, 7463, "CQ-2000000-00", "(2.8)"),
    (25, 7464, "236-30007", "(1.1)"),
    (26, 7465, "135-29607", "(2)"),
    (27, 7466, "400-10470", "1"),
    (28, 7467, "400-10471", "1"),
    (29, 7468, "SM-6040650-TP", "1"),
    (30, 7469, "400-10472", "2"),
    (31, 7470, "400-06576", "2"),
    (32, 7471, "SM-8061050-TP", "1"),
    (33, 12788, "SB-3080010-0A", "(2)"),
    (34, 12789, "SB-3080010-0B", "(2)"),
    (35, 12790, "SB-3080010-0C", "(2)"),
    (36, 12791, "SB-3080010-0D", "(2)"),
    (37, 12792, "400-36117", "1"),
    (38, 7472, "SM-6020460-TP", "2"),
]

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

try:
    comp = con.execute("""
        SELECT id, machine_id, component_name, part_number
        FROM components WHERE id = ?
    """, (component_id,)).fetchone()

    assert comp is not None, "Component tidak ditemukan."
    assert comp["machine_id"] == 44
    assert comp["component_name"] == "SHUTTLE_ASM."
    assert comp["part_number"] == "400-89364"

    # Validasi semua target sebelum perubahan
    for ref, part_id, pn, qty in targets:
        row = con.execute("""
            SELECT id, machine_id, part_number, quantity_raw, notes
            FROM parts WHERE id = ?
        """, (part_id,)).fetchone()

        assert row is not None, f"REF{ref}: part ID tidak ditemukan."
        assert row["machine_id"] == 44, f"REF{ref}: machine salah."
        assert row["part_number"] == pn, f"REF{ref}: nomor part salah."
        assert row["quantity_raw"] == qty, f"REF{ref}: quantity berbeda."
        assert "section 8" in row["notes"], f"REF{ref}: staging bukan section 8."

        exists = con.execute("""
            SELECT 1 FROM component_parts
            WHERE component_id = ? AND part_id = ?
        """, (component_id, part_id)).fetchone()

        assert exists is None, f"REF{ref}: relasi sudah ada."

    # Pastikan REF12 masih satu-satunya relasi awal
    current = con.execute("""
        SELECT COUNT(*) FROM component_parts
        WHERE component_id = ?
    """, (component_id,)).fetchone()[0]

    assert current == 1, f"Jumlah relasi awal tidak sesuai: {current}"

    # Backup
    con.execute("PRAGMA wal_checkpoint(FULL)")
    shutil.copy2(db_path, backup_path)
    print("Backup:", backup_path)

    # Transaksi
    con.execute("BEGIN IMMEDIATE")

    for ref, part_id, pn, qty in targets:
        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
            VALUES (?, ?, ?, ?)
        """, (
            component_id,
            part_id,
            "catalog_component_part",
            f"JUKI AMS-210EN catalog; section 8; REF{ref}"
        ))

    con.commit()

    # Verifikasi
    rows = con.execute("""
        SELECT p.id, p.part_number, p.part_name,
               p.quantity_raw, p.notes AS part_notes,
               cp.relation_type, cp.notes AS relation_notes
        FROM component_parts cp
        JOIN parts p ON p.id = cp.part_id
        WHERE cp.component_id = ?
        ORDER BY p.catalog_ref, p.id
    """, (component_id,)).fetchall()

    assert len(rows) == 27, f"Total relasi salah: {len(rows)}"

    print("\n=== HASIL COMPONENT 565 ===")
    for row in rows:
        print(dict(row))

    print("\nBERHASIL: 26 relasi baru ditambahkan.")
    print("Total relasi Component565:", len(rows))

except Exception:
    con.rollback()
    raise

finally:
    con.close()
