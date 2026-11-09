import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP = Path(
    f"database/garment-before-section23-{datetime.now():%Y%m%d-%H%M%S}.db"
)

MACHINE_ID = 44
SECTION = "PEDAL COMPONENTS"
STAGING_NOTE = "AMS-210EN catalog staging; section 23"

EXPECTED = [
    (13190, 1, "400-33831", "PK78 PEDAL SWITCH ASM.", "1", "#01"),
    (13191, 2, "GPK-470010AB", "3-PEDAL ASM.", "1", "#02"),
    (13192, 3, "400-33875", "PK47 RELAY CABLE ASM.", "1", "#02"),
]

shutil.copy2(DB, BACKUP)
print("Backup:", BACKUP)

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=ON")

try:
    con.execute("BEGIN IMMEDIATE")

    machine = con.execute(
        "SELECT model FROM machines WHERE id=?",
        (MACHINE_ID,)
    ).fetchone()

    if not machine or machine[0] != "AMS-210EN-2210":
        raise RuntimeError("Machine ID tidak sesuai.")

    rows = con.execute("""
        SELECT id, catalog_ref, part_number, part_name,
               quantity_raw, note
        FROM parts
        WHERE machine_id=? AND notes=?
        ORDER BY catalog_ref
    """, (MACHINE_ID, STAGING_NOTE)).fetchall()

    if rows != EXPECTED:
        raise RuntimeError(
            f"Data staging tidak sesuai dengan PDF: {rows}"
        )

    existing = con.execute("""
        SELECT id FROM components
        WHERE machine_id=? AND component_name=?
    """, (MACHINE_ID, SECTION)).fetchall()

    if existing:
        raise RuntimeError(f"Komponen sudah ada: {existing}")

    ids = [r[0] for r in EXPECTED]
    placeholders = ",".join("?" for _ in ids)

    relation_count = con.execute(f"""
        SELECT COUNT(*) FROM component_parts
        WHERE part_id IN ({placeholders})
    """, ids).fetchone()[0]

    if relation_count:
        raise RuntimeError("Part staging sudah memiliki relasi.")

    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, part_number,
            diagram_page, notes
        )
        VALUES (?, ?, NULL, ?, ?)
    """, (
        MACHINE_ID,
        SECTION,
        41,
        "JUKI AMS-210EN Series parts list; section 23; 3 rows"
    ))

    component_id = cur.lastrowid

    con.executemany("""
        INSERT INTO component_parts (
            component_id, part_id, relation_type, notes
        )
        VALUES (?, ?, 'listed_in_section', ?)
    """, [
        (
            component_id,
            part_id,
            "JUKI AMS-210EN Series Parts List; Section 23"
        )
        for part_id in ids
    ])

    count = con.execute("""
        SELECT COUNT(*) FROM component_parts
        WHERE component_id=?
          AND relation_type='listed_in_section'
    """, (component_id,)).fetchone()[0]

    if count != 3:
        raise RuntimeError(f"Validasi relasi gagal: {count}")

    con.commit()

    print("\n=== BERHASIL ===")
    print("Component ID:", component_id)
    print("Nama:", SECTION)
    print("Diagram page: 41")
    print("Jumlah relasi:", count)
    print("Relation type: listed_in_section")

except Exception as e:
    con.rollback()
    print("\nGAGAL — transaksi dibatalkan:", e)
    raise

finally:
    con.close()
