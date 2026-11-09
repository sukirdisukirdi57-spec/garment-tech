import sqlite3
import sys
import re
import shutil
from pathlib import Path
from collections import Counter
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section16/page35.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section16/page-34.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_xy_components_3_page34.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583
COMPONENT_NAME = "X-Y COMPONENTS (3)"

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

RAW_RECORDS = [
    (1,  None, "B2525-223-C00", "X DRIVE WHEEL",             "1"),
    (2,  None, "B2526-223-C00", "Y DRIVE WHEEL",             "1"),
    (3,  None, "SB-4120001-00",  "BEARING",                   "1"),
    (4,  None, "B2537-221-D00", "Y DRIVE WHEEL SPACER",      "3"),
    (5,  None, "400-72155",     "X MOTOR INSTALLING PLATE",  "1"),
    (6,  None, "SM-6051602-TP", "SCREW M5X0.8 L=16",         "4"),
    (7,  None, "SM-8060602-TP", "SCREW M6X6",               "2"),
    (8,  None, "SM-8060602-TP", "SCREW M6X6",               "2"),
    (9,  None, "SM-6051402-TP", "SCREW M5X0.8 L=14",         "8"),
    (10, None, "WP-0531000-SD", "WASHER M5",                "4"),
    (11, None, "401-04419",     "ENCODER MOTOR ASM.(X-Y)",  "2"),
    (12, None, "WP-0531000-SD", "WASHER M5",                "8"),
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


def snapshot(con):
    return [
        tuple(r) for r in con.execute("""
            SELECT c.id, c.component_name, c.diagram_page,
                   c.image_path, COUNT(cp.id)
            FROM components c
            LEFT JOIN component_parts cp ON cp.component_id=c.id
            WHERE c.machine_id=?
            GROUP BY c.id
            ORDER BY c.id
        """, (MACHINE_ID,))
    ]


if not DB.is_file() or not TXT.is_file() or not IMAGE_SRC.is_file():
    raise SystemExit(
        "GAGAL: database, page35.txt, atau diagram page-34.png tidak ditemukan"
    )

records = make_records()
refs = [r["ref"] for r in records]
number_counts = Counter(r["number"] for r in records)

expected_duplicates = {
    "SM-8060602-TP": 2,
    "WP-0531000-SD": 2,
}
actual_duplicates = {
    k: v for k, v in number_counts.items() if v > 1
}

print("=== VALIDASI SUMBER SECTION 16 ===")
print("Judul:", COMPONENT_NAME)
print("Jumlah REF:", len(records))
print("REF berurutan:", refs == list(range(1, 13)))
print("Nomor part unik:", len(number_counts))
print("Nomor part duplikat:", actual_duplicates)

if len(records) != 12 or refs != list(range(1, 13)):
    raise SystemExit("GAGAL: REF harus lengkap 1-12")

if len(number_counts) != 10:
    raise SystemExit("GAGAL: jumlah nomor part unik bukan 11")

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
    1:  ("B2525-223-C00", "X DRIVE WHEEL", "1"),
    2:  ("B2526-223-C00", "Y DRIVE WHEEL", "1"),
    3:  ("SB-4120001-00", "BEARING", "1"),
    4:  ("B2537-221-D00", "Y DRIVE WHEEL SPACER", "3"),
    5:  ("400-72155", "X MOTOR INSTALLING PLATE", "1"),
    6:  ("SM-6051602-TP", "SCREW M5X0.8 L=16", "4"),
    7:  ("SM-8060602-TP", "SCREW M6X6", "2"),
    8:  ("SM-8060602-TP", "SCREW M6X6", "2"),
    9:  ("SM-6051402-TP", "SCREW M5X0.8 L=14", "8"),
    10: ("WP-0531000-SD", "WASHER M5", "4"),
    11: ("401-04419", "ENCODER MOTOR ASM.(X-Y)", "2"),
    12: ("WP-0531000-SD", "WASHER M5", "8"),
}

for ref, expected in expected_values.items():
    r = records[ref - 1]
    actual = (r["number"], r["name"], r["qty_raw"])
    if actual != expected:
        raise SystemExit(
            f"GAGAL: data REF {ref}: {actual}, seharusnya {expected}"
        )

print("Data part dan quantity_raw: VALID")
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

    if counts != (678, 11, 678):
        stop(
            "Preflight gagal: kondisi database harus "
            "(678, 11, 678)"
        )

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
        print("Target parts     : 690")
        print("Target komponen  : 12")
        print("Target relasi    : 690")
        print("Jalankan dengan --apply untuk melakukan impor.")
        sys.exit(0)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    backup = Path(
        "database/garment-before-section16-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".db"
    )

    backup_con = sqlite3.connect(backup)
    try:
        con.backup(backup_con)
    finally:
        backup_con.close()

    print("\nBACKUP:", backup)

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
        None,
        None,
        "Official JUKI AMS-224EN-6030 parts catalog, Section 16.",
        SOURCE_URL,
        "16",
        34,
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
            f"REF {r['ref']}",
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
        SELECT COUNT(*)
        FROM component_parts
        WHERE component_id=?
    """, (component_id,)).fetchone()[0]

    linked_refs = [
        int(row["notes"].replace("REF ", ""))
        for row in con.execute("""
            SELECT notes
            FROM component_parts
            WHERE component_id=?
            ORDER BY CAST(REPLACE(notes, 'REF ', '') AS INTEGER)
        """, (component_id,))
    ]

    inserted = con.execute("""
        SELECT p.part_number, p.part_name, p.quantity_raw, p.note,
               cp.notes
        FROM component_parts cp
        JOIN parts p ON p.id=cp.part_id
        WHERE cp.component_id=?
        ORDER BY CAST(REPLACE(cp.notes, 'REF ', '') AS INTEGER)
    """, (component_id,)).fetchall()

    expected_inserted = [
        (r["number"], r["name"], r["qty_raw"], r["marker"],
         f"REF {r['ref']}")
        for r in records
    ]

    actual_inserted = [tuple(r) for r in inserted]

    if new_counts != (690, 12, 690):
        stop(f"Total database tidak sesuai: {new_counts}")

    if linked != 12:
        stop(f"Jumlah relasi Section 16 salah: {linked}")

    if linked_refs != list(range(1, 13)):
        stop("REF Section 16 tidak berurutan 1-12")

    if actual_inserted != expected_inserted:
        stop("Data part, quantity_raw, marker, atau REF tidak sesuai")

    if snapshot(con) != before + [
        (component_id, COMPONENT_NAME, 34, IMAGE_DB_PATH, 12)
    ]:
        stop("Snapshot komponen lama berubah atau data baru tidak sesuai")

    shutil.copy2(IMAGE_SRC, IMAGE_DST)

    image_info = con.execute("""
        SELECT image_path, diagram_page
        FROM components WHERE id=?
    """, (component_id,)).fetchone()

    if tuple(image_info) != (IMAGE_DB_PATH, 34):
        stop("Path diagram atau diagram_page tidak sesuai")

    print("\n=== PREFLIGHT FINAL ===")
    print("Total parts:", new_counts[0])
    print("Total komponen:", new_counts[1])
    print("Total relasi:", new_counts[2])
    print("Relasi Section 16:", linked)
    print("REF 1-12 valid:", linked_refs == list(range(1, 13)))
    print("Data part dan quantity_raw valid:", True)
    print("Duplikasi SM-8060602-TP tetap 2 occurrence:",
          actual_duplicates == expected_duplicates)
    print("Komponen lama tidak berubah:", True)
    print("Diagram DB:", tuple(image_info))

    con.commit()

    print("\n=== IMPOR SECTION 16 BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", COMPONENT_NAME)
    print("Diagram page :", 34)
    print("REF baru     :", linked)
    print("Part total   :", new_counts[0])
    print("Komponen     :", new_counts[1])
    print("Relasi total :", new_counts[2])

except Exception as exc:
    con.rollback()
    print("\n=== IMPOR DIBATALKAN ===")
    print("Alasan:", exc)
    raise

finally:
    con.close()
