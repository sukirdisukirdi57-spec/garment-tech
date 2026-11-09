import sqlite3
import sys
import re
import shutil
from pathlib import Path
from collections import Counter
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section17/page37.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section17/page-36.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_cloth_feed_mechanism_page36.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583
COMPONENT_NAME = "CLOTH FEED MECHANISM COMPONENTS"
DIAGRAM_PAGE = 36

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (690, 12, 690)
TARGET = (749, 13, 749)

EXCLUDED_REFS = [28, 46, 52]
EXPECTED_REFS = [n for n in range(1, 63) if n not in EXCLUDED_REFS]
EXPECTED_SPECIAL_REFS = [51, 53, 56, 61]

EXPECTED_DUPLICATES = {
    "SM-8050812-TP": 2,
    "WP-0531000-SD": 3,
    "WP-0641600-SC": 2,
}

PATTERN = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"(?:(#0[12])\s+)?"
    r"([A-Z0-9-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)


def stop(message):
    raise RuntimeError(message)


def parse_source():
    text = TXT.read_text(errors="replace")
    result = []

    for line in text.splitlines():
        match = PATTERN.match(line)
        if not match:
            continue

        ref, marker, number, name, qty_raw = match.groups()

        result.append({
            "ref": int(ref),
            "marker": marker,
            "number": number,
            "name": name.strip(),
            "qty_raw": qty_raw,
        })

    return result, text


def make_records(source_records):
    result = []

    for r in source_records:
        if r["marker"] == "#01":
            continue

        numeric = float(r["qty_raw"].strip("()"))
        qty = int(numeric) if numeric.is_integer() else numeric

        result.append({
            **r,
            "qty": qty,
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


def get_counts(con):
    return (
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


if not DB.is_file():
    raise SystemExit("GAGAL: database tidak ditemukan")

if not TXT.is_file():
    raise SystemExit("GAGAL: teks halaman 37 tidak ditemukan")

if not IMAGE_SRC.is_file():
    raise SystemExit("GAGAL: diagram halaman 36 tidak ditemukan")

if IMAGE_DST.exists():
    raise SystemExit(
        f"GAGAL: file diagram tujuan sudah ada: {IMAGE_DST}"
    )

source_records, source_text = parse_source()

source_refs = [r["ref"] for r in source_records]
excluded = [
    r["ref"] for r in source_records
    if r["marker"] == "#01"
]
special = [
    r["ref"] for r in source_records
    if r["marker"] == "#02"
]

if len(source_records) != 62:
    raise SystemExit(
        f"GAGAL: jumlah REF sumber {len(source_records)}, seharusnya 62"
    )

if source_refs != list(range(1, 63)):
    raise SystemExit("GAGAL: REF sumber tidak lengkap 1-62")

if excluded != EXCLUDED_REFS:
    raise SystemExit(f"GAGAL: REF #01 tidak sesuai: {excluded}")

if special != EXPECTED_SPECIAL_REFS:
    raise SystemExit(f"GAGAL: REF #02 tidak sesuai: {special}")

records = make_records(source_records)
refs = [r["ref"] for r in records]

number_counts = Counter(r["number"] for r in records)
actual_duplicates = {
    k: v for k, v in number_counts.items() if v > 1
}

print("=== VALIDASI SUMBER SECTION 17 ===")
print("Judul:", COMPONENT_NAME)
print("Jumlah REF sumber:", len(source_records))
print("REF sumber lengkap:", source_refs == list(range(1, 63)))
print("REF #01 dikecualikan:", excluded)
print("REF #02 dipertahankan:", special)
print("Jumlah occurrence 6030:", len(records))
print("REF terpilih valid:", refs == EXPECTED_REFS)
print("Nomor part unik:", len(number_counts))
print("Nomor part duplikat:", actual_duplicates)

if len(records) != 59 or refs != EXPECTED_REFS:
    raise SystemExit("GAGAL: daftar occurrence 6030 tidak sesuai")

if len(number_counts) != 55:
    raise SystemExit("GAGAL: jumlah part unik bukan 55")

if actual_duplicates != EXPECTED_DUPLICATES:
    raise SystemExit("GAGAL: pola duplikasi part tidak sesuai")

for r in records:
    if r["number"] not in source_text:
        raise SystemExit(
            f"GAGAL: nomor part REF {r['ref']} tidak ditemukan di sumber"
        )

    if r["qty_raw"] == "":
        raise SystemExit(f"GAGAL: quantity kosong pada REF {r['ref']}")

expected_values = {
    1:  ("400-72135", "CLOTH FEED BASE", "1", None),
    2:  ("400-23644", "CYLINDER KNUCKLE", "2", None),
    3:  ("B1504-210-000", "CONNECTING SHAFT", "2", None),
    4:  ("260-23408", "FEED STUD", "2", None),
    5:  ("400-23635", "CYLINDER PIN", "2", None),
    6:  ("PA-1602509-A0", "AIR CYLINDER", "2", None),
    7:  ("PJ-0460525-03", "HOSE ELBOW", "4", None),
    8:  ("B4711-220-00C", "AIR TUBE LABEL J03 LEFT", "1", None),
    9:  ("B4711-220-00D", "AIR TUBE LABEL J04 LEFT", "1", None),
    10: ("B4711-220-00G", "AIR TUBE LABEL J03 RIGHT", "1", None),
    11: ("B4711-220-00H", "AIR TUBE LABEL J04 RIGHT", "1", None),
    12: ("RE-0300000-K0", "E-RING 3", "4", None),
    13: ("400-32229", "LIFTING_LEVER_A", "2", None),
    14: ("400-85820", "LIFTING_LEVER_B", "2", None),
    15: ("SM-8050812-TP", "SCREW M5X8", "2", None),
    16: ("SM-6051000-SP", "SCREW", "2", None),
    17: ("WP-0531000-SD", "WASHER M5", "2", None),
    18: ("BT-0400251-EB", "URETHANE HOSE BLACK", "4", None),
    19: ("HX-0023300-00", "CLIP", "10", None),
    20: ("B2568-223-C00", "AIR TUBE SUPPORT", "1", None),
    21: ("SL-6062592-TN", "SCREW", "4", None),
    22: ("SM-8050812-TP", "SCREW M5X8", "2", None),
    23: ("SM-6051002-TP", "SCREW M5X0.8 L=10", "4", None),
    24: ("WP-0531000-SD", "WASHER M5", "4", None),
    25: ("RE-0320000-K0", "E-RING 3.2", "2", None),
    26: ("PC-0124010-00", "SPEED CONTROLLER", "2", None),
    27: ("B2568-224-C00", "AIR TUBE SUPPORT A", "1", None),
    29: ("SM-6060802-TP", "SCREW M6 L=8", "2", None),
    30: ("B2567-223-CA0", "WORK CLAMP FOOT PLATE B ASM.", "4", None),
    31: ("B2567-223-C00", "WORK CLAMP FOOT PLATE B", "(4)", None),
    32: ("PS-0150065-KP", "SPRING PIN 1.5X6", "(8)", None),
    33: ("400-85830", "SLIDE_PLATE_ASM.", "2", None),
    34: ("400-85824", "SLIDE_PLATE", "(2)", None),
    35: ("B1816-280-000", "GUIDE PIN", "(4)", None),
    36: ("B2569-229-000", "SLIDING PLATE BEARING", "4", None),
    37: ("SM-6051802-TP", "SCREW M5 L=18", "12", None),
    38: ("WS-0610002-KP", "SPRING WASHER", "2", None),
    39: ("WP-0611626-SP", "WASHER 15X6X1.6", "2", None),
    40: ("400-72163", "FEEDING_FRAME_ARM_B", "2", None),
    41: ("SM-6061602-TP", "SCREW M6 L=16", "4", None),
    42: ("WP-0641600-SC", "WASHEW 6.4X12.5X1.6", "4", None),
    43: ("400-51770", "FEEDING FRAME BALL CATCH", "2", None),
    44: ("SM-4041255-SP", "SCREW M4 L=12", "4", None),
    45: ("WP-0430800-SD", "WASHER M4", "4", None),
    47: ("B2560-220-000", "SUPPORT PIN", "2", None),
    48: ("SM-8050412-TP", "SCREW M5 L=4", "2", None),
    49: ("400-51769", "FEEDING FRAME SUPPORT BEARING", "2", None),
    50: ("SM-1040870-TP", "SCREW", "4", None),
    51: ("400-72137", "LOWER PLATE 6030", "1", "#02"),
    53: ("400-72162", "FEEDING_FRAME_ARM_A_6030", "1", "#02"),
    54: ("SM-6062502-TN", "HEXAGONAL-HOLE BOLT", "8", None),
    55: ("WP-0641600-SC", "WASHEW 6.4X12.5X1.6", "8", None),
    56: ("400-72139", "FEEDING FRAME 6030", "1", "#02"),
    57: ("B2563-215-000", "FEEDING FRAME HOLDING PLATE", "2", None),
    58: ("SM-6050800-SP", "SCREW M5 L=8", "4", None),
    59: ("WP-0531000-SD", "WASHER M5", "4", None),
    60: ("HX-0036400-0E", "PARTS", "1.2", None),
    61: ("CM-3002000-03", "ATTENTION LABEL", "1", "#02"),
    62: ("CM-3002000-01", "ATTENTION SEAL", "1", None),
}

for r in records:
    expected = expected_values.get(r["ref"])
    actual = (
        r["number"], r["name"], r["qty_raw"], r["marker"]
    )

    if actual != expected:
        raise SystemExit(
            f"GAGAL: data REF {r['ref']} tidak sesuai.\n"
            f"Aktual: {actual}\n"
            f"Harus : {expected}"
        )

if set(expected_values) != set(refs):
    raise SystemExit("GAGAL: daftar validasi REF tidak sama dengan sumber")

print("Nama part, nomor part, marker, dan quantity_raw: VALID")
print("Quantity khusus REF 60:", records[refs.index(60)]["qty_raw"])
print("Sumber teks:", TXT)
print("Diagram:", IMAGE_SRC)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=?",
        (MACHINE_ID,)
    ).fetchone()

    if not machine or machine["model"] != "AMS-224EN-6030":
        stop("Machine ID 47 tidak cocok dengan AMS-224EN-6030")

    document = con.execute(
        "SELECT id FROM documents WHERE id=? AND machine_id=?",
        (DOCUMENT_ID, MACHINE_ID)
    ).fetchone()

    if not document:
        stop("Dokumen sumber ID 583 tidak ditemukan")

    counts = get_counts(con)
    print("\nKondisi database:", counts)

    if counts != BASELINE:
        stop(
            f"Preflight gagal: baseline harus {BASELINE}, "
            f"aktual {counts}"
        )

    existing = con.execute("""
        SELECT id FROM components
        WHERE machine_id=? AND component_name=?
    """, (MACHINE_ID, COMPONENT_NAME)).fetchone()

    if existing:
        stop(
            f"Komponen sudah ada dengan ID {existing['id']}"
        )

    before = snapshot(con)

    if len(before) != 12:
        stop("Jumlah komponen lama bukan 12")

    if "--apply" not in sys.argv:
        print("\n=== DRY RUN BERHASIL ===")
        print("Database belum diubah.")
        print("Target parts     :", TARGET[0])
        print("Target komponen  :", TARGET[1])
        print("Target relasi    :", TARGET[2])
        print("REF baru         :", len(records))
        print("Diagram page     :", DIAGRAM_PAGE)
        print("Jalankan dengan --apply untuk melakukan impor.")
        sys.exit(0)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    backup = Path(
        "database/garment-before-section17-"
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
        "Official JUKI AMS-224EN-6030 parts catalog, Section 17.",
        SOURCE_URL,
        "17",
        DIAGRAM_PAGE,
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

    new_counts = get_counts(con)

    inserted = con.execute("""
        SELECT p.part_number, p.part_name, p.quantity_raw,
               p.note, cp.notes
        FROM component_parts cp
        JOIN parts p ON p.id=cp.part_id
        WHERE cp.component_id=?
        ORDER BY CAST(REPLACE(cp.notes, 'REF ', '') AS INTEGER)
    """, (component_id,)).fetchall()

    expected_inserted = [
        (
            r["number"], r["name"], r["qty_raw"],
            r["marker"], f"REF {r['ref']}"
        )
        for r in records
    ]

    actual_inserted = [tuple(r) for r in inserted]

    linked_refs = [
        int(row["notes"].replace("REF ", ""))
        for row in con.execute("""
            SELECT notes
            FROM component_parts
            WHERE component_id=?
            ORDER BY CAST(REPLACE(notes, 'REF ', '') AS INTEGER)
        """, (component_id,))
    ]

    if new_counts != TARGET:
        stop(f"Total database tidak sesuai: {new_counts}")

    if linked_refs != EXPECTED_REFS:
        stop("Daftar REF relasi tidak sesuai")

    if actual_inserted != expected_inserted:
        stop("Data part, quantity_raw, marker, atau REF tidak sesuai")

    if snapshot(con) != before + [
        (
            component_id,
            COMPONENT_NAME,
            DIAGRAM_PAGE,
            IMAGE_DB_PATH,
            59,
        )
    ]:
        stop("Snapshot komponen lama berubah atau data baru tidak sesuai")

    shutil.copy2(IMAGE_SRC, IMAGE_DST)

    image_info = con.execute("""
        SELECT image_path, diagram_page
        FROM components WHERE id=?
    """, (component_id,)).fetchone()

    if tuple(image_info) != (IMAGE_DB_PATH, DIAGRAM_PAGE):
        stop("Path diagram atau diagram_page tidak sesuai")

    print("\n=== PREFLIGHT FINAL ===")
    print("Total parts:", new_counts[0])
    print("Total komponen:", new_counts[1])
    print("Total relasi:", new_counts[2])
    print("Relasi Section 17:", len(linked_refs))
    print("REF valid:", linked_refs == EXPECTED_REFS)
    print("Data part dan quantity_raw valid:", True)
    print("Marker #02 tersimpan:", True)
    print("Duplikasi part tetap terpisah:", actual_duplicates)
    print("Komponen lama tidak berubah:", True)
    print("Diagram DB:", tuple(image_info))

    con.commit()

    print("\n=== IMPOR SECTION 17 BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", COMPONENT_NAME)
    print("Diagram page :", DIAGRAM_PAGE)
    print("REF baru     :", len(linked_refs))
    print("Part total   :", new_counts[0])
    print("Komponen     :", new_counts[1])
    print("Relasi total :", new_counts[2])
    print("Backup       :", backup)

except Exception as exc:
    con.rollback()

    if IMAGE_DST.exists():
        IMAGE_DST.unlink()

    print("\n=== IMPOR DIBATALKAN ===")
    print("Alasan:", exc)
    raise

finally:
    con.close()
