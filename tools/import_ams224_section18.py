import sqlite3
import sys
import re
import shutil
from pathlib import Path
from collections import Counter
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section18/page38.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section18/page-38.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_pneumatic_components_page38.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583
COMPONENT_NAME = "PNEUMATIC COMPONENTS"
DIAGRAM_PAGE = 38

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (749, 13, 749)
TARGET = (773, 14, 773)

EXPECTED_REFS = list(range(1, 25))

EXPECTED_DUPLICATES = {
    "EA-9500B01-00": 2,
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


EXPECTED_VALUES = {
    1:  ("400-72220", "SOLENOID_VALVE_ASM", "1", None),
    2:  ("PV-9150050-00", "SOLENOID VALVE INSTALLING BASE", "(1)", None),
    3:  ("PJ-3010405-05", "HALF UNION", "(2)", None),
    4:  ("PV-1502091-00", "SOLENOID VALVE", "(1)", None),
    5:  ("PV-1351270-A0", "3-WAY SOLENOID VALVE", "1", None),
    6:  ("PJ-3010651-03", "HALF UNION 6XPT1/8", "2", None),
    7:  ("PX-0551040-00", "SILENCER (PT1/8)", "1", None),
    8:  ("BT-0600401-EB", "TUBE", "1.1", None),
    9:  ("EA-9500B01-00", "CABLE BAND", "1", None),
    10: ("PJ-3010600-03", "REDUCER", "1", None),
    11: ("SL-4040891-SC", "SCREW M4 L=8", "4", None),
    12: ("B4715-215-0A0", "FILTER REGULATOR ASM.", "1", None),
    13: ("PF-0552040-B0", "FILTER REGULATOR", "(1)", None),
    14: ("G8124-270-000", "AIR PRESSUE SWITCH", "(1)", None),
    15: ("PJ-3050652-02", "TEE", "(1)", None),
    16: ("PJ-0305200-01", "RING JOINT (NIPPLE)", "(1)", None),
    17: ("G5430-116-000", "AIR COCK", "(1)", None),
    18: ("PJ-3090052-03", "QUICK JOINT PLUG", "(1)", None),
    19: ("HK-0346100-40", "HOUSING", "(1)", None),
    20: ("HK-0346400-00", "PIN CONTACT", "(3)", None),
    21: ("EA-9500B01-00", "CABLE BAND", "(5)", None),
    22: ("PX-9500090-00", "PLUG", "(1)", None),
    23: ("E2678-453-000", "CONNECTOR MARKER J78", "(1)", None),
    24: ("SL-4051091-SC", "SCREW M5X0.8 L=10", "2", None),
}


def validate_source(source_records, source_text):
    source_refs = [r["ref"] for r in source_records]

    if len(source_records) != 24:
        stop(
            f"Jumlah REF sumber {len(source_records)}, seharusnya 24"
        )

    if source_refs != EXPECTED_REFS:
        stop("REF sumber tidak lengkap atau tidak berurutan 1-24")

    records = make_records(source_records)
    refs = [r["ref"] for r in records]

    number_counts = Counter(r["number"] for r in records)
    actual_duplicates = {
        k: v for k, v in number_counts.items() if v > 1
    }

    print("=== VALIDASI SUMBER SECTION 18 ===")
    print("Judul:", COMPONENT_NAME)
    print("Jumlah REF sumber:", len(source_records))
    print("REF sumber lengkap:", source_refs == EXPECTED_REFS)
    print("Jumlah occurrence:", len(records))
    print("REF terpilih valid:", refs == EXPECTED_REFS)
    print("Nomor part unik:", len(number_counts))
    print("Nomor part duplikat:", actual_duplicates)

    if refs != EXPECTED_REFS:
        stop("Daftar occurrence tidak sesuai")

    if len(number_counts) != 23:
        stop("Jumlah nomor part unik bukan 23")

    if actual_duplicates != EXPECTED_DUPLICATES:
        stop("Pola duplikasi nomor part tidak sesuai")

    if any(r["marker"] is not None for r in records):
        stop("Ditemukan marker yang tidak diharapkan")

    if set(EXPECTED_VALUES) != set(refs):
        stop("Daftar validasi REF tidak sama dengan sumber")

    for r in records:
        expected = EXPECTED_VALUES[r["ref"]]
        actual = (
            r["number"],
            r["name"],
            r["qty_raw"],
            r["marker"],
        )

        if actual != expected:
            stop(
                f"Data REF {r['ref']} tidak sesuai.\n"
                f"Aktual: {actual}\n"
                f"Harus : {expected}"
            )

        if r["number"] not in source_text:
            stop(
                f"Nomor part REF {r['ref']} tidak ditemukan di sumber"
            )

        if not r["qty_raw"]:
            stop(f"Quantity kosong pada REF {r['ref']}")

    print("Nomor part, nama, marker, dan quantity_raw: VALID")
    print("Quantity khusus REF 8:", records[7]["qty_raw"])
    print("Duplikasi occurrence:", actual_duplicates)
    print("Sumber teks:", TXT)
    print("Diagram:", IMAGE_SRC)

    return records, actual_duplicates


def main():
    if not DB.is_file():
        stop("Database aktif tidak ditemukan")

    if not TXT.is_file():
        stop(f"Teks sumber tidak ditemukan: {TXT}")

    if not IMAGE_SRC.is_file():
        stop(f"Diagram sumber tidak ditemukan: {IMAGE_SRC}")

    if IMAGE_DST.exists():
        stop(f"File diagram tujuan sudah ada: {IMAGE_DST}")

    source_records, source_text = parse_source()
    records, actual_duplicates = validate_source(
        source_records, source_text
    )

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    image_copied = False

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
                f"Baseline harus {BASELINE}, aktual {counts}"
            )

        existing = con.execute("""
            SELECT id, component_name, catalog_ref
            FROM components
            WHERE machine_id=?
              AND (component_name=? OR catalog_ref='18')
        """, (MACHINE_ID, COMPONENT_NAME)).fetchone()

        if existing:
            stop(
                "Komponen Section 18 sudah ada: "
                f"ID {existing['id']}, "
                f"{existing['component_name']}, "
                f"catalog_ref={existing['catalog_ref']}"
            )

        before = snapshot(con)

        if len(before) != 13:
            stop("Jumlah komponen lama bukan 13")

        if "--apply" not in sys.argv:
            print("\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Target parts     :", TARGET[0])
            print("Target komponen  :", TARGET[1])
            print("Target relasi    :", TARGET[2])
            print("REF baru         :", len(records))
            print("Nomor part unik  :", 23)
            print("Diagram page     :", DIAGRAM_PAGE)
            print("Jalankan dengan --apply untuk melakukan impor.")
            return

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        backup = Path(
            "database/garment-before-section18-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )

        if backup.exists():
            stop(f"File backup sudah ada: {backup}")

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
            "Official JUKI AMS-224EN-6030 parts catalog, Section 18.",
            SOURCE_URL,
            "18",
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
            SELECT p.part_number, p.part_name, p.quantity,
                   p.quantity_raw, p.note, cp.notes,
                   cp.relation_type
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY CAST(REPLACE(cp.notes, 'REF ', '') AS INTEGER)
        """, (component_id,)).fetchall()

        expected_inserted = [
            (
                r["number"],
                r["name"],
                r["qty"],
                r["qty_raw"],
                r["marker"],
                f"REF {r['ref']}",
                "catalog_component_part",
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
            stop("Data part, quantity, quantity_raw, atau relasi tidak sesuai")

        expected_snapshot = before + [
            (
                component_id,
                COMPONENT_NAME,
                DIAGRAM_PAGE,
                IMAGE_DB_PATH,
                24,
            )
        ]

        if snapshot(con) != expected_snapshot:
            stop("Komponen lama berubah atau snapshot komponen baru tidak sesuai")

        shutil.copy2(IMAGE_SRC, IMAGE_DST)
        image_copied = True

        image_info = con.execute("""
            SELECT image_path, diagram_page
            FROM components
            WHERE id=?
        """, (component_id,)).fetchone()

        if not image_info:
            stop("Komponen baru tidak ditemukan saat audit diagram")

        if tuple(image_info) != (IMAGE_DB_PATH, DIAGRAM_PAGE):
            stop("Path diagram atau diagram_page tidak sesuai")

        if not IMAGE_DST.is_file() or IMAGE_DST.stat().st_size == 0:
            stop("File diagram hasil salin tidak valid")

        print("\n=== PREFLIGHT FINAL ===")
        print("Total parts:", new_counts[0])
        print("Total komponen:", new_counts[1])
        print("Total relasi:", new_counts[2])
        print("Relasi Section 18:", len(linked_refs))
        print("REF valid:", linked_refs == EXPECTED_REFS)
        print("Data part dan quantity_raw valid:", True)
        print("Quantity REF 8:", records[7]["qty_raw"])
        print("Duplikasi part tetap terpisah:", actual_duplicates)
        print("Komponen lama tidak berubah:", True)
        print("Diagram DB:", tuple(image_info))
        print("Ukuran diagram:", IMAGE_DST.stat().st_size, "bytes")

        con.commit()

        print("\n=== IMPOR SECTION 18 BERHASIL ===")
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

        if image_copied and IMAGE_DST.exists():
            IMAGE_DST.unlink()

        print("\n=== IMPOR DIBATALKAN ===")
        print("Alasan:", exc)
        raise

    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nGAGAL:", exc)
        sys.exit(1)
