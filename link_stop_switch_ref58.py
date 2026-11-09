import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db_path = Path("database/garment.db")
backup = db_path.with_name(
    f"garment-before-stop-sw-ref58-{datetime.now():%Y%m%d-%H%M%S}.db"
)
shutil.copy2(db_path, backup)
print("Backup:", backup)

con = sqlite3.connect(db_path)

try:
    con.execute("BEGIN IMMEDIATE")

    component = con.execute("""
        SELECT machine_id, component_name, part_number
        FROM components WHERE id = 572
    """).fetchone()

    if component != (44, "STOP SW ASM.", "400-29632"):
        raise RuntimeError(f"Komponen tidak cocok: {component}")

    part = con.execute("""
        SELECT machine_id, catalog_ref, part_number,
               part_name, quantity_raw, notes
        FROM parts WHERE id = 7149
    """).fetchone()

    expected = (
        44, 58, "SS-7110740-TP",
        "SCREW 11/64-40 L=7", "(1)",
        "AMS-210EN catalog staging; section 1"
    )

    if part != expected:
        raise RuntimeError(f"Data REF58 tidak cocok: {part}")

    if con.execute("""
        SELECT 1 FROM component_parts
        WHERE component_id = 572 AND part_id = 7149
    """).fetchone():
        raise RuntimeError("Relasi REF58 sudah ada.")

    con.execute("""
        INSERT INTO component_parts
            (component_id, part_id, relation_type, notes)
        VALUES
            (572, 7149, 'listed_in_component',
             'JUKI AMS-210EN Section 1; STOP SW ASM.; REF 58')
    """)

    con.commit()
    print("BERHASIL: REF58 ditambahkan.")

except Exception:
    con.rollback()
    raise
finally:
    con.close()

con = sqlite3.connect(db_path)
print("\n=== VERIFIKASI STOP SW ASM. ===")

for row in con.execute("""
    SELECT p.catalog_ref, p.part_number, p.part_name,
           p.quantity_raw, cp.relation_type
    FROM component_parts cp
    JOIN parts p ON p.id = cp.part_id
    WHERE cp.component_id = 572
    ORDER BY p.catalog_ref
"""):
    print(row)

print("Total relasi:", con.execute("""
    SELECT COUNT(*) FROM component_parts
    WHERE component_id = 572
""").fetchone()[0])

con.close()
