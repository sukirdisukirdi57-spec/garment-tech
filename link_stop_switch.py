import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
backup = DB.with_name(
    f"garment-before-stop-switch-{datetime.now():%Y%m%d-%H%M%S}.db"
)

expected = [
    (7146, 55, "EA-9500B01-00", "CABLE BAND"),
    (7147, 56, "320-02305", "STOP SW BRACKET"),
    (7148, 57, "320-02404", "STOP SW GUIDE"),
]

shutil.copy2(DB, backup)
print("Backup:", backup)

con = sqlite3.connect(DB)
try:
    con.execute("BEGIN IMMEDIATE")

    component = con.execute("""
        SELECT id, machine_id, component_name, part_number
        FROM components WHERE id = 572
    """).fetchone()

    if component != (572, 44, "STOP SW ASM.", "400-29632"):
        raise RuntimeError(f"Komponen tidak sesuai: {component}")

    for part_id, ref, number, name in expected:
        row = con.execute("""
            SELECT machine_id, catalog_ref, part_number, part_name, notes
            FROM parts WHERE id = ?
        """, (part_id,)).fetchone()

        if not row:
            raise RuntimeError(f"Part ID {part_id} tidak ditemukan")

        if row[:4] != (44, ref, number, name):
            raise RuntimeError(
                f"Data part {part_id} tidak cocok: {row}"
            )

        if row[4] != "AMS-210EN catalog staging; section 1":
            raise RuntimeError(
                f"Catatan staging part {part_id} tidak cocok: {row[4]}"
            )

        exists = con.execute("""
            SELECT 1 FROM component_parts
            WHERE component_id = 572 AND part_id = ?
        """, (part_id,)).fetchone()

        if exists:
            raise RuntimeError(
                f"Relasi part {part_id} sudah ada; dibatalkan"
            )

    for part_id, ref, number, name in expected:
        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
            VALUES
                (572, ?, 'listed_in_component',
                 'JUKI AMS-210EN Section 1; STOP SW ASM.; REF ' || ?)
        """, (part_id, str(ref)))

    con.commit()
    print("BERHASIL: 3 relasi baru ditambahkan.")

except Exception:
    con.rollback()
    raise
finally:
    con.close()

con = sqlite3.connect(DB)
rows = con.execute("""
    SELECT p.id, p.catalog_ref, p.part_number, p.part_name,
           cp.relation_type
    FROM component_parts cp
    JOIN parts p ON p.id = cp.part_id
    WHERE cp.component_id = 572
    ORDER BY p.catalog_ref
""").fetchall()

print("\n=== VERIFIKASI STOP SW ASM. ===")
for row in rows:
    print(row)

print("\nTotal relasi:", len(rows))
con.close()
