import sqlite3
from datetime import datetime
from pathlib import Path

db_path = Path("database/garment.db")
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

expected = [
    (7236, 64, "400-06496", "SAFETY_SW_BASE", "(1)"),
    (7237, 65, "236-38109", "SAFETY SWITCH ARM", "(1)"),
    (7238, 66, "400-06497", "SAFETY_SW_ARM_SHAFT", "(1)"),
    (7239, 67, "236-38208", "SAFETY SWITCH SPRING", "(1)"),
    (7240, 68, "236-38406", "SAFETY SWITCH NUT", "(1)"),
    (7241, 69, "SM-4021201-SC", "SCREW M2 L=12", "(2)"),
    (7242, 70, "EA-9500B01-00", "CABLE BAND", "(1)"),
    (7243, 71, "400-29633", "SAFETY SW CORD ASM.", "(1)"),
]

try:
    component = con.execute("""
        SELECT id, machine_id, component_name, part_number
        FROM components WHERE id = 575
    """).fetchone()

    if not component or (
        component["machine_id"] != 44
        or component["component_name"] != "SAFTY_SW_ASM."
        or component["part_number"] != "400-29776"
    ):
        raise RuntimeError("Identitas Component 575 tidak sesuai.")

    for part_id, ref, pn, name, qty in expected:
        p = con.execute("""
            SELECT id, machine_id, catalog_ref, part_number,
                   part_name, quantity_raw, notes
            FROM parts WHERE id = ?
        """, (part_id,)).fetchone()

        if not p:
            raise RuntimeError(f"Part ID {part_id} tidak ditemukan.")

        actual = (
            p["machine_id"], p["catalog_ref"], p["part_number"],
            p["part_name"], p["quantity_raw"]
        )
        wanted = (44, ref, pn, name, qty)

        if actual != wanted or "section 3" not in (p["notes"] or "").lower():
            raise RuntimeError(
                f"Data part ID {part_id} tidak cocok.\n"
                f"Aktual: {actual}\nSeharusnya: {wanted}"
            )

        linked = con.execute("""
            SELECT component_id FROM component_parts WHERE part_id = ?
        """, (part_id,)).fetchall()

        if linked:
            raise RuntimeError(
                f"Part ID {part_id} sudah memiliki relasi: "
                f"{[r['component_id'] for r in linked]}"
            )

    backup = Path(
        f"database/garment-before-safety-switch-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()
    print("Backup:", backup)

    con.execute("BEGIN")
    for part_id, *_ in expected:
        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type)
            VALUES (575, ?, 'listed_in_component')
        """, (part_id,))
    con.commit()

    print("\nBERHASIL: 8 relasi baru ditambahkan.")
    print("\n=== VERIFIKASI COMPONENT 575 ===")

    rows = con.execute("""
        SELECT p.id, p.catalog_ref, p.part_number, p.part_name,
               p.quantity_raw, cp.relation_type
        FROM component_parts cp
        JOIN parts p ON p.id = cp.part_id
        WHERE cp.component_id = 575
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
