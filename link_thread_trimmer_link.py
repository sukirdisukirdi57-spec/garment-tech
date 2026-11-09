import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

db_path = Path("database/garment.db")
backup_path = Path(
    f"database/garment-before-thread-trimmer-link-{datetime.now():%Y%m%d-%H%M%S}.db"
)

component_id = 564

targets = [
    (11, 7567, "SD-0800327-TP", "SHOULDER SCREW", "1"),
    (12, 7568, "NM-6050001-SP", "NUT M5", "1"),
    (13, 7569, "400-23624", "THREAD_TRIMMER_SHAFT", "1"),
    (14, 7570, "SM-8060812-TP", "SCREW M6 L=8", "2"),
    (15, 7571, "400-30935", "CONNECTING_BAR", "1"),
]

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

try:
    # Pemeriksaan komponen
    comp = con.execute("""
        SELECT id, machine_id, component_name, part_number
        FROM components
        WHERE id = ?
    """, (component_id,)).fetchone()

    assert comp is not None, "Component ID564 tidak ditemukan."
    assert comp["machine_id"] == 44, "Machine ID tidak sesuai."
    assert comp["component_name"] == "THREAD_TRIMMER_LINK_ASM"
    assert comp["part_number"] == "400-72228"

    # Pemeriksaan part dan staging
    for ref, part_id, pn, name, qty in targets:
        row = con.execute("""
            SELECT id, machine_id, part_number, part_name,
                   quantity_raw, notes
            FROM parts
            WHERE id = ?
        """, (part_id,)).fetchone()

        assert row is not None, f"Part ID {part_id} tidak ditemukan."
        assert row["machine_id"] == 44
        assert row["part_number"] == pn
        assert row["part_name"] == name
        assert row["quantity_raw"] == qty
        assert row["notes"] == "AMS-210EN catalog staging; section 11"

        exists = con.execute("""
            SELECT 1 FROM component_parts
            WHERE component_id = ? AND part_id = ?
        """, (component_id, part_id)).fetchone()

        assert exists is None, f"Relasi REF{ref} sudah ada."

    # Backup sebelum perubahan
    con.execute("PRAGMA wal_checkpoint(FULL)")
    shutil.copy2(db_path, backup_path)
    print("Backup:", backup_path)

    # Tambahkan relasi secara atomik
    con.execute("BEGIN IMMEDIATE")

    for ref, part_id, pn, name, qty in targets:
        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
            VALUES (?, ?, ?, ?)
        """, (
            component_id,
            part_id,
            "catalog_component_part",
            f"JUKI AMS-210EN catalog; section 11; REF{ref}"
        ))

    con.commit()

    # Verifikasi
    rows = con.execute("""
        SELECT p.id, p.part_number, p.part_name, p.quantity_raw,
               cp.relation_type, cp.notes
        FROM component_parts cp
        JOIN parts p ON p.id = cp.part_id
        WHERE cp.component_id = ?
        ORDER BY p.catalog_ref, p.id
    """, (component_id,)).fetchall()

    print("\n=== HASIL COMPONENT 564 ===")
    for row in rows:
        print(dict(row))

    assert len(rows) == 6, f"Total relasi tidak sesuai: {len(rows)}"

    print("\nBERHASIL: 5 relasi baru ditambahkan.")
    print("Total relasi Component 564:", len(rows))

except Exception:
    con.rollback()
    raise

finally:
    con.close()
