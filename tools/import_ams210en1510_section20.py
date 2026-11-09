import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TITLE = "20. OPERATION PANEL COMPONENTS"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-40.jpg"
SOURCE = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"

# REF, part number, official description, quantity_raw, NOTE, symbol
ROWS = [
    (1,  "400-86485",     "IP-420F PANEL ASSY",                  "1",    None, None),
    (2,  "400-78163",     "FRONT_CASE",                          "(1)",  None, None),
    (3,  "400-80799",     "REAR_CASE_ASSY",                      "(1)",  None, None),
    (4,  "400-80800",     "LCD_ASSY",                            "(1)",  None, None),
    (5,  "400-86541",     "LCD TOUCH PANEL ASSY",                "(1)",  None, None),
    (6,  "400-83668",     "LCD_BRACKET",                         "(1)",  None, None),
    (7,  "400-83666",     "LCD_STAY",                            "(1)",  None, None),
    (8,  "SL-4030681-SC", "SCREW M3 L=6",                        "(2)",  None, None),
    (9,  "400-78168",     "INSULATION_SHEET",                    "(1)",  None, None),
    (10, "400-83960",     "PANEL PCB ASSY",                      "(1)",  None, None),
    (11, "SL-4030681-SC", "SCREW M3 L=6",                        "(3)",  None, None),
    (12, "HX-0035400-0B", "PCB SUPPORT L=8MM",                   "(2)",  None, None),
    (13, "SL-4030881-SC", "SCREW M3X8",                         "(4)",  None, None),
    (14, "CM-6001001-01", "WEEE MARK LABEL S",                   "(1)",  None, None),
    (15, "HW-0021802-00", "FLAT CABLE",                          "(1)",  None, None),
    (16, "400-81602",     "POWER SWITCH ASM",                    "1",    None, None),
    (17, "HA-0058200-00", "SWITCH",                              "(1)",  None, None),
    (18, "400-81603",     "SWITCH INSTALLATION BOARD",            "(1)",  None, None),
    (19, "SL-4041091-SE", "SCREW M4 L=10",                       "(2)",  None, None),
    (20, "CM-3001004-01", "LABEL 3 (LARGE)",                     "1",    "#01", None),
    (21, "BME-01100000",  "VOLTAGE INDICATION SEAL",             "1",    "#01", None),
    (22, "CM-3004007-01", "VOLTAGE CAUTION LABEL",               "1",    "#02", None),
    (23, "BME-03200000",  "VOLTAGE INDICATION SEAL",             "1",    "#02", None),
    (24, "CM-3001000-03", "VOLTAGE WARNING LABEL(25)",           "1",    "#03", None),
    (25, "CM-3004006-01", "VOLTAGE CAUTION LABEL",               "1",    "#03", None),
    (26, "400-85316",     "OPTION A ASSY",                       "1",    None, None),
    (27, "M3004-511-00A", "VOLTAGE INDICATION CARD A",           "(1)",  None, None),
    (28, "HF-0013031-5S", "FUSE 3.15A 250V REF. NO.112",         "(1)",  None, None),
    (29, "HF-0030002-00", "FUSE 2A (220/240V)",                  "(1)",  None, None),
    (30, "HF-0013050-P0", "FUSE 5A",                            "(1)",  None, None),
    (31, "MA-0115320-00", "STAPLE",                              "(3)",  None, None),
    (32, "SK-3512001-SE", "WOOD SCREW D=5.1 L=20",               "(2)",  None, None),
    (33, "MTS-HJ100003",  "BOLT",                                "(2)",  None, None),
    (34, "SM-6084002-TN", "SCREW M8 L=40",                       "(1)",  None, None),
    (35, "WP-0852086-SC", "WASHER M8",                           "(2)",  None, None),
    (36, "WP-0841601-SC", "WASHER 8.4X17.4X1.6",                "(1)",  None, None),
    (37, "WS-0820002-KR", "SPRING WASHER M8",                    "(3)",  None, None),
    (38, "NM-6080002-SC", "NUT M8",                              "(2)",  None, None),
    (39, "HX-0015000-0D", "CABLE CLIP",                          "(2)",  None, None),
    (40, "SL-4040881-SC", "SCREW M4 L=8",                        "(2)",  None, None),
    (41, "HX-0006500-0A", "CABLE CLIP",                          "(2)",  None, None),
    (42, "400-86468",     "POWER CABLE 1P PLUG ASSY",             "1",    "#01", None),
    (43, "M9034-580-0A0", "GROUND CORD ASM.",                    "1",    "#01", None),
    (44, "400-86469",     "POWER CABLE 3P ASSY",                  "1",    "#02", None),
    (45, "400-86470",     "POWER CABLE 1P ASSY",                  "1",    "#03", None),
    (46, "400-65566",     "PANEL CABLE D ASM",                   "1",    None, None),
    (47, "400-35024",     "OPERATION_BOX_FIXED_PLATE(B)ASM",     "1",    None, None),
    (48, "SK-3413201-SE", "WOOD SCREW D=4.1 L=32",               "2",    None, None),
    (49, "CM-3001004-01", "LABEL 3 (LARGE)",                     "1",    "#02", None),
    (50, "403-11568",     "IP-510B PANEL ASSY",                  "1",    "#04", "＊"),
    (51, "402-95563",     "PANEL CABLE ASSY",                    "1",    "#04", "＊"),
]

def numeric_quantity(raw):
    n = float(raw.strip().strip("()"))
    return int(n) if n.is_integer() else n

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

if len(ROWS) != 51 or [r[0] for r in ROWS] != list(range(1, 52)):
    raise SystemExit("GAGAL: REF harus lengkap 1-51.")

if not Path("static", IMAGE).is_file():
    raise SystemExit("GAGAL: gambar halaman 40 tidak ditemukan.")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

machine = con.execute(
    "SELECT id, model FROM machines WHERE id=15"
).fetchone()

if not machine or machine["model"] != "AMS-210EN-1510":
    raise SystemExit("GAGAL: machine ID15 tidak sesuai.")

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
    raise SystemExit(
        f"GAGAL: komponen sudah ada: {[dict(x) for x in existing]}"
    )

print("=== PREFLIGHT SECTION 20 ===")
print("Machine:", dict(machine))
print("Dokumen:", dict(doc))
print("Judul:", TITLE)
print("REF katalog:", len(ROWS))
print("Gambar:", IMAGE, "| OK")

print("\n=== DAFTAR PART ===")
for ref, pn, name, raw, note, symbol in ROWS:
    marker = f"{symbol or ''} {note or ''}".strip() or "-"
    print(
        f"REF{ref:02} | {pn:16} | Qty {raw:5} "
        f"| NOTE {marker:5} | {name}"
    )

duplicates = {
    pn: [r[0] for r in ROWS if r[1] == pn]
    for pn in sorted(set(r[1] for r in ROWS))
    if sum(r[1] == pn for r in ROWS) > 1
}

print("\n=== PEMERIKSAAN ===")
print("REF berurutan:", [r[0] for r in ROWS] == list(range(1, 52)))
print("Nomor part kosong:", sum(not r[1] for r in ROWS))
print("Duplikasi nomor part:", duplicates)
print("Marker NOTE:", {
    marker: [r[0] for r in ROWS if r[4] == marker]
    for marker in ("#01", "#02", "#03", "#04")
})
print("Simbol ＊:", [r[0] for r in ROWS if r[5] == "＊"])

# Tampilkan kandidat lama, tetapi tidak menggunakannya kembali.
pns = sorted(set(r[1] for r in ROWS))
marks = ",".join("?" for _ in pns)
old = con.execute(f"""
    SELECT id, catalog_ref, part_number, part_name,
           quantity_raw, note, notes
    FROM parts
    WHERE machine_id=15 AND part_number IN ({marks})
    ORDER BY part_number, id
""", pns).fetchall()

print("\nPart lama dengan nomor part yang sama:", len(old))
for r in old:
    print(dict(r))

print("\nPart baru:", len(ROWS))
print("Relasi baru:", len(ROWS))
print("Data lama tidak digunakan ulang: ya")

if not args.apply:
    print("\nDRY-RUN: belum ada perubahan database.")
    con.close()
    raise SystemExit(0)

backup = Path(
    "database/garment-before-ams210en1510-section20-"
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
        "AMS-210EN-1510 Parts List; Section 20",
        IMAGE, SOURCE, "20", 35
    ))
    component_id = cur.lastrowid

    for ref, pn, name, raw, note, symbol in ROWS:
        part_notes = "AMS-210EN-1510 Parts List; Section 20"
        if symbol:
            part_notes += f"; {symbol} option"

        cur = con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number,
                part_name, quantity, catalog_ref, diagram_page,
                note, source_url, notes, quantity_raw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            15, 136, pn, name, numeric_quantity(raw),
            ref, 35, note, SOURCE, part_notes, raw
        ))

        con.execute("""
            INSERT INTO component_parts (
                component_id, part_id, relation_type, notes
            ) VALUES (?, ?, ?, ?)
        """, (
            component_id, cur.lastrowid,
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
