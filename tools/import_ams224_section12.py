import re
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section12/page27.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section12/page-26.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_thread_trimmer_mechanism_page26.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "THREAD TRIMMER MECHANISM COMPONENTS"

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

# REF, MARKER, PART NUMBER, DESCRIPTION, QUANTITY RAW
RAW_RECORDS = [
    (1,  None,      "400-30936",       "THREAD_TRIMMER_CAM",               "1"),
    (2,  None,      "SM-8050592-TP",   "SCREW",                            "2"),
    (3,  None,      "SM-1040650-TP",   "SCREW",                            "4"),
    (4,  "#01",     "235-17501",       "NEEDLE CAM ROLLER A",              "1"),
    (5,  "#01",     "235-17600",       "NEEDLE CAM ROLLER B",              "1"),
    (6,  "#01",     "235-17709",       "NEEDLE CAM ROLLER C",              "1"),
    (7,  "#01",     "235-17808",       "NEEDLE CAM ROLLER D",              "1"),
    (8,  None,      "400-40256",       "ROLLER_SHAFT",                     "1"),
    (9,  None,      "NM-6040001-SP",   "NUT M4X0.7",                       "2"),
    (10, None,      "400-72228",       "THREAD_TRIMMER_LINK_ASM",          "1"),
    (11, None,      "SD-0800327-TP",   "SHOULDER SCREW",                   "1"),
    (12, None,      "NM-6050001-SP",   "NUT M5",                           "1"),
    (13, None,      "400-23624",       "THREAD_TRIMMER_SHAFT",             "1"),
    (14, None,      "SM-8060812-TP",   "SCREW M6 L=8",                     "2"),
    (15, None,      "400-72107",       "THREAD TRIMMER CONNECTING BAR",    "1"),
    (16, "#03",     "HN-0028400-00",   "CORES",                            "1"),
    (17, None,      "HD-0005700-0A",   "PHOTO SENSOR",                     "1"),
    (18, None,      "SL-4031091-SC",   "SCREW M3X10",                     "1"),
    (19, None,      "401-03968",       "ENCODER MOTOR ASM.(TC)",            "1"),
    (20, None,      "SM-6040650-TP",   "SCREW",                            "1"),
    (21, None,      "400-06666",       "SENSOR_SLIT_ASM",                  "1"),
    (22, None,      "SM-8050592-TP",   "SCREW",                            "2"),
    (23, "#02",     "400-30933",       "NEEDLE_PLATE_H_ASM.",              "1"),
    (24, None,      "SS-6110430-TP",   "SCREW 11/64-40 L=4.0",            "(1)"),
    (25, None,      "400-30934",       "NEEDLE_PLATE",                     "(1)"),
    (26, None,      "SS-7110740-TP",   "SCREW 11/64-40 L=7",              "(1)"),
    (27, "☆ #02",   "B2426-210-00B",   "NEEDLE HOLE GUIDE D=2.0",         "(1)"),
    (28, "☆",       "B2424-210-000",   "COUNTER KNIFE",                    "(1)"),
    (29, "☆",       "B2421-210-AA0",   "MOVING KNIFE COMPL.",              "(1)"),
    (30, None,      "B2418-280-000",   "MOVING KNIFE LINK",                "(1)"),
    (31, None,      "B2416-280-000",   "THREAD CUTTING LEVER RING",        "(1)"),
    (32, None,      "B2415-280-0A0",   "THREAD CUTTER LEVER ASM. SMALL",   "(1)"),
    (33, None,      "SS-7090410-SP",   "SCREW 9/64-40 L=3.5",             "(2)"),
    (34, None,      "B2414-280-0A0",   "THREAD CUTTER LEVER ASM. LARGE",   "(1)"),
    (35, "☆",       "SS-1060210-TP",   "SCREW 3/32-56 L=2.2",             "(2)"),
    (36, None,      "B2417-210-000",   "MOVING KNIFE HINGE SCREW",         "(1)"),
    (37, None,      "WP-0450846-SP",   "WASHER",                           "(1)"),
    (38, None,      "B2417-280-000",   "THREAD CUTTER LEVER SHAFT",        "(1)"),
    (39, "#01",     "B2423-280-00D",   "MOVING KNIFE WASHER D",            "(1)"),
    (40, "#01",     "B2423-280-00B",   "MOVING KNIFE WASHER B",            "(1)"),
    (41, "#01",     "B2423-280-00A",   "MOVING KNIFE WASHER A",            "(1)"),
    (42, "#01",     "B2423-280-00C",   "MOVING KNIFE WASHER C",            "(1)"),
    (43, None,      "HX-0015000-0C",   "CABLE CLIP",                       "1"),
    (44, None,      "SM-6040802-TP",   "SCREW M4X0.7 L=8",                "1"),
    (45, None,      "400-72211",       "MOTOR_BASE",                       "1"),
    (46, None,      "SM-6061802-TP",   "SCREW M6 L=18",                   "3"),
    (47, None,      "WP-0651001-SC",   "WASHER",                           "3"),
    (48, None,      "B1816-215-P00",   "GUIDE PIN",                        "2"),
    (49, None,      "400-10443",       "SENSOR_INSTALLING_BASE",           "1"),
    (50, None,      "SM-4051655-SP",   "SCREW M5 L=16",                    "4"),
    (51, None,      "SM-6040802-TP",   "SCREW M4X0.7 L=8",                "1"),
    (52, None,      "SB-1100024-00",   "BEARING",                          "1"),
]


def stop(message):
    raise RuntimeError(message)


def make_records():
    result = []
    for ref, marker, number, name, qty_raw in RAW_RECORDS:
        numeric = float(qty_raw.strip("()"))
        qty = int(numeric) if numeric.is_integer() else numeric
        result.append({
            "ref": ref,
            "marker": marker,
            "number": number,
            "name": name,
            "qty": qty,
            "qty_raw": qty_raw,
        })
    return result


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
        "GAGAL: database, page27.txt, atau diagram page-26.png tidak ditemukan"
    )


records = make_records()
refs = [r["ref"] for r in records]
number_counts = Counter(r["number"] for r in records)

expected_duplicates = {
    "SM-8050592-TP": 2,
    "SM-6040802-TP": 2,
}
actual_duplicates = {
    k: v for k, v in number_counts.items() if v > 1
}

print("=== VALIDASI SUMBER SECTION 12 ===")
print("Judul:", COMPONENT_NAME)
print("Jumlah REF:", len(records))
print("REF berurutan:", refs == list(range(1, 53)))
print("Nomor part unik:", len(number_counts))
print("Nomor part duplikat:", actual_duplicates)

if len(records) != 52 or refs != list(range(1, 53)):
    raise SystemExit("GAGAL: REF harus lengkap 1-52")

if len(number_counts) != 50:
    raise SystemExit("GAGAL: jumlah nomor part unik bukan 50")

if actual_duplicates != expected_duplicates:
    raise SystemExit("GAGAL: pola duplikasi part tidak sesuai")

source_text = TXT.read_text(errors="replace")

for number, count in number_counts.items():
    found = len(re.findall(re.escape(number), source_text))
    if found < count:
        raise SystemExit(
            f"GAGAL: nomor part {number} ditemukan {found} kali; "
            f"minimal {count} kali diperlukan"
        )

expected_values = {
    16: ("HN-0028400-00", "1", "#03"),
    24: ("SS-6110430-TP", "(1)", None),
    27: ("B2426-210-00B", "(1)", "☆ #02"),
    28: ("B2424-210-000", "(1)", "☆"),
    29: ("B2421-210-AA0", "(1)", "☆"),
    35: ("SS-1060210-TP", "(2)", "☆"),
    39: ("B2423-280-00D", "(1)", "#01"),
    42: ("B2423-280-00C", "(1)", "#01"),
    44: ("SM-6040802-TP", "1", None),
    51: ("SM-6040802-TP", "1", None),
}

for ref, expected in expected_values.items():
    r = records[ref - 1]
    actual = (r["number"], r["qty_raw"], r["marker"])
    if actual != expected:
        raise SystemExit(
            f"GAGAL: data khusus REF {ref}: {actual}, "
            f"seharusnya {expected}"
        )

print("Quantity dan marker khusus: VALID")
print("Sumber teks:", TXT)
print("Diagram:", IMAGE_SRC)


con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    if not con.execute(
        "SELECT id FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone():
        stop("Machine ID 47 tidak ditemukan")

    if not con.execute(
        "SELECT id FROM documents WHERE id=? AND machine_id=?",
        (DOCUMENT_ID, MACHINE_ID)
    ).fetchone():
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

    if counts != (584, 9, 584):
        stop("Preflight gagal: database bukan (584, 9, 584)")

    existing = con.execute("""
        SELECT id FROM components
        WHERE machine_id=? AND component_name=?
    """, (MACHINE_ID, COMPONENT_NAME)).fetchone()

    if existing:
        stop(f"Komponen sudah ada dengan ID {existing['id']}")

    before = snapshot(con)

    if "--apply" not in sys.argv:
        print("\n=== DRY RUN BERHASIL ===")
        print("Database belum diubah.")
        print("Target parts     : 636")
        print("Target komponen  : 10")
        print("Target relasi    : 636")
        print("Jalankan dengan --apply untuk melakukan impor.")
        sys.exit(0)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    backup = Path(
        "database/garment-before-section12-"
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
        "Official JUKI parts catalog. Diagram page 26, parts list page 27. Model 6030.",
        SOURCE_URL,
        None,
        26,
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

        con.execute("""
            INSERT INTO component_parts (
                component_id, part_id, relation_type, notes
            )
            VALUES (?, ?, ?, ?)
        """, (
            component_id,
            cur.lastrowid,
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
        (r["ref"], r["number"], r["name"], r["qty_raw"], r["marker"])
        for r in records
    ]

    old_unchanged = snapshot(con, exclude_id=component_id) == before

    image_db = con.execute("""
        SELECT image_path, diagram_page
        FROM components WHERE id=?
    """, (component_id,)).fetchone()

    marker_db = [
        tuple(r) for r in con.execute("""
            SELECT p.catalog_ref, p.note
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=? AND p.note IS NOT NULL
            ORDER BY p.catalog_ref
        """, (component_id,))
    ]

    expected_markers = [
        (r["ref"], r["marker"])
        for r in records if r["marker"] is not None
    ]

    print("\n=== PREFLIGHT FINAL ===")
    print("Total parts:", new_counts[0])
    print("Total komponen:", new_counts[1])
    print("Total relasi:", new_counts[2])
    print("Relasi Section 12:", linked)
    print("REF 1-52 valid:", refs_db == list(range(1, 53)))
    print("Data part dan quantity_raw valid:",
          records_db == expected_records_db)
    print("Marker valid:", marker_db == expected_markers)
    print("Komponen lama tidak berubah:", old_unchanged)
    print("Diagram DB:", tuple(image_db))

    if new_counts != (636, 10, 636):
        stop("Jumlah akhir database tidak sesuai")

    if linked != 52 or refs_db != list(range(1, 53)):
        stop("Verifikasi relasi Section 12 gagal")

    if records_db != expected_records_db:
        stop("Verifikasi data part Section 12 gagal")

    if marker_db != expected_markers:
        stop("Verifikasi marker Section 12 gagal")

    if not old_unchanged:
        stop("Data komponen lama berubah")

    if tuple(image_db) != (IMAGE_DB_PATH, 26):
        stop("Path diagram atau halaman diagram tidak sesuai")

    con.commit()

    print("\n=== IMPOR SECTION 12 BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", COMPONENT_NAME)
    print("Diagram page : 26")
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
