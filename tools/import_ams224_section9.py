import re
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section9/page23.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section9/page-22.png")
IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_shuttle_driver_shaft_2_page22.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583
COMPONENT_NAME = "SHUTTLE DRIVER SHAFT COMPONENTS (2)"
SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

PATTERN = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"([A-Z0-9][A-Z0-9-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)

def parse_records():
    records = []

    for line in TXT.read_text(errors="replace").splitlines():
        m = PATTERN.match(line)
        if not m:
            continue

        ref, number, name, qty_raw = m.groups()
        raw = qty_raw.strip()
        numeric = float(raw.strip("()"))
        qty = int(numeric) if numeric.is_integer() else numeric

        records.append({
            "ref": int(ref),
            "marker": None,
            "number": number,
            "name": name.strip(),
            "qty": qty,
            "qty_raw": raw,
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

def stop(message):
    raise RuntimeError(message)

if not DB.is_file() or not TXT.is_file() or not IMAGE_SRC.is_file():
    raise SystemExit("GAGAL: database, teks PDF, atau diagram tidak ditemukan")

records = parse_records()
refs = [r["ref"] for r in records]
number_counts = Counter(r["number"] for r in records)
unique_numbers = len(number_counts)

print("=== VALIDASI SUMBER SECTION 9 ===")
print("Jumlah REF terbaca :", len(records))
print("REF berurutan      :", refs == list(range(1, 73)))
print("Nomor part unik    :", unique_numbers)
print("Nomor part duplikat:", {
    k: v for k, v in number_counts.items() if v > 1
})

if len(records) != 72 or refs != list(range(1, 73)):
    raise SystemExit("GAGAL: REF harus lengkap 1-72")

if unique_numbers != 70:
    raise SystemExit("GAGAL: jumlah nomor part unik bukan 70")

expected = {
    4: ("SM-8060812-TP", "4"),
    6: ("400-86384", "4"),
    8: ("SS-8660612-TP", "(2)"),
    16: ("SM-8060812-TP", "2"),
    69: ("CQ-2000000-00", "2.6"),
    70: ("236-30007", "6.3"),
    72: ("400-72088", "1"),
}

for ref, expected_value in expected.items():
    r = records[ref - 1]
    if (r["number"], r["qty_raw"]) != expected_value:
        raise SystemExit(
            f"GAGAL: data REF {ref} tidak sesuai: "
            f"{r['number']} / {r['qty_raw']}"
        )

expected_duplicates = {
    "SM-8060812-TP": 2,
    "SM-8040502-TP": 2,
}

actual_duplicates = {
    k: v for k, v in number_counts.items() if v > 1
}

if actual_duplicates != expected_duplicates:
    raise SystemExit("GAGAL: pola duplikasi nomor part tidak sesuai")

print("Kuantitas dan duplikasi: VALID")
print("Penanda katalog: tidak ditemukan pada kolom NOTE")
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

    if counts != (423, 6, 423):
        stop("Preflight gagal: kondisi database bukan (423, 6, 423)")

    existing = con.execute(
        "SELECT id FROM components WHERE machine_id=? AND component_name=?",
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
        print("Target akhir parts      : 495")
        print("Target akhir komponen   : 7")
        print("Target akhir relasi     : 495")
        print("Jalankan dengan --apply untuk melakukan impor.")
        sys.exit(0)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    backup = Path(
        "database/garment-before-section9-"
        + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
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
        "Official JUKI parts catalog. Diagram page 22, parts list page 23. Model 6030.",
        SOURCE_URL,
        None,
        22,
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
        SELECT COUNT(*)
        FROM component_parts
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

    old_unchanged = snapshot(con, exclude_id=component_id) == before

    image_db = con.execute(
        "SELECT image_path, diagram_page FROM components WHERE id=?",
        (component_id,)
    ).fetchone()

    print("\n=== PREFLIGHT FINAL ===")
    print("Total parts:", new_counts[0])
    print("Total komponen:", new_counts[1])
    print("Total relasi:", new_counts[2])
    print("Relasi Section 9:", linked)
    print("REF 1-72 valid:", refs_db == list(range(1, 73)))
    print("Komponen lama tidak berubah:", old_unchanged)
    print("Diagram DB:", tuple(image_db))

    if new_counts != (495, 7, 495):
        stop("Jumlah akhir database tidak sesuai")

    if linked != 72 or refs_db != list(range(1, 73)):
        stop("Verifikasi relasi Section 9 gagal")

    if not old_unchanged:
        stop("Data komponen lama berubah")

    if tuple(image_db) != (IMAGE_DB_PATH, 22):
        stop("Path diagram atau halaman diagram tidak sesuai")

    con.commit()

    print("\n=== IMPOR SECTION 9 BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", COMPONENT_NAME)
    print("Diagram page : 22")
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
