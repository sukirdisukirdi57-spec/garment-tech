import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-38.jpg"
SOURCE = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
TITLE = "18. PNEUMATIC COMPONENTS (TYPE L, ACCESSORIE PARTS)"

# REF, part number, official description, quantity_raw
ROWS = [
    (1,  "WP-0871602-SE", "WASHER 8.7X18X1.6",             "1"),
    (2,  "NM-6080721-SE", "NUT M8",                        "1"),
    (3,  "BT-0600401-EB", "TUBE",                          "0.5"),
    (4,  "SK-3452500-SC", "WOOD SCREW D=4.5 L=25",         "2"),
    (5,  "SL-9082093-SE", "SCREW",                        "1"),
    (6,  "400-75962",     "SOLENOID VALVE ASM(1)",         "1"),
    (7,  "SL-6041092-TN", "SCREW",                        "2"),
    (8,  "400-30950",     "SORENOID_VALVE_FITTING_BASE",   "1"),
    (9,  "400-30951",     "FILTER_REGULATOR_ASM.",         "1"),
    (10, "SL-4051091-SC", "SCREW M5X0.8 L=10",            "2"),
    (11, "400-23662",     "FILTER INSTALLING PLATE",       "1"),
    (12, "400-76736",     "SOLENOID_INSTALLING_PLATE_A_ASM.", "1"),
    (13, "BT-0600401-EB", "TUBE",                          "(1.1)"),
    (14, "400-76738",     "SOLENOID_INSTALLING_PLATE",     "(1)"),
    (15, "PV-1352070-00", "3-PORT ELECTROMAGNETIC VALVE",  "(1)"),
    (16, "PJ-3040652-01", "ELBOW UNION 6XPT1/4",           "(1)"),
    (17, "PJ-3050652-04", "DOUBLE-ENDED T UNION",          "(1)"),
    (18, "PV-1551130-00", "5-PORT SOLENOID VALVE",         "(1)"),
    (19, "PJ-3050651-07", "DOUBLE-ENDED T UNION",          "(1)"),
    (20, "PJ-3080600-05", "IKEI UNION",                    "(1)"),
    (21, "PC-0124060-00", "SPEED CONTROLLER",              "(2)"),
    (22, "PJ-3080400-02", "QUICK COUPLING",                "(4)"),
    (23, "SL-4031691-SC", "SCREW M3 L=16",                "(4)"),
    (24, "SL-4032591-SC", "SCREW M3X25",                  "(4)"),
    (25, "EA-9500B01-00", "CABLE BAND",                    "(3)"),
    (26, "BT-0400251-EB", "URETHANE HOSE BLACK",            "(0.6)"),
    (27, "401-78441",     "FG CABLE ASSY 1",               "1"),
    (28, "401-78442",     "FG CABLE ASSY 2",               "1"),
    (29, "SL-4040891-SC", "SCREW M4 L=8",                 "1"),
]

def numeric_quantity(raw):
    value = raw.strip().strip("()")
    number = float(value)
    return int(number) if number.is_integer() else number

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

if len(ROWS) != 29 or [r[0] for r in ROWS] != list(range(1, 30)):
    raise SystemExit("GAGAL: REF harus lengkap 1-29.")

if not Path("static/" + IMAGE).is_file():
    raise SystemExit("GAGAL: gambar halaman 38 tidak ditemukan.")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

machine = con.execute(
    "SELECT id, model FROM machines WHERE id=15"
).fetchone()
if not machine or machine["model"] != "AMS-210EN-1510":
    raise SystemExit("GAGAL: identitas machine ID15 tidak sesuai.")

doc = con.execute(
    "SELECT id, title FROM documents WHERE id=136 AND machine_id=15"
).fetchone()
if not doc:
    raise SystemExit("GAGAL: dokumen Parts List ID136 tidak ditemukan.")

existing = con.execute("""
    SELECT id, component_name
    FROM components
    WHERE machine_id=15 AND component_name=?
""", (TITLE,)).fetchall()
if existing:
    raise SystemExit(f"GAGAL: komponen sudah ada: {[dict(x) for x in existing]}")

print("=== PREFLIGHT SECTION 18 ===")
print("Machine:", dict(machine))
print("Dokumen:", dict(doc))
print("Judul:", TITLE)
print("REF katalog:", len(ROWS))
print("Gambar:", IMAGE, "| OK")
print("\n=== DAFTAR PART ===")

for ref, pn, name, raw in ROWS:
    qty = numeric_quantity(raw)
    print(
        f"REF{ref:02} | {pn:16} | Qty {str(raw):7} "
        f"| numeric={qty} | {name}"
    )

print("\n=== PEMERIKSAAN ===")
print("REF berurutan:", [r[0] for r in ROWS] == list(range(1, 30)))
print("Nomor part kosong:", sum(not r[1] for r in ROWS))
print("Quantity pecahan:", [
    (r[0], r[3]) for r in ROWS
    if not numeric_quantity(r[3]).is_integer()
])
print("Semua NOTE kosong sesuai tabel sumber: ya")
print("Part baru yang akan dibuat:", len(ROWS))
print("Relasi baru yang akan dibuat:", len(ROWS))

if not args.apply:
    print("\nDRY-RUN: belum ada perubahan database.")
    con.close()
    raise SystemExit(0)

backup = Path(
    "database/garment-before-ams210en1510-section18-"
    + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)
shutil.copy2(DB, backup)
print("\nBackup:", backup)

try:
    con.execute("BEGIN IMMEDIATE")

    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, part_number,
            location, function, notes, image_path,
            source_url, catalog_ref, diagram_page
        ) VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?, ?, ?)
    """, (
        15, TITLE,
        "AMS-210EN-1510 Parts List; Section 18",
        IMAGE, SOURCE, "18", 33
    ))
    component_id = cur.lastrowid

    for ref, pn, name, raw in ROWS:
        cur = con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number,
                part_name, quantity, catalog_ref, diagram_page,
                note, source_url, notes, quantity_raw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
        """, (
            15, 136, pn, name, numeric_quantity(raw),
            ref, 33, SOURCE,
            "AMS-210EN-1510 Parts List; Section 18",
            raw
        ))
        part_id = cur.lastrowid

        con.execute("""
            INSERT INTO component_parts (
                component_id, part_id, relation_type, notes
            ) VALUES (?, ?, ?, ?)
        """, (
            component_id, part_id,
            "catalog_component_part", f"REF {ref}"
        ))

    con.commit()
    print("\nAPPLY BERHASIL")
    print("Component ID:", component_id)
    print("Part dibuat:", len(ROWS))
    print("Relasi dibuat:", len(ROWS))

except Exception:
    con.rollback()
    raise
finally:
    con.close()
