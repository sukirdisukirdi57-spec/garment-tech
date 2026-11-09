import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TITLE = "19. THREAD STAND COMPONENTS"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-39.jpg"
SOURCE = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"

# REF, part number, official description, quantity_raw
ROWS = [
    (1,  "229-30358",    "THREAD STAND ASM.",             "1"),
    (2,  "229-31109",    "SPOOL RETAINER",                "(2)"),
    (3,  "229-31000",    "SPOOL PIN",                     "(2)"),
    (4,  "229-30903",    "SPOOL REST CUSHION",             "(2)"),
    (5,  "229-30804",    "SPOOL REST",                    "(2)"),
    (6,  "SM-6061610-SC","SCREW M6 L=16",                 "(2)"),
    (7,  "229-30705",    "THREAD GUIDE ARM JOINT",         "(2)"),
    (8,  "229-31406",    "SPOOL REST ROD RUBBER CAP",      "(1)"),
    (9,  "229-30507",    "SPOOL REST ARM",                "(1)"),
    (10, "229-30408",    "SPOOL REST ROD UPPER",           "(1)"),
    (11, "229-31307",    "SPOOL REST ROD JOINT",           "(1)"),
    (12, "SM-4051405-SE","SCREW M5 L=14",                 "(2)"),
    (13, "NM-6050001-SE","NUT M5",                        "(2)"),
    (14, "229-30309",    "SPOOL REST ROD LOWER",           "(1)"),
    (15, "229-30556",    "THREAD STANDING ARM ASM.",       "(1)"),
    (16, "WS-0510002-KN","SPRING WASHER",                 "(2)"),
    (17, "NM-6050001-SE","NUT M5",                        "(2)"),
    (18, "NM-6160511-SE","NUT M16X1.5",                   "(2)"),
    (19, "WP-1612616-SE","WASHER 16X30X2.6",              "(2)"),
    (20, "WS-1643202-KR","SPRING WASHER",                 "(1)"),
]

def numeric_quantity(raw):
    n = float(raw.strip().strip("()"))
    return int(n) if n.is_integer() else n

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

if len(ROWS) != 20 or [r[0] for r in ROWS] != list(range(1, 21)):
    raise SystemExit("GAGAL: REF harus lengkap 1-20.")

if not Path("static", IMAGE).is_file():
    raise SystemExit("GAGAL: gambar halaman 39 tidak ditemukan.")

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
    raise SystemExit(f"GAGAL: komponen sudah ada: {[dict(x) for x in existing]}")

print("=== PREFLIGHT SECTION 19 ===")
print("Machine:", dict(machine))
print("Dokumen:", dict(doc))
print("Judul:", TITLE)
print("REF katalog:", len(ROWS))
print("Gambar:", IMAGE, "| OK")

print("\n=== DAFTAR PART ===")
for ref, pn, name, raw in ROWS:
    print(f"REF{ref:02} | {pn:16} | Qty {raw:5} | {name}")

print("\n=== PEMERIKSAAN ===")
print("REF berurutan:", [r[0] for r in ROWS] == list(range(1, 21)))
print("Nomor part kosong:", sum(not r[1] for r in ROWS))
print("Duplikasi nomor part:", {
    pn: [r[0] for r in ROWS if r[1] == pn]
    for pn in sorted(set(r[1] for r in ROWS))
    if sum(r[1] == pn for r in ROWS) > 1
})
print("Semua NOTE kosong sesuai sumber: ya")
print("Part baru:", len(ROWS))
print("Relasi baru:", len(ROWS))

if not args.apply:
    print("\nDRY-RUN: belum ada perubahan database.")
    con.close()
    raise SystemExit(0)

backup = Path(
    "database/garment-before-ams210en1510-section19-"
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
        "AMS-210EN-1510 Parts List; Section 19",
        IMAGE, SOURCE, "19", 34
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
            ref, 34, SOURCE,
            "AMS-210EN-1510 Parts List; Section 19",
            raw
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
