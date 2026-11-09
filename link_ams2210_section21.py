import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
BACKUP = Path(
    f"database/garment-before-section21-{datetime.now():%Y%m%d-%H%M%S}.db"
)

MACHINE_ID = 44
SECTION_NAME = "CONTROL BOX COMPONENTS"
SECTION_PAGE = 37
SECTION_NOTE = (
    "JUKI AMS-210EN Series parts list; section 21; 66 rows"
)
STAGING_NOTE = "AMS-210EN catalog staging; section 21"

# Backup sebelum perubahan
shutil.copy2(DB, BACKUP)
print(f"Backup dibuat: {BACKUP}")

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys = ON")

try:
    con.execute("BEGIN IMMEDIATE")

    # Pastikan mesin target benar
    machine = con.execute(
        "SELECT model FROM machines WHERE id=?",
        (MACHINE_ID,)
    ).fetchone()

    if not machine or machine[0] != "AMS-210EN-2210":
        raise RuntimeError("Machine ID 44 bukan AMS-210EN-2210.")

    # Pastikan staging tepat 66 baris dan REF 1-66 lengkap
    parts = con.execute("""
        SELECT id, catalog_ref
        FROM parts
        WHERE machine_id=?
          AND notes=?
        ORDER BY CAST(catalog_ref AS INTEGER), id
    """, (MACHINE_ID, STAGING_NOTE)).fetchall()

    if len(parts) != 66:
        raise RuntimeError(
            f"Jumlah staging bukan 66, ditemukan {len(parts)}."
        )

    refs = [int(row[1]) for row in parts]

    if refs != list(range(1, 67)):
        raise RuntimeError("REF staging tidak lengkap atau tidak berurutan.")

    # Jangan membuat komponen duplikat
    existing = con.execute("""
        SELECT id
        FROM components
        WHERE machine_id=?
          AND component_name=?
    """, (MACHINE_ID, SECTION_NAME)).fetchall()

    if existing:
        raise RuntimeError(
            f"Komponen section sudah ada: {existing}"
        )

    # Pastikan belum ada relasi untuk part staging
    part_ids = [row[0] for row in parts]
    placeholders = ",".join("?" for _ in part_ids)

    existing_relations = con.execute(f"""
        SELECT COUNT(*)
        FROM component_parts
        WHERE part_id IN ({placeholders})
    """, part_ids).fetchone()[0]

    if existing_relations:
        raise RuntimeError(
            f"Ditemukan {existing_relations} relasi sebelumnya."
        )

    # Buat komponen section
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
        MACHINE_ID,
        SECTION_NAME,
        SECTION_PAGE,
        SECTION_NOTE
    ))

    component_id = cur.lastrowid

    # Hubungkan seluruh 66 part ke section
    con.executemany("""
        INSERT INTO component_parts (
            component_id,
            part_id,
            relation_type,
            notes
        )
        VALUES (?, ?, 'listed_in_section', ?)
    """, [
        (
            component_id,
            part_id,
            "JUKI AMS-210EN Series Parts List; Section 21"
        )
        for part_id in part_ids
    ])

    # Validasi sebelum commit
    result = con.execute("""
        SELECT
            c.id,
            c.component_name,
            c.part_number,
            c.diagram_page,
            c.notes,
            COUNT(cp.id)
        FROM components c
        JOIN component_parts cp ON cp.component_id=c.id
        WHERE c.id=?
          AND cp.relation_type='listed_in_section'
        GROUP BY c.id
    """, (component_id,)).fetchone()

    if not result or result[5] != 66:
        raise RuntimeError("Validasi komponen atau jumlah relasi gagal.")

    con.commit()

    print("\n=== BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", result[1])
    print("Part number  :", result[2])
    print("Diagram page :", result[3])
    print("Relasi       :", result[5])
    print("Relation type: listed_in_section")
    print("Backup       :", BACKUP)

except Exception as e:
    con.rollback()
    print("\nGAGAL — transaksi dibatalkan:", e)
    print("Backup tetap tersedia:", BACKUP)
    raise

finally:
    con.close()
