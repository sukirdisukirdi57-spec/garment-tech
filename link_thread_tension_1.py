import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
COMPONENT_ID = 568

# REF, part_id, part_number, part_name, quantity_raw
TARGETS = [
    (28, 7544, "229-28808", "NUT", "(1)"),
    (29, 7545, "229-21506", "THREAD TENSION DISK", "(2)"),
    (30, 7546, "400-10504", "THREAD_TENSION_SHAFT", "(1)"),
    (31, 7547, "262-18602", "FIRST THREAD TENSION SPRING", "(1)"),
]

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    # Validasi komponen sasaran
    component = con.execute("""
        SELECT id, machine_id, component_name, part_number
        FROM components WHERE id = ?
    """, (COMPONENT_ID,)).fetchone()

    expected_component = (44, "THREAD_TENSION_1_ASM.", "400-10503")
    if not component or (
        component["machine_id"],
        component["component_name"],
        component["part_number"]
    ) != expected_component:
        raise RuntimeError("Identitas Component568 tidak sesuai. Dibatalkan.")

    # Validasi seluruh part dan staging section 10
    for ref, part_id, pn, name, qty in TARGETS:
        part = con.execute("""
            SELECT id, machine_id, part_number, part_name,
                   quantity_raw, notes
            FROM parts WHERE id = ?
        """, (part_id,)).fetchone()

        if not part:
            raise RuntimeError(f"Part ID {part_id} tidak ditemukan.")

        expected = (44, pn, name, qty)
        actual = (
            part["machine_id"], part["part_number"],
            part["part_name"], part["quantity_raw"]
        )
        if actual != expected:
            raise RuntimeError(
                f"Data REF{ref} tidak sesuai: {actual} != {expected}"
            )

        if "section 10" not in (part["notes"] or "").lower():
            raise RuntimeError(f"REF{ref} bukan staging section 10.")

        exists = con.execute("""
            SELECT 1 FROM component_parts
            WHERE component_id = ? AND part_id = ?
        """, (COMPONENT_ID, part_id)).fetchone()

        if exists:
            raise RuntimeError(f"REF{ref} sudah terhubung. Dibatalkan.")

    # Backup sebelum perubahan
    backup = DB.with_name(
        f"garment-before-thread-tension-1-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    shutil.copy2(DB, backup)

    try:
        con.execute("BEGIN IMMEDIATE")

        for ref, part_id, pn, name, qty in TARGETS:
            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, ?, ?)
            """, (
                COMPONENT_ID,
                part_id,
                "catalog_component_part",
                f"Katalog JUKI AMS-210EN; section 10; REF{ref}"
            ))

        # Verifikasi sebelum commit
        rows = con.execute("""
            SELECT p.part_number, p.part_name, p.quantity_raw,
                   cp.relation_type, cp.notes
            FROM component_parts cp
            JOIN parts p ON p.id = cp.part_id
            WHERE cp.component_id = ?
              AND cp.part_id IN (?, ?, ?, ?)
            ORDER BY p.id
        """, (COMPONENT_ID, 7544, 7545, 7546, 7547)).fetchall()

        if len(rows) != 4:
            raise RuntimeError("Verifikasi gagal: jumlah relasi bukan 4.")

        con.commit()

    except Exception:
        con.rollback()
        raise

    print("BERHASIL: 4 relasi REF28–31 ditambahkan.")
    print("Backup:", backup)
    print("\n=== VERIFIKASI ===")
    for row in rows:
        print(dict(row))

    total = con.execute("""
        SELECT COUNT(*) FROM component_parts
        WHERE component_id = ?
    """, (COMPONENT_ID,)).fetchone()[0]
    print("\nTotal relasi Component568:", total)

except Exception as e:
    if con.in_transaction:
        con.rollback()
    raise SystemExit(f"DIBATALKAN: {e}")

finally:
    con.close()
