import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
COMPONENT_ID = 562
MACHINE_ID = 44

items = [
    (5, "262-60109", "BTW_BASE", 7159, "(1)"),
    (6, "262-60208", "BTW_CAM_PLATE", 7160, "(1)"),
    (7, "262-60307", "BTW_BASE_SHAFT", 7161, "(1)"),
    (8, "262-60406", "BTW_SHAFT_BASE", 7162, "(1)"),
    (9, "262-60505", "BTW_CAM_LEVER", 7163, "(1)"),
    (10, "262-60604", "BTW_WHEEL", 7164, "(1)"),
    (11, "262-60703", "BTW_TORSION_SPRING", 7165, "(1)"),
    (12, "262-60802", "BTW_BEARING_SPACER", 7166, "(1)"),
    (13, "400-23865", "BTW_SHAFT", 7167, "(1)"),
    (14, "400-23866", "BTW_LEVER_SHAFT", 7168, "(1)"),
    (15, "400-30829", "BTW_LEVER", 7169, "(1)"),
    (16, "262-61206", "BTW_SPACER", 7170, "(1)"),
    (17, "262-61305", "BTW_BEARING", 7171, "(2)"),
    (18, "262-61503", "BTW_WHEEL_RUBBER", None, "(1)"),
    (19, "262-61602", "BOBBIN_SPRING", 7172, "(1)"),
    (20, "262-61701", "BTW_SPRING", 7173, "(1)"),
    (21, "RC-0560711-KP", "RETAINING RING", 7174, "(1)"),
    (22, "RE-0400000-K0", "E-RING 4", 7175, "(1)"),
    (23, "WP-0450826-SC", "WASHER 4.5X10X0.8", 7176, "(1)"),
    (24, "SM-5040655-SN", "SCREW", 7177, "(1)"),
    (25, "SM-8050502-TP", "SCREW M5 L=5", 7178, "(1)"),
    (26, "SM-8040802-TP", "SCREW M4X8", 7179, "(2)"),
    (27, "SM-6041150-TP", "SCREW", 7180, "3"),
]

backup = DB.with_name(
    "garment-before-bobbin-winder-" +
    datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)

shutil.copy2(DB, backup)
print("Backup:", backup)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    con.execute("BEGIN IMMEDIATE")

    component = con.execute("""
        SELECT id, machine_id, component_name
        FROM components WHERE id = ?
    """, (COMPONENT_ID,)).fetchone()

    assert component is not None
    assert component["machine_id"] == MACHINE_ID
    assert component["component_name"] == "BOBBIN_WINDER_UNIT"

    main = con.execute("""
        SELECT * FROM parts
        WHERE id = 7158 AND machine_id = 44
          AND part_number = '400-28338'
          AND catalog_ref = 4
    """).fetchone()

    assert main is not None, "Part utama REF 4 tidak cocok"

    added = 0
    linked = 0

    for ref, pn, name, expected_id, qty in items:
        if ref == 18:
            existing = con.execute("""
                SELECT id FROM parts
                WHERE machine_id = ? AND part_number = ?
                  AND catalog_ref = ?
            """, (MACHINE_ID, pn, ref)).fetchall()

            assert not existing, "Part REF 18 sudah ada"

            cur = con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number,
                    part_name, catalog_ref, diagram_page, note,
                    quantity_raw
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
            """, (
                MACHINE_ID, main["source_document_id"],
                pn, name, ref, "☆", qty
            ))
            part_id = cur.lastrowid
            added += 1

        else:
            row = con.execute("""
                SELECT id, machine_id, part_number, part_name,
                       catalog_ref, quantity_raw
                FROM parts WHERE id = ?
            """, (expected_id,)).fetchone()

            assert row is not None, f"Part ID {expected_id} tidak ditemukan"
            assert row["machine_id"] == MACHINE_ID
            assert row["part_number"] == pn
            assert row["part_name"] == name
            assert row["catalog_ref"] == ref

            # Jangan menimpa data kuantitas yang sudah ada.
            part_id = expected_id

        relation = con.execute("""
            SELECT id FROM component_parts
            WHERE component_id = ? AND part_id = ?
        """, (COMPONENT_ID, part_id)).fetchone()

        if relation is None:
            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, 'listed_in_component', ?)
            """, (
                COMPONENT_ID, part_id,
                f"JUKI AMS-210EN Series Parts List; "
                f"printed page 4; REF {ref}"
            ))
            linked += 1

    count = con.execute("""
        SELECT COUNT(*) FROM component_parts
        WHERE component_id = ?
    """, (COMPONENT_ID,)).fetchone()[0]

    assert count == 24, f"Jumlah relasi akhir salah: {count}"

    con.commit()

    print("\nBERHASIL")
    print("Part baru:", added)
    print("Relasi baru:", linked)
    print("Total relasi:", count)

    print("\n=== HASIL REF 4-27 ===")
    for row in con.execute("""
        SELECT p.catalog_ref, p.id, p.part_number, p.part_name,
               p.quantity_raw, p.note, cp.relation_type
        FROM component_parts cp
        JOIN parts p ON p.id = cp.part_id
        WHERE cp.component_id = ?
          AND p.catalog_ref BETWEEN 4 AND 27
        ORDER BY p.catalog_ref
    """, (COMPONENT_ID,)):
        print(tuple(row))

except Exception:
    con.rollback()
    print("\nGAGAL: transaksi dibatalkan.")
    raise
finally:
    con.close()
