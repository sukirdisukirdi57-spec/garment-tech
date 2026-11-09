import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

db_path = Path("database/garment.db")

if not db_path.exists():
    raise SystemExit("ERROR: database/garment.db tidak ditemukan.")

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

try:
    # Pastikan component yang dituju benar
    component = con.execute("""
        SELECT id, machine_id, component_name, part_number
        FROM components
        WHERE id = 574
    """).fetchone()

    if not component:
        raise RuntimeError("Component ID 574 tidak ditemukan.")

    if component["machine_id"] != 44 or component["component_name"] != "OIL TANK ASM.":
        raise RuntimeError("Identitas component tidak sesuai. Dibatalkan.")

    expected = [
        (7233, "SM-6040650-TP", "SCREW", "1", 61),
        (7234, "400-06840", "RUBBER BUSH", "2", 62),
    ]

    for part_id, pn, name, qty, ref in expected:
        p = con.execute("""
            SELECT id, machine_id, part_number, part_name,
                   quantity_raw, catalog_ref
            FROM parts
            WHERE id = ?
        """, (part_id,)).fetchone()

        if not p:
            raise RuntimeError(f"Part ID {part_id} tidak ditemukan.")

        actual = (
            p["machine_id"], p["part_number"], p["part_name"],
            p["quantity_raw"], p["catalog_ref"]
        )
        wanted = (44, pn, name, qty, ref)

        if actual != wanted:
            raise RuntimeError(
                f"Data part ID {part_id} tidak sesuai.\n"
                f"Aktual: {actual}\nSeharusnya: {wanted}"
            )

        existing = con.execute("""
            SELECT id FROM component_parts
            WHERE component_id = 574 AND part_id = ?
        """, (part_id,)).fetchone()

        if existing:
            raise RuntimeError(
                f"Relasi component 574 dengan part {part_id} sudah ada."
            )

    # Backup sebelum perubahan
    backup = Path(
        f"database/garment-before-oil-tank-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    con.commit()
    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()
    print("Backup:", backup)

    # Tambahkan relasi dalam satu transaksi
    con.execute("BEGIN")

    for part_id, *_ in expected:
        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type)
            VALUES (?, ?, 'listed_in_component')
        """, (574, part_id))

    con.commit()

    print("\nBERHASIL: 2 relasi baru ditambahkan.")

    print("\n=== VERIFIKASI OIL TANK ASM. ===")
    rows = con.execute("""
        SELECT p.id, p.catalog_ref, p.part_number, p.part_name,
               p.quantity_raw, cp.relation_type
        FROM component_parts cp
        JOIN parts p ON p.id = cp.part_id
        WHERE cp.component_id = 574
        ORDER BY p.catalog_ref
    """).fetchall()

    for r in rows:
        print(dict(r))

    print("\nTotal relasi:", len(rows))

except Exception as e:
    con.rollback()
    raise SystemExit(f"GAGAL — perubahan dibatalkan: {e}")

finally:
    con.close()
