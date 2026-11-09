import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
backup = DB.with_name(
    f"garment-before-section24-{datetime.now():%Y%m%d-%H%M%S}.db"
)

shutil.copy2(DB, backup)
print("Backup:", backup)

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=ON")

try:
    con.execute("BEGIN IMMEDIATE")

    machine = con.execute("""
        SELECT id, model
        FROM machines
        WHERE id=44
    """).fetchone()

    if not machine:
        raise RuntimeError("Machine ID 44 tidak ditemukan")

    print("Machine:", machine)

    if "AMS-210EN-2210" not in str(machine):
        raise RuntimeError("Machine ID 44 bukan AMS-210EN-2210")

    existing = con.execute("""
        SELECT id
        FROM components
        WHERE machine_id=44
          AND component_name='ACCESSORIE PARTS COMPONENTS'
    """).fetchall()

    if existing:
        raise RuntimeError("Component Section 24 sudah ada")

    rows = con.execute("""
        SELECT id, catalog_ref
        FROM parts
        WHERE machine_id=44
          AND notes='AMS-210EN catalog staging; section 24'
        ORDER BY catalog_ref
    """).fetchall()

    expected = list(range(1, 27))
    refs = [r[1] for r in rows]

    if len(rows) != 26 or refs != expected:
        raise RuntimeError(
            f"Staging tidak cocok: jumlah={len(rows)}, REF={refs}"
        )

    linked = con.execute("""
        SELECT COUNT(*)
        FROM component_parts cp
        JOIN parts p ON p.id=cp.part_id
        WHERE p.machine_id=44
          AND p.notes='AMS-210EN catalog staging; section 24'
    """).fetchone()[0]

    if linked != 0:
        raise RuntimeError("Ditemukan relasi staging sebelumnya")

    cur = con.execute("""
        INSERT INTO components (
            machine_id,
            component_name,
            part_number,
            diagram_page,
            notes
        )
        VALUES (?, ?, NULL, ?, ?)
    """, (
        44,
        "ACCESSORIE PARTS COMPONENTS",
        42,
        "JUKI AMS-210EN Series parts list; section 24; 26 rows"
    ))

    component_id = cur.lastrowid

    con.executemany("""
        INSERT INTO component_parts (
            component_id,
            part_id,
            relation_type,
            notes
        )
        VALUES (?, ?, ?, ?)
    """, [
        (
            component_id,
            part_id,
            "listed_in_section",
            "JUKI AMS-210EN Series Parts List; Section 24"
        )
        for part_id, ref in rows
    ])

    count = con.execute("""
        SELECT COUNT(*)
        FROM component_parts
        WHERE component_id=?
          AND relation_type='listed_in_section'
    """, (component_id,)).fetchone()[0]

    if count != 26:
        raise RuntimeError(f"Jumlah relasi salah: {count}")

    con.commit()

    print("\nBERHASIL")
    print("Component ID:", component_id)
    print("Nama: ACCESSORIE PARTS COMPONENTS")
    print("Halaman: 42")
    print("Jumlah relasi:", count)

except Exception:
    con.rollback()
    print("\nGAGAL — transaksi dibatalkan.")
    raise

finally:
    con.close()
