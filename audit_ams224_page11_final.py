import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
BACKUP = Path(
    "database/garment-before-ams224-page11-20261102-132618.db"
)

MACHINE_ID = 46
DOCUMENT_ID = 162
PDF_PAGE = 11

# REF: (part_id, part_number, part_name, quantity_raw)
EXPECTED = {
    "41": (9837, "400-24997", "LIFTER_BASE", "1"),
    "42": (9838, "SM-6061202-TP", "SCREW M6 L=12", "2"),
    "43": (9839, "WP-0641601-SC", "WASHER", "2"),
    "44": (9840, "401-42674", "CYLINDER_ARM_CAP_ASM.", "1"),
    "45": (9841, "401-76021", "CABLE_STAY", "1"),
    "46": (9842, "262-21200", "HOOK COVER PRESSER SPRING B", "1"),
    "47": (9843, "SM-6040860-TP", "SCREW M4 L=8", "1"),
    "48": (9844, "SL-4041091-SC", "SCREW M4 L=10", "1"),
    "49": (9845, "400-72244", "NEEDLE PLATE SUPPORT COVER ASM", "1"),
    "50": (9846, "401-01763", "SUS_NEEDLE_SUPPORT_PLATE_4530", "(1)"),
    "51": (9847, "400-72176", "COVER_SUPPORT_A_RIGHT", "(2)"),
    "52": (9848, "400-72175", "COVER_SUPPORT_A_LEFT", "(2)"),
    "53": (9849, "400-72179", "COVER_SUPPORT_BRACKET", "(6)"),
    "54": (9850, "400-25014", "COVER_SUPPORT_B", "(2)"),
    "55": (9851, "SM-6450610-TP", "SCREW", "(32)"),
    "56": (9852, "WP-0450801-SP", "WASHER", "(32)"),
    "57": (9853, "SM-6040802-TP", "SCREW M4X0.7 L=8", "(24)"),
    "58": (9854, "WP-0450801-SP", "WASHER", "(24)"),
    "59": (9855, "400-72178", "COVER_SUPPORT_B_RIGHT", "(1)"),
    "60": (9856, "400-72177", "COVER_SUPPORT_B_LEFT", "(1)"),
}

def fail(message):
    raise RuntimeError(message)

if not DB.exists():
    fail(f"Database aktif tidak ditemukan: {DB}")

if not BACKUP.exists():
    fail(f"Backup pembanding tidak ditemukan: {BACKUP}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
bak = sqlite3.connect(BACKUP)

try:
    print("=== AUDIT OCCURRENCES REF 41-60 ===")

    rows = con.execute("""
        SELECT catalog_ref, machine_id, source_document_id,
               pdf_page, part_number, part_name, quantity_raw
        FROM catalog_occurrences
        WHERE machine_id = ?
          AND source_document_id = ?
          AND pdf_page = ?
          AND CAST(catalog_ref AS INTEGER) BETWEEN 41 AND 60
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, DOCUMENT_ID, PDF_PAGE)).fetchall()

    if len(rows) != 20:
        fail(f"Jumlah occurrence salah: ditemukan {len(rows)}, seharusnya 20")

    seen = set()

    for row in rows:
        ref = str(row["catalog_ref"])
        if ref in seen:
            fail(f"REF duplikat: {ref}")
        seen.add(ref)

        if ref not in EXPECTED:
            fail(f"REF tidak dikenal: {ref}")

        part_id, number, name, qty = EXPECTED[ref]

        actual = (
            row["part_number"],
            row["part_name"],
            row["quantity_raw"],
        )
        wanted = (number, name, qty)

        if actual != wanted:
            fail(
                f"REF {ref} tidak cocok.\n"
                f"  Aktual : {actual}\n"
                f"  Target : {wanted}"
            )

        part = con.execute(
            "SELECT * FROM parts WHERE id = ?",
            (part_id,)
        ).fetchone()

        if part is None:
            fail(f"Part ID {part_id} tidak ditemukan untuk REF {ref}")

        part_cols = set(part.keys())

        number_col = next(
            (c for c in ("part_number", "parts_number")
             if c in part_cols), None
        )
        name_col = next(
            (c for c in ("part_name", "description", "name")
             if c in part_cols), None
        )

        if number_col and part[number_col] != number:
            fail(f"Nomor part pada parts.id={part_id} tidak cocok")

        if name_col and part[name_col] != name:
            fail(f"Nama part pada parts.id={part_id} tidak cocok")

        print(
            f"OK REF {ref:>2} | ID {part_id} | "
            f"{number} | {qty}"
        )

    if seen != set(EXPECTED):
        fail("Ada REF yang hilang.")

    print("\n=== PERBANDINGAN TABEL TERHADAP BACKUP ===")

    for table in ("parts", "component_parts", "components"):
        current = con.execute(
            f'SELECT * FROM "{table}" ORDER BY rowid'
        ).fetchall()

        previous = bak.execute(
            f'SELECT * FROM "{table}" ORDER BY rowid'
        ).fetchall()

        current_data = [tuple(row) for row in current]
        previous_data = [tuple(row) for row in previous]

        if current_data != previous_data:
            fail(
                f"Tabel {table} BERUBAH dibanding backup. "
                "Perlu pemeriksaan lebih lanjut."
            )

        print(f"OK {table}: tidak berubah ({len(current_data)} baris)")

    print("\n=== HASIL AKHIR ===")
    print("Occurrence REF 41-60 : 20/20 cocok")
    print("Parts                : tidak berubah")
    print("Component parts      : tidak berubah")
    print("Components           : tidak berubah")
    print("STATUS               : AUDIT LULUS")

finally:
    con.close()
    bak.close()
