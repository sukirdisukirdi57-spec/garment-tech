import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
COMPONENT_ID = 567

# REF, part_id, part_number, part_name, quantity_raw
EXPECTED = [
    (23, 7339, "131-22403", "FEED BRANCH CRANK", "(1)"),
    (24, 7340, "SM-6061402-TP", "SCREW M6 L=14", "(1)"),
    (25, 7341, "RC-0650811-KP", "RETAINING RING", "2"),
    (26, 7342, "400-25429", "ROD_CONNECTING_SHAFT", "1"),
    (27, 7343, "WP-1221016-SP", "WASHER", "1"),
]

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

backup = DB.with_name(
    f"garment-before-feed-branch-crank-{datetime.now():%Y%m%d-%H%M%S}.db"
)

shutil.copy2(DB, backup)
print("Backup:", backup)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    con.execute("BEGIN IMMEDIATE")

    component = con.execute("""
        SELECT id, machine_id, component_name, part_number
        FROM components
        WHERE id = ?
    """, (COMPONENT_ID,)).fetchone()

    if not component:
        raise RuntimeError("Component ID 567 tidak ditemukan.")

    if component["machine_id"] != 44:
        raise RuntimeError("Machine ID component bukan 44.")

    if component["part_number"] != "131-22452":
        raise RuntimeError("Part number component tidak sesuai.")

    # Pastikan REF22 induk sudah terhubung.
    parent = con.execute("""
        SELECT COUNT(*)
        FROM component_parts
        WHERE component_id = 567 AND part_id = 7338
    """).fetchone()[0]

    if parent != 1:
        raise RuntimeError("Relasi induk REF22 tidak ditemukan atau tidak unik.")

    # Validasi seluruh kandidat sebelum menambahkan apa pun.
    for ref, part_id, pn, name, qty in EXPECTED:
        row = con.execute("""
            SELECT id, machine_id, part_number, part_name,
                   quantity_raw, notes
            FROM parts
            WHERE id = ?
        """, (part_id,)).fetchone()

        if not row:
            raise RuntimeError(f"Part ID {part_id} tidak ditemukan.")

        actual = (
            row["machine_id"], row["part_number"],
            row["part_name"], row["quantity_raw"]
        )
        expected = (44, pn, name, qty)

        if actual != expected:
            raise RuntimeError(
                f"Data REF{ref} tidak cocok: {actual} != {expected}"
            )

        if "section 5" not in (row["notes"] or ""):
            raise RuntimeError(f"REF{ref} bukan staging section 5.")

        exists = con.execute("""
            SELECT COUNT(*)
            FROM component_parts
            WHERE component_id = 567 AND part_id = ?
        """, (part_id,)).fetchone()[0]

        if exists:
            raise RuntimeError(f"Relasi REF{ref} sudah ada.")

    # Tambahkan 5 relasi.
    for ref, part_id, pn, name, qty in EXPECTED:
        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
            VALUES (?, ?, ?, ?)
        """, (
            COMPONENT_ID,
            part_id,
            "catalog_component_part",
            f"JUKI AMS-210EN Section 5; REF{ref}"
        ))

    # Verifikasi sebelum commit.
    linked = con.execute("""
        SELECT p.id, p.part_number, p.part_name, p.quantity_raw,
               cp.relation_type, cp.notes
        FROM component_parts cp
        JOIN parts p ON p.id = cp.part_id
        WHERE cp.component_id = 567
        ORDER BY p.catalog_ref, p.id
    """).fetchall()

    refs_added = [
        r for r in linked
        if r["notes"] in {
            f"JUKI AMS-210EN Section 5; REF{ref}"
            for ref, *_ in EXPECTED
        }
    ]

    if len(refs_added) != 5:
        raise RuntimeError("Verifikasi jumlah relasi baru gagal.")

    con.commit()

    print("\nBERHASIL: 5 relasi baru ditambahkan.")
    print("Total relasi Component567:", len(linked))
    print("\n=== VERIFIKASI ===")
    for r in refs_added:
        print(dict(r))

except Exception:
    con.rollback()
    print("\nGAGAL: transaksi dibatalkan.")
    raise
finally:
    con.close()
