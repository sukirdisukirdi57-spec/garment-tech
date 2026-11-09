import re
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section11/page25.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section11/page-25.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_tension_release_thread_tension_page25.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "TENSION RELEASE & THREAD TENSION COMPONENTS"

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

# REF, NOTE, PART NO, DESCRIPTION, QTY RAW
RAW_RECORDS = [
    (1,  None,       "400-73660",       "AT SOLENOID",                    "1"),
    (2,  None,       "SM-6040802-TP",   "SCREW M4X0.7 L=8",               "4"),
    (3,  None,       "RE-0900000-K0",   "E-RING 9",                       "1"),
    (4,  None,       "400-06625",       "SPRING",                         "1"),
    (5,  None,       "400-06617",       "AT_SOL_PIN",                     "1"),
    (6,  None,       "400-10477",       "AT_SOL_COLLAR",                  "1"),
    (7,  None,       "SM-8030412-TP",   "SCREW",                          "2"),
    (8,  None,       "400-10479",       "AT_PLATE",                       "1"),
    (9,  None,       "SM-6040802-TP",   "SCREW M4X0.7 L=8",               "2"),
    (10, None,       "WP-0430801-SC",   "WASHER 4.3X9X0.8",              "2"),
    (11, None,       "400-32343",       "AT_DRIVE_LINK_F_ASM",            "1"),
    (12, None,       "400-23993",       "AT_PIVOT_BASE(F)",               "1"),
    (13, None,       "SM-6040860-TP",   "SCREW M4 L=8",                  "2"),
    (14, None,       "400-32345",       "AT_DRIVE_LINK_R_ASM",            "1"),
    (15, None,       "400-23999",       "AT_PIVOT_BASE(R)",               "1"),
    (16, None,       "SM-6040802-TP",   "SCREW M4X0.7 L=8",               "2"),
    (17, None,       "400-10487",       "AT_PIVOT_SCREW",                 "2"),
    (18, None,       "NM-6040003-SC",   "NUT M4",                         "2"),
    (19, None,       "400-10489",       "AT_PIVOT_SCREW_WASHER",          "4"),
    (20, None,       "400-10490",       "AT_PIVOT_BEARING",               "2"),
    (21, None,       "400-10497",       "AT_JOINT",                       "2"),
    (22, None,       "400-10498",       "AT_JOINT_BEARING",               "2"),
    (23, None,       "400-10489",       "AT_PIVOT_SCREW_WASHER",          "2"),
    (24, None,       "400-10499",       "AT_JOINT_NUT",                   "2"),
    (25, None,       "400-06622",       "AT_SNAP_PIN",                    "2"),
    (26, None,       "400-72111",       "AT CONNECTION BAR",              "1"),
    (27, None,       "400-10503",       "THREAD_TENSION_1_ASM.",          "1"),
    (28, None,       "229-28808",       "NUT",                            "(1)"),
    (29, None,       "229-21506",       "THREAD TENSION DISK",            "(2)"),
    (30, None,       "400-10504",       "THREAD_TENSION_SHAFT",           "(1)"),
    (31, None,       "262-18602",       "FIRST THREAD TENSION SPRING",    "(1)"),
    (32, "#01",      "400-29411",       "THREAD_TENSION_2_ASM._H",        "1"),
    (33, None,       "400-10523",       "POST_BASE_C_RING",               "(1)"),
    (34, None,       "400-10509",       "TENSION RELEASE PIN",            "(1)"),
    (35, None,       "400-10510",       "THREAD_TENSION_POST_BASE",       "(1)"),
    (36, None,       "400-10511",       "DISK_STOPPER_HOLDER_CAP",        "(1)"),
    (37, None,       "400-10512",       "THREAD_TENSION_SHAFT_COLLAR",    "(1)"),
    (38, None,       "400-10513",       "DISK_STOPPER_SPRING",            "(3)"),
    (39, None,       "400-10514",       "DISK_STOPPER",                   "(1)"),
    (40, None,       "400-10515",       "ASSY_THREAD_TENSION_POST",       "(1)"),
    (41, None,       "400-10478",       "AT_SOL_COLLAR_SCREW",            "(1)"),
    (42, "☆ #01",    "400-29412",       "THREAD_TAKE-UP_SPRING_H",        "(1)"),
    (43, None,       "400-10521",       "HOLD_CAP_SCREW",                 "(3)"),
    (44, None,       "400-10522",       "SHAFT_NUT",                      "(1)"),
    (45, None,       "WP-0510516-SD",   "WASHER 5.1X7.5X0.5",            "2"),
    (46, None,       "B1228-232-000",   "OIL FELT",                       "2"),
    (47, None,       "SM-8061612-TP",   "SCREW M6X16",                    "1"),
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
        "GAGAL: database, page25.txt, atau page-25.png tidak ditemukan"
    )


records = make_records()
refs = [r["ref"] for r in records]
number_counts = Counter(r["number"] for r in records)

expected_duplicates = {
    "SM-6040802-TP": 3,
    "400-10489": 2,
}

actual_duplicates = {
    k: v for k, v in number_counts.items() if v > 1
}

print("=== VALIDASI SUMBER SECTION 11 ===")
print("Judul:", COMPONENT_NAME)
print("Jumlah REF:", len(records))
print("REF berurutan:", refs == list(range(1, 48)))
print("Nomor part unik:", len(number_counts))
print("Nomor part duplikat:", actual_duplicates)

if len(records) != 47 or refs != list(range(1, 48)):
    raise SystemExit("GAGAL: REF harus lengkap 1-47")

if len(number_counts) != 44:
    raise SystemExit("GAGAL: jumlah nomor part unik tidak sesuai")

if actual_duplicates != expected_duplicates:
    raise SystemExit("GAGAL: pola duplikasi part tidak sesuai")


# Pastikan nomor part ditemukan pada hasil ekstraksi PDF.
source_text = TXT.read_text(errors="replace")

for number, count in number_counts.items():
    found = len(re.findall(re.escape(number), source_text))

    if found < count:
        raise SystemExit(
            f"GAGAL: nomor part {number} hanya ditemukan {found} kali "
            f"di sumber, seharusnya minimal {count}"
        )


# Pemeriksaan data khusus.
expected_values = {
    28: ("229-28808", "(1)"),
    29: ("229-21506", "(2)"),
    32: ("400-29411", "1"),
    38: ("400-10513", "(3)"),
    42: ("400-29412", "(1)"),
    45: ("WP-0510516-SD", "2"),
}

for ref, expected in expected_values.items():
    r = records[ref - 1]

    if (r["number"], r["qty_raw"]) != expected:
        raise SystemExit(
            f"GAGAL: data REF {ref} tidak sesuai"
        )

if records[31]["marker"] != "#01":
    raise SystemExit("GAGAL: marker REF 32 tidak sesuai")

if records[41]["marker"] != "☆ #01":
    raise SystemExit("GAGAL: marker REF 42 tidak sesuai")

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

    if counts != (537, 8, 537):
        stop(
            "Preflight gagal: kondisi database bukan (537, 8, 537)"
        )

    existing = con.execute("""
        SELECT id FROM components
        WHERE machine_id=? AND component_name=?
    """, (MACHINE_ID, COMPONENT_NAME)).fetchone()

    if existing:
        stop(
            f"Komponen sudah ada dengan ID {existing['id']}; "
            "impor dihentikan"
        )

    before = snapshot(con)

    if "--apply" not in sys.argv:
        print("\n=== DRY RUN BERHASIL ===")
        print("Database belum diubah.")
        print("Target akhir parts      : 584")
        print("Target akhir komponen   : 9")
        print("Target akhir relasi     : 584")
        print("Jalankan dengan --apply untuk melakukan impor.")
        sys.exit(0)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    backup = Path(
        "database/garment-before-section11-"
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
        "Official JUKI parts catalog. Diagram page 25, parts list page 25. Model 6030.",
        SOURCE_URL,
        None,
        25,
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

    image_db = con.execute("""
        SELECT image_path, diagram_page
        FROM components
        WHERE id=?
    """, (component_id,)).fetchone()

    marker_db = [
        tuple(r) for r in con.execute("""
            SELECT p.catalog_ref, p.note
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
              AND p.catalog_ref IN (32, 42)
            ORDER BY p.catalog_ref
        """, (component_id,))
    ]

    records_db = [
        tuple(r) for r in con.execute("""
            SELECT p.catalog_ref, p.part_number, p.part_name,
                   p.quantity_raw, p.note
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY p.catalog_ref
        """, (component_id,))
    ]

    expected_records_db = [
        (
            r["ref"],
            r["number"],
            r["name"],
            r["qty_raw"],
            r["marker"],
        )
        for r in records
    ]

    print("\n=== PREFLIGHT FINAL ===")
    print("Total parts:", new_counts[0])
    print("Total komponen:", new_counts[1])
    print("Total relasi:", new_counts[2])
    print("Relasi Section 11:", linked)
    print("REF 1-47 valid:", refs_db == list(range(1, 48)))
    print("Data part dan quantity_raw valid:",
          records_db == expected_records_db)
    print("Komponen lama tidak berubah:", old_unchanged)
    print("Diagram DB:", tuple(image_db))
    print("Marker REF 32 dan 42:", marker_db)

    if new_counts != (584, 9, 584):
        stop("Jumlah akhir database tidak sesuai")

    if linked != 47 or refs_db != list(range(1, 48)):
        stop("Verifikasi relasi Section 11 gagal")

    if records_db != expected_records_db:
        stop("Verifikasi data part Section 11 gagal")

    if not old_unchanged:
        stop("Data komponen lama berubah")

    if tuple(image_db) != (IMAGE_DB_PATH, 25):
        stop("Path diagram atau halaman diagram tidak sesuai")

    if marker_db != [(32, "#01"), (42, "☆ #01")]:
        stop("Penyimpanan marker REF 32 dan 42 gagal")

    con.commit()

    print("\n=== IMPOR SECTION 11 BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", COMPONENT_NAME)
    print("Diagram page : 25")
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
