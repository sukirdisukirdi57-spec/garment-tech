import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
MACHINE_ID = 44
SECTION = "AMS-210EN catalog staging; section 18"

# REF, PART NO, DESCRIPTION, quantity, quantity_raw
parts = [
    (1,  "WP-0871602-SE", "WASHER 8.7X18X1.6",              1, "1"),
    (2,  "NM-6080721-SE", "NUT M8",                          1, "1"),
    (3,  "BT-0600401-EB", "TUBE",                         None, "0.5"),
    (4,  "SK-3452500-SC", "WOOD SCREW D=4.5 L=25",           2, "2"),
    (5,  "SL-9082093-SE", "SCREW",                           1, "1"),
    (6,  "400-75962",     "SOLENOID VALVE ASM(1)",           1, "1"),
    (7,  "SL-6041092-TN", "SCREW",                           2, "2"),
    (8,  "400-30950",     "SORENOID_VALVE_FITTING_BASE",     1, "1"),
    (9,  "400-30951",     "FILTER_REGULATOR_ASM.",           1, "1"),
    (10, "SL-4051091-SC", "SCREW M5X0.8 L=10",               2, "2"),
    (11, "400-23662",     "FILTER INSTALLING PLATE",         1, "1"),
    (12, "400-76736",     "SOLENOID_INSTALLING_PLATE_A_ASM.",1, "1"),
    (13, "BT-0600401-EB", "TUBE",                         None, "(1.1)"),
    (14, "400-76738",     "SOLENOID_INSTALLING PLATE",       1, "(1)"),
    (15, "PV-1352070-00", "3-PORT ELECTROMAGNETIC VALVE",    1, "(1)"),
    (16, "PJ-3040652-01", "ELBOW UNION 6XPT1/4",             1, "(1)"),
    (17, "PJ-3050652-04", "DOUBLE-ENDED T UNION",            1, "(1)"),
    (18, "PV-1551130-00", "5-PORT SOLENOID VALVE",           1, "(1)"),
    (19, "PJ-3050651-07", "DOUBLE-ENDED T UNION",            1, "(1)"),
    (20, "PJ-3080600-05", "IKEI UNION",                      1, "(1)"),
    (21, "PC-0124060-00", "SPEED CONTROLLER",                2, "(2)"),
    (22, "PJ-3080400-02", "QUICK COUPLING",                  4, "(4)"),
    (23, "SL-4031691-SC", "SCREW M3 L=16",                   4, "(4)"),
    (24, "SL-4032591-SC", "SCREW M3X25",                    4, "(4)"),
    (25, "EA-9500B01-00", "CABLE BAND",                      3, "(3)"),
    (26, "BT-0400251-EB", "URETHANE HOSE BLACK",           None, "(0.6)"),
    (27, "401-78441",     "FG CABLE ASSY 1",                 1, "1"),
    (28, "401-78442",     "FG CABLE ASSY 2",                 1, "1"),
    (29, "SL-4040891-SC", "SCREW M4 L=8",                    1, "1"),
]

assert len(parts) == 29
assert [p[0] for p in parts] == list(range(1, 30))

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / (
    "garment-before-fix-pneumatic-section18-"
    + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)

src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(backup))
src.backup(dst)
dst.close()
src.close()
print("Backup:", backup)

con = sqlite3.connect(str(DB))
try:
    con.execute("BEGIN IMMEDIATE")

    if not con.execute(
        "SELECT 1 FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone():
        raise RuntimeError(f"Machine ID {MACHINE_ID} tidak ditemukan")

    existing = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id=? AND notes=?
    """, (MACHINE_ID, SECTION)).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Section 18 sudah berisi {existing} baris; INSERT dibatalkan."
        )

    con.executemany("""
        INSERT INTO parts (
            machine_id, source_document_id, part_number, part_name,
            quantity, catalog_ref, diagram_page, note,
            source_url, notes, quantity_raw
        )
        VALUES (?, NULL, ?, ?, ?, ?, NULL, 'COMMON', NULL, ?, ?)
    """, [
        (MACHINE_ID, pn, name, qty, ref, SECTION, raw)
        for ref, pn, name, qty, raw in parts
    ])

    rows = con.execute("""
        SELECT catalog_ref, COUNT(*)
        FROM parts
        WHERE machine_id=? AND notes=?
        GROUP BY catalog_ref
        ORDER BY catalog_ref
    """, (MACHINE_ID, SECTION)).fetchall()

    refs = [r[0] for r in rows]
    if refs != list(range(1, 30)) or any(n != 1 for _, n in rows):
        raise RuntimeError("Validasi REF gagal; transaksi dibatalkan.")

    con.commit()
    print("BERHASIL: Section 18 dimasukkan.")
    print("Jumlah baris:", len(rows))
    print("REF lengkap dan unik: 1–29")
    print("Kuantitas desimal disimpan di quantity_raw tanpa pembulatan.")
    print("Backup:", backup)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
