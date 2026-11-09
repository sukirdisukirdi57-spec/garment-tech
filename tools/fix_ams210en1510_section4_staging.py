import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
MACHINE_ID = 15
STAGING_NOTE = "AMS-210EN catalog staging; section 4"

# REF, PART NUMBER, DESCRIPTION, QTY RAW, MARKER
NEW_ROWS = [
    (19, "TA-0670604-R0", "PLUG D=6.7 L=6", "(1)", "COMMON"),
    (29, "SB-3070002-0A", "BEARING", "2", "#01"),
    (30, "SB-3070002-0B", "BEARING", "2", "#01"),
    (31, "SB-3070002-0C", "BEARING", "2", "#01"),
    (32, "SB-3070002-0D", "BEARING", "2", "#01"),
    (34, "SM-8060812-TP", "SCREW M6 L=8", "2", "COMMON"),
    (35, "SM-8480652-TP", "SCREW", "3", "COMMON"),
    (43, "SM-8060812-TP", "SCREW M6 L=8", "4", "COMMON"),
    (53, "SM-8040310-SS", "SCREW M4 L=3", "2", "COMMON"),
    (60, "B1405-210-000", "THREAD GUIDE A", "1", "☆ #04"),
    (61, "400-26884", "NEEDLE_BAR_SHREAD_GUIDE_H", "1", "☆ #05"),
    (79, "MDP-500B1400", "NEEDLE DPX5 #14", "1", "☆ #06"),
    (80, "MDP-170B1800", "NEEDLE DPX17 #18", "1", "☆ #02"),
    (81, "MC-2005010-00", "NEEDLE 134 NM100/DPX134 #16", "1", "☆ #07"),
    (82, "MC-3720011-00", "NEEDLE 135X17 #110", "1", "☆ #03"),
    (83, "400-78079", "THREAD_TAKE_UP_CRANK_SHAFT", "1", "COMMON"),
    (84, "SM-8061612-TP", "SCREW M6X16", "2", "COMMON"),
    (85, "400-00299", "NEEDLE FEED SHAFT METAL", "1", "COMMON"),
    (86, "SM-8480652-TP", "SCREW", "1", "COMMON"),
    (87, "400-78107", "KNIFE", "1", "COMMON"),
    (88, "SM-6030450-TP", "SCREW M3 L=4", "2", "COMMON"),
    (89, "400-78160", "NEEDLE_ROD_METAL_GREASE_COVER", "1", "COMMON"),
]

EXPECTED_EXISTING = set(range(1, 90)) - {
    19, 29, 30, 31, 32, 34, 35, 43, 53,
    60, 61, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89
}

def stop(message):
    raise SystemExit("STOP: " + message)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.exists():
        stop(f"Database tidak ditemukan: {DB}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, catalog_ref, part_number, part_name,
               quantity, quantity_raw, note,
               source_document_id, diagram_page, source_url
        FROM parts
        WHERE machine_id=? AND notes=?
        ORDER BY CAST(catalog_ref AS INTEGER), id
    """, (MACHINE_ID, STAGING_NOTE)).fetchall()

    refs = [int(r["catalog_ref"]) for r in rows]
    if len(refs) != len(set(refs)):
        stop("Ada catalog_ref ganda dalam staging Section 4")

    existing = set(refs)
    expected_missing = {r[0] for r in NEW_ROWS}

    print("=== PREFLIGHT PERBAIKAN SECTION 4 STAGING ===")
    print("Baris staging sekarang:", len(rows))
    print("REF lama:", len(existing))
    print("REF yang akan ditambahkan:", len(expected_missing))
    print("Daftar REF baru:", sorted(expected_missing))

    if existing != EXPECTED_EXISTING:
        stop(
            "REF lama tidak sesuai baseline audit. "
            f"Selisih: {sorted(existing ^ EXPECTED_EXISTING)}"
        )

    if expected_missing & existing:
        stop("Ada REF baru yang ternyata sudah ada")

    for r in rows:
        if r["note"] != "COMMON":
            stop(f"Marker baris lama berubah: REF {r['catalog_ref']}")
        if r["source_document_id"] is not None:
            stop(f"source_document_id staging tidak sesuai: REF {r['catalog_ref']}")

    print("REF lama: VALID (67/67)")
    print("Tidak ada REF ganda: VALID")
    print("Marker baris lama: COMMON, tidak diubah")
    print("Duplikasi part number lintas REF: dipertahankan")
    print("Quantity raw: akan dipertahankan persis")
    print("Metadata staging: mengikuti pola lama (NULL)")

    if not args.apply:
        print("\nDRY-RUN BERHASIL. Belum ada perubahan database.")
        conn.close()
        return

    backup = DB.with_name(
        f"garment-before-ams210en1510-section4-staging-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    conn.close()
    shutil.copy2(DB, backup)
    print("\nBackup:", backup)

    conn = sqlite3.connect(DB)
    try:
        conn.execute("BEGIN IMMEDIATE")

        current = conn.execute("""
            SELECT catalog_ref
            FROM parts
            WHERE machine_id=? AND notes=?
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        current_refs = {int(r[0]) for r in current}
        if current_refs != EXPECTED_EXISTING:
            stop("Database berubah setelah preflight; transaksi dibatalkan")

        for ref, pn, name, qty_raw, marker in NEW_ROWS:
            qty = int(qty_raw.strip("()"))
            conn.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number, part_name,
                    quantity, catalog_ref, diagram_page, note,
                    source_url, notes, quantity_raw
                )
                VALUES (?, NULL, ?, ?, ?, ?, NULL, ?, NULL, ?, ?)
            """, (
                MACHINE_ID, pn, name, qty, ref,
                marker, STAGING_NOTE, qty_raw
            ))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    # Audit hasil setelah commit
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    final_rows = conn.execute("""
        SELECT catalog_ref, part_number, part_name,
               quantity, quantity_raw, note
        FROM parts
        WHERE machine_id=? AND notes=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, STAGING_NOTE)).fetchall()

    final_refs = [int(r["catalog_ref"]) for r in final_rows]
    expected_all = set(range(1, 90))

    if len(final_rows) != 89 or set(final_refs) != expected_all:
        stop("Audit akhir gagal: REF tidak lengkap 1-89")

    by_ref = {int(r["catalog_ref"]): r for r in final_rows}
    for ref, pn, name, qty_raw, marker in NEW_ROWS:
        r = by_ref[ref]
        if (
            r["part_number"] != pn
            or r["part_name"] != name
            or r["quantity_raw"] != qty_raw
            or r["quantity"] != int(qty_raw.strip("()"))
            or r["note"] != marker
        ):
            stop(f"Audit isi gagal pada REF {ref}")

    print("\n=== HASIL APPLY ===")
    print("Total staging:", len(final_rows))
    print("REF lengkap 1-89: VALID")
    print("REF baru tervalidasi:", len(NEW_ROWS))
    print("Marker khusus:", [
        (ref, by_ref[ref]["note"])
        for ref in (29, 30, 31, 32, 60, 61, 79, 80, 81, 82)
    ])
    print("Quantity raw dan quantity numerik: VALID")
    print("Backup aman:", backup)
    conn.close()

if __name__ == "__main__":
    main()
