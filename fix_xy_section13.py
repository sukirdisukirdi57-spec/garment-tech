import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import re

DB = Path("database/garment.db")
MACHINE_ID = 44
SECTION = "AMS-210EN catalog staging; section 13"

# REF, part number, description, NOTE, quantity as printed in catalog.
CATALOG = [
    (1,  "400-78001",      "X-Y_TABLE_ASM_1306",             "#01", "1"),
    (2,  "400-77999",      "X-Y_TABLE_ASM_1510",             "#02", "1"),
    (3,  "400-78000",      "X-Y_TABLE_ASM_2210",             "#03", "1"),
    (4,  "400-30945",      "X_FIXED_RACE",                   "#01", "(2)"),
    (5,  "400-33145",      "X_FIXED_RACE",                   "#02", "(2)"),
    (6,  "400-38562",      "X FIXED RACE",                   "#03", "(2)"),
    (7,  "B2520-210-D0A",  "Y FIXED RACE RIGHT",             "#01", "(1)"),
    (8,  "400-33146",      "Y_FIXED_RACE_RIGHT",             "#04", "(1)"),
    (9,  "B2521-210-D00",  "Y BALL GAUGE",                   "#01", "(2)"),
    (10, "400-33148",      "Y_BALL_GAUGE",                   "#04", "(2)"),
    (11, "B2522-210-D00",  "Y STOPPER",                      "#01", "(1)"),
    (12, "400-33149",      "Y_STOPPER",                      "#04", "(1)"),
    (13, "400-30946",      "Y_REMOVAL_RACE",                 "COMMON", "(1)"),
    (14, "B2520-210-D0B",  "Y FIXED RACE LEFT",              "#01", "(1)"),
    (15, "400-33147",      "Y_FIXED_RACE_LEFT",              "#04", "(1)"),
    (16, "400-77998",      "RACE TABLE",                     "COMMON", "(1)"),
    (17, "B2508-210-DA0",  "X BALL GAUGE ASM.",              "#01", "(2)"),
    (18, "400-33150",      "X_BALL_GAUGE_ASM",               "#02", "(2)"),
    (19, "B2508-210-DAB",  "X BALL GAUGE ASM.(EXTENSION)",   "#03", "(2)"),
    (20, "400-33153",      "X_STOPPER",                      "COMMON", "(2)"),
    (21, "B2527-210-000",  "BALL",                           "#01", "(30)"),
    (22, "B2527-210-000",  "BALL",                           "#04", "(36)"),
    (23, "SM-6041002-TP",  "SCREW M4 L=10",                  "COMMON", "(4)"),
    (24, "SM-6040860-TP",  "SCREW M4 L=8",                   "COMMON", "(4)"),
    (25, "SM-6040802-TP",  "SCREW M4X0.7 L=8",               "COMMON", "(4)"),
    (26, "SM-8040602-TP",  "SCREW M4X0.7 L=6",               "COMMON", "(2)"),
    (27, "B2522-210-D00",  "Y STOPPER",                      "COMMON", "(1)"),
    (28, "WP-0450846-SP",  "WASHER",                         "#04", "(2)"),
    (29, "WP-0450846-SP",  "WASHER",                         "#02", "(2)"),
    (30, "400-77990",      "X_SENSOR_SLIT",                  "COMMON", "1"),
    (31, "226-87701",      "SPRING SHAFT",                   "COMMON", "1"),
    (32, "NM-6050001-SP",  "NUT M5",                         "COMMON", "3"),
    (33, "SB-1080005-00",  "RADIAL BEARING",                 "COMMON", "2"),
    (34, "SM-6040802-TP",  "SCREW M4X0.7 L=8",               "COMMON", "2"),
    (35, "SM-6040602-TP",  "SCREW M4 L=6",                   "COMMON", "2"),
    (36, "SM-6052502-TP",  "SCREW M5X0.8 L=25",              "COMMON", "1"),
    (37, "SM-8050412-TP",  "SCREW M5 L=4",                   "COMMON", "1"),
    (38, "B1519-026-00G",  "HINGE STUD",                     "COMMON", "2"),
    (39, "SM-6041202-TP",  "SCREW M4X0.7 L=12",              "COMMON", "4"),
    (40, "WP-0450801-SP",  "WASHER",                         "COMMON", "4"),
    (41, "SM-6041402-TP",  "SCREW M4 L=14",                  "COMMON", "8"),
    (42, "400-77991",      "X DRIVEN BRACKET",               "COMMON", "1"),
    (43, "WP-0520656-SA",  "WASHER 5.2X9.5X0.6",             "COMMON", "1"),
    (44, "400-77992",      "BELT RECEIVER",                  "COMMON", "1"),
    (45, "400-77997",      "X BELT BASE",                    "COMMON", "1"),
    (46, "400-77995",      "DRIVEN_SPROCKET",                "COMMON", "1"),
    (47, "SM-8050812-TP",  "SCREW M5X8",                     "COMMON", "2"),
    (48, "400-77993",      "TIMMING_BELT",                   "COMMON", "1"),
]

def numeric_quantity(raw):
    return int(re.sub(r"[()]", "", raw))

def main():
    if not DB.exists():
        raise FileNotFoundError(f"Database tidak ditemukan: {DB}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        con.execute("PRAGMA busy_timeout=5000")

        existing = con.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note
            FROM parts
            WHERE machine_id=?
              AND notes LIKE ?
        """, (MACHINE_ID, "%section 13%")).fetchall()

        by_ref = {}
        for row in existing:
            ref = row["catalog_ref"]
            if ref in by_ref:
                raise RuntimeError(f"REF {ref} duplikat sebelum perbaikan")
            by_ref[ref] = row

        # Pastikan REF yang sudah ada cocok dengan katalog.
        for ref, part_no, name, note, raw in CATALOG:
            if ref not in by_ref:
                continue
            row = by_ref[ref]
            actual = (
                row["part_number"], row["part_name"], row["quantity_raw"]
            )
            expected = (part_no, name, raw)
            if actual != expected:
                raise RuntimeError(
                    f"REF {ref} tidak cocok; tidak ada perubahan.\n"
                    f"Aktual:   {actual}\n"
                    f"Katalog:  {expected}\n"
                    f"ID: {row['id']}"
                )

        unexpected = sorted(set(by_ref) - set(range(1, 49)))
        if unexpected:
            raise RuntimeError(f"REF di luar katalog 1–48: {unexpected}")

        missing = [item for item in CATALOG if item[0] not in by_ref]
        if not missing:
            print("Section 13 sudah lengkap; tidak ada perubahan.")
            return

        backup = Path("backups") / (
            "garment-before-fix-xy-section13-"
            + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
        )
        backup.parent.mkdir(parents=True, exist_ok=True)
        con.commit()
        shutil.copy2(DB, backup)
        print("BACKUP:", backup)

        con.execute("BEGIN IMMEDIATE")

        for ref, part_no, name, note, raw in missing:
            con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number, part_name,
                    quantity, catalog_ref, diagram_page, note, source_url,
                    notes, quantity_raw
                ) VALUES (?, NULL, ?, ?, ?, ?, NULL, ?, NULL, ?, ?)
            """, (
                MACHINE_ID, part_no, name, numeric_quantity(raw),
                ref, note, SECTION, raw
            ))

        rows = con.execute("""
            SELECT id, catalog_ref, part_number, part_name, quantity_raw
            FROM parts
            WHERE machine_id=?
              AND notes LIKE ?
            ORDER BY catalog_ref
        """, (MACHINE_ID, "%section 13%")).fetchall()

        refs = [r["catalog_ref"] for r in rows]
        if len(rows) != 48 or refs != list(range(1, 49)):
            raise RuntimeError(
                f"Audit gagal: {len(rows)} baris, REF={refs}"
            )

        # Pastikan baris lama tetap ada dengan ID yang sama.
        for ref, old in by_ref.items():
            check = con.execute("""
                SELECT id, part_number, part_name, quantity_raw
                FROM parts
                WHERE machine_id=? AND catalog_ref=?
                  AND notes LIKE ?
            """, (MACHINE_ID, ref, "%section 13%")).fetchone()
            if check is None or check["id"] != old["id"]:
                raise RuntimeError(f"Baris lama REF {ref} berubah/hilang")

        con.commit()
        print("\nBERHASIL")
        print("Baris baru ditambahkan:", len(missing))
        print("Section 13:", len(rows), "baris; REF 1–48 lengkap.")
        print("Baris lama dipertahankan:", len(by_ref))
        print("Backup:", backup)

    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
