import re
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section10/page24.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section10/page-24.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_wiper_mechanism_page24.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "WIPER MECHANISM COMPONENTS"

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

# REF, NOTE, PART NO, DESCRIPTION, QTY RAW
RAW_RECORDS = [
    (1,  None, "400-86363",       "WIPER_ASM",                    "1"),
    (2,  None, "B2107-210-D00",   "WIPER",                        "(1)"),
    (3,  None, "SM-8040412-TP",   "SET SCREW M4 L=4",             "(1)"),
    (4,  None, "400-86364",       "WIPER_B_ASM",                  "(1)"),
    (5,  None, "400-86355",       "WIPER_BASE_ASM",               "(1)"),
    (6,  None, "400-30956",       "WIPER_SOLENOID",               "(1)"),
    (7,  None, "229-55900",       "WIPER RUBBER A",               "(1)"),
    (8,  None, "229-56007",       "WIPER RUBBER B",               "(1)"),
    (9,  None, "400-86350",       "WIPER_LINK_A",                 "(1)"),
    (10, None, "400-86353",       "WIPER_HINGE_SCREW_COLLAR",     "(1)"),
    (11, None, "400-86349",       "WIPER_SPRING",                 "(1)"),
    (12, None, "400-86357",       "WIPER_LINK_B",                 "(1)"),
    (13, None, "400-86358",       "WIPER_DRIVING_SHAFT_ASM",      "(1)"),
    (14, None, "229-56908",       "WIPER LINK B HINGE SCREW",     "(1)"),
    (15, None, "400-86352",       "WIPER_SOLENOID_SHAFT",         "(1)"),
    (16, None, "400-91894",       "SLIDE_BLOCK",                  "(1)"),
    (17, None, "HK-0346100-20",   "2-POLE NYLON PLUG",            "(1)"),
    (18, None, "HK-0346400-0B",   "PIN CONTACT",                  "(2)"),
    (19, None, "HA-0060000-00",   "SWITCH",                       "(1)"),
    (20, None, "HW-2003900-00",   "ELECTRIC WIRE",                "(0.04)"),
    (21, None, "HW-5000700-00",   "2-CORE CABTYRE CORD",          "(1.8)"),
    (22, None, "NS-6090310-SP",   "NUT 9/64-40",                  "(1)"),
    (23, None, "NM-6050001-SC",   "NUT M5",                       "(1)"),
    (24, None, "RC-0370411-KP",   "RETAINING RING",               "(1)"),
    (25, None, "RE-0500000-K0",   "E-RING",                       "(1)"),
    (26, None, "SM-8040412-TP",   "SET SCREW M4 L=4",             "(1)"),
    (27, None, "400-86354",       "WIPER_SHAFT_CAP",              "(1)"),
    (28, None, "400-86351",       "SHOULDER_SCREW",               "(1)"),
    (29, None, "SM-4030601-SN",   "SCREW M3X6",                   "(1)"),
    (30, None, "SL-4031091-SC",   "SCREW M3X10",                 "(3)"),
    (31, None, "WP-0320501-SC",   "WASHER M3",                    "(1)"),
    (32, None, "400-37500",       "RUBBER_HOLDER",                "(1)"),
    (33, None, "400-37501",       "STOPPER_RUBBER",               "(1)"),
    (34, None, "WP-0482086-SD",   "WASHER 4.8X11.5X2",            "(3)"),
    (35, None, "229-55504",       "WIPER COVER",                  "(1)"),
    (36, None, "400-25440",       "WIPER_STUD_TOP",               "1"),
    (37, None, "SM-4040855-SP",   "SCREW",                        "1"),
    (38, None, "SM-4050855-SP",   "SCREW",                        "1"),
    (39, None, "WP-0450801-SP",   "WASHER",                       "1"),
    (40, None, "WP-0531001-SC",   "WASHER",                       "1"),
    (41, "#01", "400-76294",      "WIPER_SHAFT_CAP",              "1"),
    (42, "#01", "B2107-210-D0B",  "WIPER",                        "1"),
]


def stop(message):
    raise RuntimeError(message)


def make_records():
    records = []

    for ref, marker, number, name, qty_raw in RAW_RECORDS:
        numeric = float(qty_raw.strip("()"))
        qty = int(numeric) if numeric.is_integer() else numeric

        records.append({
            "ref": ref,
            "marker": marker,
            "number": number,
            "name": name,
            "qty": qty,
            "qty_raw": qty_raw,
        })

    return records


def snapshot(con, exclude_id=None):
    sql = """
        SELECT c.id, c.component_name, c.diagram_page,
               c.image_path, COUNT(cp.id)
        FROM components c
        LEFT JOIN component_parts cp ON cp.component_id=c.id
        WHERE c.machine_id=?
    """
    params = [MACHINE_ID]

    if exclude_id is not None:
        sql += " AND c.id != ?"
        params.append(exclude_id)

    sql += " GROUP BY c.id ORDER BY c.id"
    return [tuple(r) for r in con.execute(sql, params)]


if not DB.is_file() or not TXT.is_file() or not IMAGE_SRC.is_file():
    raise SystemExit(
        "GAGAL: database, page24.txt, atau gambar page-24.png tidak ditemukan"
    )

records = make_records()
refs = [r["ref"] for r in records]
number_counts = Counter(r["number"] for r in records)

expected_duplicates = {
    "SM-8040412-TP": 2,
}

actual_duplicates = {
    k: v for k, v in number_counts.items() if v > 1
}

print("=== VALIDASI SUMBER SECTION 10 ===")
print("Judul:", COMPONENT_NAME)
print("Jumlah REF:", len(records))
print("REF berurutan:", refs == list(range(1, 43)))
print("Nomor part unik:", len(number_counts))
print("Nomor part duplikat:", actual_duplicates)

if len(records) != 42 or refs != list(range(1, 43)):
    raise SystemExit("GAGAL: REF harus lengkap 1-42")

if len(number_counts) != 41:
    raise SystemExit("GAGAL: jumlah nomor part unik tidak sesuai")

if actual_duplicates != expected_duplicates:
    raise SystemExit("GAGAL: pola duplikasi part tidak sesuai")

# Pastikan seluruh nomor part terdapat pada hasil ekstraksi PDF.
source_text = TXT.read_text(errors="replace")

for number, count in number_counts.items():
    found = len(re.findall(re.escape(number), source_text))
    if found < count:
        raise SystemExit(
            f"GAGAL: nomor part {number} hanya ditemukan {found} kali "
            f"di sumber, seharusnya minimal {count}"
        )

# Pemeriksaan nilai khusus agar data penting tidak berubah.
expected_values = {
    20: ("HW-2003900-00", "(0.04)"),
    21: ("HW-5000700-00", "(1.8)"),
    41: ("400-76294", "1"),
    42: ("B2107-210-D0B", "1"),
}

for ref, expected in expected_values.items():
    r = records[ref - 1]
    if (r["number"], r["qty_raw"]) != expected:
        raise SystemExit(f"GAGAL: data REF {ref} tidak sesuai")

if records[2]["number"] != records[25]["number"]:
    raise SystemExit("GAGAL: duplikasi REF 3 dan 26 tidak sesuai")

if records[40]["marker"] != "#01" or records[41]["marker"] != "#01":
    raise SystemExit("GAGAL: marker #01 REF 41-42 tidak sesuai")

print("Kuantitas dan marker: VALID")
print("Sumber teks:", TXT)
print("Diagram:", IMAGE_SRC)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    machine = con.execute(
        "SELECT id FROM machines WHERE id=?",
        (MACHINE_ID,)
    ).fetchone()

    if machine is None:
        stop("Machine ID 47 tidak ditemukan")

    doc = con.execute(
        "SELECT id FROM documents WHERE id=? AND machine_id=?",
        (DOCUMENT_ID, MACHINE_ID)
    ).fetchone()

    if doc is None:
        stop("Dokumen sumber ID 583 tidak ditemukan")

    counts = (
        con.execute(
            "SELECT COUNT(*) FROM parts WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],
        con.execute(
            "SELECT COUNT(*) FROM components WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],
        con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0],
    )

    print("\nKondisi database:", counts)

    if counts != (495, 7, 495):
        stop("Preflight gagal: kondisi database bukan (495, 7, 495)")

    existing = con.execute(
        """
        SELECT id FROM components
        WHERE machine_id=? AND component_name=?
        """,
        (MACHINE_ID, COMPONENT_NAME)
    ).fetchone()

    if existing:
        stop(
            f"Komponen sudah ada dengan ID {existing['id']}; "
            "impor dihentikan"
        )

    before = snapshot(con)

    if "--apply" not in sys.argv:
        print("\n=== DRY RUN BERHASIL ===")
        print("Database belum diubah.")
        print("Target akhir parts      : 537")
        print("Target akhir komponen   : 8")
        print("Target akhir relasi     : 537")
        print("Jalankan dengan --apply untuk melakukan impor.")
        sys.exit(0)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    backup = Path(
        "database/garment-before-section10-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".db"
    )

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()

    print("\nBACKUP:", backup)

    shutil.copy2(IMAGE_SRC, IMAGE_DST)
    print("Diagram disalin:", IMAGE_DST)

    con.execute("BEGIN IMMEDIATE")

    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, location, function,
            notes, source_url, catalog_ref, diagram_page, image_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        MACHINE_ID,
        COMPONENT_NAME,
        COMPONENT_NAME,
        COMPONENT_NAME,
        "Official JUKI parts catalog. Diagram page 24, parts list page 24. Model 6030.",
        SOURCE_URL,
        None,
        24,
        IMAGE_DB_PATH,
    ))

    component_id = cur.lastrowid

    for r in records:
        cur = con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number, part_name,
                quantity, catalog_ref, diagram_page, note,
                source_url, notes, quantity_raw
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
        """, (
            MACHINE_ID,
            DOCUMENT_ID,
            r["number"],
            r["name"],
            r["qty"],
            r["ref"],
            r["marker"],
            SOURCE_URL,
            f"AMS-224EN-6030 section: {COMPONENT_NAME}",
            r["qty_raw"],
        ))

        part_id = cur.lastrowid

        con.execute("""
            INSERT INTO component_parts (
                component_id, part_id, relation_type, notes
            )
            VALUES (?, ?, ?, ?)
        """, (
            component_id,
            part_id,
            "catalog_component_part",
            f"Catalog REF {r['ref']:02d}",
        ))

    new_counts = (
        con.execute(
            "SELECT COUNT(*) FROM parts WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],
        con.execute(
            "SELECT COUNT(*) FROM components WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],
        con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0],
    )

    linked = con.execute("""
        SELECT COUNT(*) FROM component_parts
        WHERE component_id=?
    """, (component_id,)).fetchone()[0]

    refs_db = [
        r[0] for r in con.execute("""
            SELECT p.catalog_ref
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY p.catalog_ref
        """, (component_id,))
    ]

    old_unchanged = (
        snapshot(con, exclude_id=component_id) == before
    )

    image_db = con.execute(
        "SELECT image_path, diagram_page FROM components WHERE id=?",
        (component_id,)
    ).fetchone()

    marker_db = [
        tuple(r) for r in con.execute("""
            SELECT p.catalog_ref, p.note
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
              AND p.catalog_ref IN (41, 42)
            ORDER BY p.catalog_ref
        """, (component_id,))
    ]

    print("\n=== PREFLIGHT FINAL ===")
    print("Total parts:", new_counts[0])
    print("Total komponen:", new_counts[1])
    print("Total relasi:", new_counts[2])
    print("Relasi Section 10:", linked)
    print("REF 1-42 valid:", refs_db == list(range(1, 43)))
    print("Komponen lama tidak berubah:", old_unchanged)
    print("Diagram DB:", tuple(image_db))
    print("Marker REF 41-42:", marker_db)

    if new_counts != (537, 8, 537):
        stop("Jumlah akhir database tidak sesuai")

    if linked != 42 or refs_db != list(range(1, 43)):
        stop("Verifikasi relasi Section 10 gagal")

    if not old_unchanged:
        stop("Data komponen lama berubah")

    if tuple(image_db) != (IMAGE_DB_PATH, 24):
        stop("Path diagram atau halaman diagram tidak sesuai")

    if marker_db != [(41, "#01"), (42, "#01")]:
        stop("Penyimpanan marker REF 41-42 gagal")

    con.commit()

    print("\n=== IMPOR SECTION 10 BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", COMPONENT_NAME)
    print("Diagram page : 24")
    print("REF baru     :", linked)
    print("Part total   :", new_counts[0])
    print("Komponen     :", new_counts[1])
    print("Relasi total :", new_counts[2])

except Exception as e:
    if con.in_transaction:
        con.rollback()
    print("\nGAGAL — TRANSAKSI DIBATALKAN:", e)
    raise

finally:
    con.close()
