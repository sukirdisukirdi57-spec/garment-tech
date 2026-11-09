import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
SECTION = "AMS-210EN catalog staging; section 15"
MACHINE_ID = 44

# REF, Part No., Description, Qty, Note
parts = [
    (1,  "400-23636",       "FEED BRACKET",                         1, "COMMON"),
    (2,  "400-23645",       "LIFTING LEVER RIGHT",                  1, "COMMON"),
    (3,  "400-23646",       "LIFTING LEVER LEFT",                   1, "COMMON"),
    (4,  "400-23652",       "FEED BRACKET UPPER LINK RIGHT",        1, "COMMON"),
    (5,  "400-23653",       "FEED BRACKET UPPER LINK LEFT",         1, "COMMON"),
    (6,  "400-23649",       "SUPPORT LINK RIGHT",                   1, "COMMON"),
    (7,  "400-23650",       "SUPPORT LINK LEFT",                    1, "COMMON"),
    (8,  "B2579-210-D00-A", "SLIDER",                               1, "COMMON"),
    (9,  "400-23648",       "SLIDER SHAFT",                         1, "COMMON"),
    (10, "400-23638",       "FEEDING FRAME",                        1, "#01"),
    (11, "400-71897",       "FEEDING_FRAME_1510",                   1, "#02"),
    (12, "401-78093",       "LOWER PLATE",                          1, "#01"),
    (13, "401-78092",       "LOWER PLATE",                          1, "#02"),
    (14, "B2583-210-D00",   "SPRING",                               2, "COMMON"),
    (15, "B2581-210-D00",   "SPRING RIGHT",                         1, "COMMON"),
    (16, "B2582-210-D00",   "SPRING LEFT",                          1, "COMMON"),
    (17, "400-23651",       "FEED BRACKET LINK",                    1, "COMMON"),
    (18, "400-23654",       "LINK STOPPER",                         2, "COMMON"),
    (19, "B1626-555-000",   "FEED REGULATOR CONNECTING ROD PIN",    2, "COMMON"),
    (20, "400-23663",       "SHAFT BLOCK SHAFT",                    1, "COMMON"),
    (21, "400-23635",       "CYLINDER PIN",                         2, "COMMON"),
    (22, "CS-079073A-SH",   "THRUST COLLAR ASM.",                    1, "COMMON"),
    (23, "RE-0300000-K0",   "E-RING 3",                             4, "COMMON"),
    (24, "RE-0300000-K0",   "E-RING 3",                             2, "COMMON"),
    (25, "RE-0700000-K0",   "E-RING 7",                             1, "COMMON"),
    (26, "SB-7100005-00",   "BEARING",                              1, "COMMON"),
    (27, "SM-6030802-TP",   "SCREW M3X0.5 L=8",                     1, "COMMON"),
    (28, "WS-0410002-KP",   "SPRING WASHER",                        2, "COMMON"),
    (29, "SM-6061002-TP",   "SCREW M6 L=10",                       2, "COMMON"),
    (30, "WP-0651001-SC",   "WASHER",                               2, "COMMON"),
    (31, "SM-6061402-TN",   "BOLT",                                 2, "COMMON"),
    (32, "WP-0651001-SC",   "WASHER",                               2, "COMMON"),
    (33, "SM-8050412-TP",   "SCREW M5 L=4",                        2, "COMMON"),
    (34, "SM-6040800-SP",   "SCREW",                                2, "#01"),
    (35, "WP-0480856-SP",   "WASHER 4.8X8.4X0.8",                   2, "#01"),
    (36, "SM-6450610-TP",   "SCREW",                                4, "COMMON"),
    (37, "B2557-280-00C",   "WASHER",                               1, "COMMON"),
    (38, "400-86368",       "WORK_CLAMP_FOOT_PLATE_BASE",           1, "COMMON"),
    (39, "SM-1040870-TP",   "SCREW",                                4, "COMMON"),
    (40, "SM-6041002-TP",   "SCREW M4 L=10",                       2, "COMMON"),
    (41, "400-86370",       "WORK_CLAMP_FOOT_SLIDE_PLATE_ASM.",     2, "COMMON"),
    (42, "B2513-215-000",   "BEARING",                              4, "COMMON"),
    (43, "400-52852",       "WORK_CLAMP_FOOT_PLATE_A_ASM.",         1, "COMMON"),
    (44, "SM-1040801-SP",   "SCREW M4X0.7 L=8",                    2, "COMMON"),
    (45, "400-52854",       "WORK_CLAMP_FOOT_PLATE_B_ASM.",         2, "COMMON"),
    (46, "SM-6041202-TP",   "SCREW M4X0.7 L=12",                   4, "COMMON"),
    (47, "WP-0480856-SP",   "WASHER 4.8X8.4X0.8",                   4, "COMMON"),
    (48, "NM-6040001-SP",   "NUT M4X0.7",                          4, "COMMON"),
    (49, "400-86376",       "RECEIVER_PLATE_RIGHT_ASM",             1, "#01"),
    (50, "SM-6041050-TP",   "SCREW",                                2, "COMMON"),
    (51, "400-86378",       "RECEIVER_PLATE_LEFT_ASM",              1, "#01"),
    (52, "SM-6041050-TP",   "SCREW",                                2, "COMMON"),
    (53, "400-86372",       "RECEIVER_PLATE_RIGHT_ASM",             1, "#02"),
    (54, "400-86374",       "RECEIVER_PLATE_LEFT_ASM",              1, "#02"),
    (55, "SM-8030612-TP",   "SET SCREW",                            4, "COMMON"),
    (56, "SM-6050800-SP",   "SCREW M5 L=8",                        4, "#02"),
    (57, "WP-0550800-SP",   "WASHER 5.5X10X0.8",                    4, "#02"),
    (58, "SM-8050812-TP",   "SCREW M5X8",                          2, "#02"),
    (59, "NM-6050001-SD",   "NUT M5X0.8",                          2, "#02"),
]

# Validasi data skrip sebelum menyentuh database.
assert len(parts) == 59, f"Jumlah data bukan 59: {len(parts)}"
assert [p[0] for p in parts] == list(range(1, 60)), "REF tidak lengkap/berurutan"

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"garment-before-fix-cloth-feed-section15-{stamp}.db"

# Backup konsisten menggunakan SQLite backup API.
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(backup))
src.backup(dst)
dst.close()
src.close()
print("Backup dibuat:", backup)

con = sqlite3.connect(str(DB))
con.row_factory = sqlite3.Row

try:
    con.execute("BEGIN IMMEDIATE")

    # Pastikan machine 44 ada.
    machine = con.execute(
        "SELECT id FROM machines WHERE id = ?", (MACHINE_ID,)
    ).fetchone()
    if not machine:
        raise RuntimeError(f"Machine ID {MACHINE_ID} tidak ditemukan.")

    # Jangan mengulang proses jika section sudah memiliki data.
    existing = con.execute("""
        SELECT id, catalog_ref, part_number
        FROM parts
        WHERE machine_id = 44 AND notes = ?
    """, (SECTION,)).fetchall()

    if existing:
        raise RuntimeError(
            f"Section 15 sudah berisi {len(existing)} baris; dibatalkan "
            "agar tidak terjadi duplikasi."
        )

    # Pastikan setiap REF target belum digunakan pada penanda section 15.
    # Tidak menolak nomor part yang sama di section lain.
    for ref, pn, name, qty, note in parts:
        if not pn or not name or qty <= 0:
            raise RuntimeError(f"Data tidak valid pada REF {ref}")

    # Mengikuti pola staging AMS-210EN yang ada:
    # source_document_id dan diagram_page tetap NULL.
    con.executemany("""
        INSERT INTO parts (
            machine_id, source_document_id, part_number, part_name,
            quantity, catalog_ref, diagram_page, note,
            source_url, notes, quantity_raw
        )
        VALUES (?, NULL, ?, ?, ?, ?, NULL, ?, NULL, ?, ?)
    """, [
        (
            MACHINE_ID, pn, name, qty, ref, note,
            SECTION, str(qty)
        )
        for ref, pn, name, qty, note in parts
    ])

    # Audit di dalam transaksi sebelum commit.
    rows = con.execute("""
        SELECT catalog_ref, part_number, part_name, quantity,
               quantity_raw, note
        FROM parts
        WHERE machine_id = 44 AND notes = ?
        ORDER BY catalog_ref
    """, (SECTION,)).fetchall()

    refs = [r["catalog_ref"] for r in rows]
    if len(rows) != 59 or refs != list(range(1, 60)):
        raise RuntimeError("Audit REF 1–59 gagal; transaksi dibatalkan.")

    con.commit()

    print("\nBERHASIL: Section 15 dimasukkan.")
    print("Jumlah baris:", len(rows))
    print("REF:", refs[0], "sampai", refs[-1])
    print("Backup:", backup)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
