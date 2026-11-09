import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
backup = DB.with_name(
    f"garment-before-lower-shaft-gear-{datetime.now():%Y%m%d-%H%M%S}.db"
)

parts = [
    (7444, 5, "400-06567", "LOWER_SHAFT_GEAR", "(1)"),
    (7445, 6, "400-06569", "LOWER_SHAFT_REAR_METAL", "(1)"),
    (7446, 7, "400-24063", "NUT", "(1)"),
    (7447, 8, "SB-1120017-00", "BEARING", "(2)"),
    (7448, 9, "400-06317", "LOWER SHAFT GEAR RING", "(2)"),
    (7449, 10, "SM-8060612-TP", "SCREW M6 L=6", "2"),
    (7450, 11, "SM-8060812-TP", "SCREW M6 L=8", "2"),
]

shutil.copy2(DB, backup)
print("Backup:", backup)

con = sqlite3.connect(DB)

try:
    con.execute("BEGIN IMMEDIATE")

    component = con.execute("""
        SELECT machine_id, component_name, part_number
        FROM components WHERE id = 563
    """).fetchone()

    if component != (44, "LOWEW_SHAFT_GEAR_ASM", "400-72009"):
        raise RuntimeError(f"Komponen tidak cocok: {component}")

    for pid, ref, number, name, qty in parts:
        row = con.execute("""
            SELECT machine_id, catalog_ref, part_number,
                   part_name, quantity_raw, notes
            FROM parts WHERE id = ?
        """, (pid,)).fetchone()

        expected = (
            44, ref, number, name, qty,
            "AMS-210EN catalog staging; section 8"
        )

        if row != expected:
            raise RuntimeError(
                f"Data part ID {pid} tidak cocok: {row}"
            )

        exists = con.execute("""
            SELECT 1 FROM component_parts
            WHERE component_id = 563 AND part_id = ?
        """, (pid,)).fetchone()

        if exists:
            raise RuntimeError(f"Relasi part ID {pid} sudah ada.")

    for pid, ref, number, name, qty in parts:
        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
            VALUES (?, ?, 'listed_in_component', ?)
        """, (
            563, pid,
            f"JUKI AMS-210EN Section 8; LOWEW_SHAFT_GEAR_ASM; REF {ref}"
        ))

    con.commit()
    print("BERHASIL: 7 relasi baru ditambahkan.")

except Exception:
    con.rollback()
    raise
finally:
    con.close()

con = sqlite3.connect(DB)

print("\n=== VERIFIKASI COMPONENT 563 ===")
rows = con.execute("""
    SELECT p.id, p.catalog_ref, p.part_number,
           p.part_name, p.quantity_raw, cp.relation_type
    FROM component_parts cp
    JOIN parts p ON p.id = cp.part_id
    WHERE cp.component_id = 563
    ORDER BY p.catalog_ref
""").fetchall()

for row in rows:
    print(row)

print("Total relasi:", len(rows))
con.close()
