import re
import sys
import sqlite3
import shutil

from pathlib import Path
from datetime import datetime
from collections import Counter


# ============================================================
# KONFIGURASI
# ============================================================

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section26/page50.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section26/page-50.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_type_g_exclusive_parts_page50.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "TYPE G EXCLUSIVE PARTS"
DIAGRAM_PAGE = 50

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (1079, 21, 1079)
TARGET = (1107, 22, 1107)

EXPECTED_REFS = list(range(1, 29))
EXPECTED_DUPLICATES = {}


# ============================================================
# DATA RESMI KATALOG
# REF: (PART NUMBER, DESCRIPTION, QTY RAW, MARKER)
# ============================================================

EXPECTED_VALUES = {
    1: ("400-53776", "NEEDLE_PLATE_ASM.", "1", None),
    2: ("400-30934", "NEEDLE_PLATE", "(1)", None),
    3: ("B2426-210-00F", "NEEDLE HOLE GUIDE D=3.0", "(1)", None),
    4: ("B2424-210-A00", "FIX KNIFE", "(1)", None),
    5: ("B2421-210-AA0", "MOVING KNIFE COMPL.", "(1)", None),
    6: ("B2418-280-000", "MOVING KNIFE LINK", "(1)", None),
    7: ("B2416-280-000", "THREAD CUTTING LEVER RING", "(1)", None),
    8: ("B2415-280-0A0", "THREAD CUTTER LEVER ASM. SMALL", "(1)", None),
    9: ("SS-7090410-SP", "SCREW 9/64-40 L= 3.5", "(1)", None),
    10: ("B2414-280-0A0", "THREAD CUTTER LEVER ASM. LARGE", "(1)", None),
    11: ("SS-1060210-TP", "SCREW 3/32-56 L=2.2", "(1)", None),
    12: ("B2417-210-000", "MOVING KNIFE HINGE SCREW", "(1)", None),
    13: ("WP-0450846-SP", "WASHER", "(1)", None),
    14: ("B2417-280-000", "THREAD CUTTER LEVER SHAFT", "(1)", None),
    15: ("SS-7110740-TP", "SCREW 11/64-40 L=7", "(1)", None),
    16: ("SS-6110430-TP", "SCREW 11/64-40 L=4.0", "(1)", None),
    17: ("B2423-280-00A", "MOVING KNIFE WASHER A", "(1)", "#01"),
    18: ("B2423-280-00B", "MOVING KNIFE WASHER B", "(1)", "#01"),
    19: ("B2423-280-00C", "MOVING KNIFE WASHER C", "(1)", "#01"),
    20: ("B2423-280-00D", "MOVING KNIFE WASHER D", "(1)", "#01"),
    21: ("141-03659", "SHUTTLE RACE RING ASM. C", "1", None),
    22: ("B1601-210-D0B-A", "INTERMEDIATE PRESSER B", "1", None),
    23: ("MDP-170B2300", "NEEDLE DPX17 #23", "1", "#02"),
    24: ("MC-3720016-00", "NEEDLE SY3355 160", "1", "#03"),
    25: ("MDP-170B2302", "NEEDLE DPX17#23-2", "1", "#05"),
    26: ("400-97301", "SILICONE OIL TANK ASM", "1", "#04"),
    27: ("MC-3720016-02", "NEEDLE SY3355 #160-2", "1", "#06"),
    28: ("B2426-210-00G", "NEEDLE HOLE GUIDE D=3", "1", "#04"),
}


# ============================================================
# PARSING
# ============================================================

PATTERN = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"(#\d{2})?\s*"
    r"([A-Z0-9-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)


def stop(message):
    raise RuntimeError(message)


def parse_source():
    source_text = TXT.read_text(
        encoding="utf-8",
        errors="replace"
    )

    records = []
    started = False

    for line in source_text.splitlines():
        if not started:
            if "REF.NO" in line.upper():
                started = True
            continue

        match = PATTERN.match(line)

        if not match:
            if records:
                break
            continue

        ref = int(match.group(1))
        marker = match.group(2)
        number = match.group(3)
        name = match.group(4).strip()
        qty_raw = match.group(5).strip()

        records.append({
            "ref": ref,
            "marker": marker,
            "number": number,
            "name": name,
            "qty_raw": qty_raw,
        })

    if not started:
        stop("Header REF.NO tidak ditemukan")

    if not records:
        stop("Tidak ada REF yang berhasil dibaca")

    return records, source_text


def make_records(source_records):
    records = []

    for r in source_records:
        raw = r["qty_raw"].strip("()")
        qty = float(raw) if "." in raw else int(raw)

        records.append({
            **r,
            "qty": qty,
        })

    return records


# ============================================================
# SNAPSHOT DAN HITUNG DATABASE
# ============================================================

def snapshot(con):
    rows = con.execute("""
        SELECT
            c.id,
            c.component_name,
            c.diagram_page,
            c.image_path,
            COUNT(cp.id) AS relation_count
        FROM components c
        LEFT JOIN component_parts cp
            ON cp.component_id = c.id
        WHERE c.machine_id = ?
        GROUP BY
            c.id,
            c.component_name,
            c.diagram_page,
            c.image_path
        ORDER BY c.id
    """, (MACHINE_ID,)).fetchall()

    return [
        (
            row["id"],
            row["component_name"],
            row["diagram_page"],
            row["image_path"],
            row["relation_count"],
        )
        for row in rows
    ]


def get_counts(con):
    parts = con.execute("""
        SELECT COUNT(*) FROM parts WHERE machine_id = ?
    """, (MACHINE_ID,)).fetchone()[0]

    components = con.execute("""
        SELECT COUNT(*) FROM components WHERE machine_id = ?
    """, (MACHINE_ID,)).fetchone()[0]

    relations = con.execute("""
        SELECT COUNT(*)
        FROM component_parts cp
        JOIN components c ON c.id = cp.component_id
        WHERE c.machine_id = ?
    """, (MACHINE_ID,)).fetchone()[0]

    return parts, components, relations


# ============================================================
# VALIDASI SOURCE
# ============================================================

def validate_source(source_records, source_text):
    records = make_records(source_records)

    refs = [r["ref"] for r in records]
    number_counts = Counter(r["number"] for r in records)

    actual_duplicates = {
        k: v for k, v in number_counts.items() if v > 1
    }

    if len(records) != 28:
        stop(f"Jumlah REF bukan 28: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("REF tidak berurutan atau tidak lengkap")

    if len(number_counts) != 28:
        stop(f"Nomor part unik bukan 28: {len(number_counts)}")

    if actual_duplicates != EXPECTED_DUPLICATES:
        stop(f"Duplikasi tidak sesuai: {actual_duplicates}")

    if set(EXPECTED_VALUES) != set(refs):
        stop("EXPECTED_VALUES tidak cocok dengan daftar REF")

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
            stop(f"Nomor part REF {r['ref']} tidak ditemukan")

        if not r["qty_raw"]:
            stop(f"Quantity kosong pada REF {r['ref']}")

    print("Jumlah REF:", len(refs))
    print("REF berurutan:", refs == EXPECTED_REFS)
    print("Nomor part unik:", len(number_counts))
    print("Duplikasi:", actual_duplicates)
    print("Nama dan nomor part: VALID")
    print("Marker #01 sampai #06: VALID")
    print("Quantity raw: VALID")

    return records, actual_duplicates


# ============================================================
# MAIN IMPORT
# ============================================================

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
        source_records,
        source_text
    )

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    image_copied = False

    try:
        machine = con.execute("""
            SELECT id, model FROM machines WHERE id = ?
        """, (MACHINE_ID,)).fetchone()

        if not machine or machine["model"] != "AMS-224EN-6030":
            stop("Machine ID 47 tidak cocok dengan AMS-224EN-6030")

        document = con.execute("""
            SELECT id FROM documents
            WHERE id = ? AND machine_id = ?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

        if not document:
            stop("Dokumen sumber ID 583 tidak ditemukan")

        counts = get_counts(con)
        print("\nKondisi database:", counts)

        if counts != BASELINE:
            stop(f"Baseline harus {BASELINE}, aktual {counts}")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref
            FROM components
            WHERE machine_id = ?
              AND (
                  component_name = ?
                  OR catalog_ref = '26'
              )
        """, (MACHINE_ID, COMPONENT_NAME)).fetchone()

        if existing:
            stop(
                "Komponen Section 26 sudah ada: "
                f"ID {existing['id']} "
                f"{existing['component_name']}"
            )

        before = snapshot(con)

        if len(before) != 21:
            stop("Jumlah komponen lama bukan 21")

        # ----------------------------------------------------
        # DRY RUN
        # ----------------------------------------------------

        if "--apply" not in sys.argv:
            print("\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Target parts    :", TARGET[0])
            print("Target komponen :", TARGET[1])
            print("Target relasi   :", TARGET[2])
            print("REF baru        :", len(records))
            print("Nomor part unik :", len({r["number"] for r in records}))
            print("Marker #01      :", 4)
            print("Marker #02      :", 1)
            print("Marker #03      :", 1)
            print("Marker #04      :", 2)
            print("Marker #05      :", 1)
            print("Marker #06      :", 1)
            print("Quantity (1)    :", 19)
            print("Quantity 1      :", 9)
            print("Diagram page    :", DIAGRAM_PAGE)
            print("\nJalankan --apply hanya setelah dry-run valid.")
            return

        # ----------------------------------------------------
        # BACKUP
        # ----------------------------------------------------

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        backup = Path(
            "database/garment-before-section26-"
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

        # ----------------------------------------------------
        # TRANSAKSI
        # ----------------------------------------------------

        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components (
                machine_id,
                component_name,
                location,
                function,
                notes,
                source_url,
                catalog_ref,
                diagram_page,
                image_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
            None,
            None,
            "Official JUKI AMS-224EN-6030 parts catalog, Section 26.",
            SOURCE_URL,
            "26",
            DIAGRAM_PAGE,
            IMAGE_DB_PATH,
        ))

        component_id = cur.lastrowid

        for r in records:
            cur = con.execute("""
                INSERT INTO parts (
                    machine_id,
                    source_document_id,
                    part_number,
                    part_name,
                    quantity,
                    catalog_ref,
                    diagram_page,
                    note,
                    source_url,
                    notes,
                    quantity_raw
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
                    component_id,
                    part_id,
                    relation_type,
                    notes
                )
                VALUES (?, ?, ?, ?)
            """, (
                component_id,
                part_id,
                "catalog_component_part",
                f"REF {r['ref']}",
            ))

        # ----------------------------------------------------
        # AUDIT HASIL INSERT
        # ----------------------------------------------------

        new_counts = get_counts(con)

        inserted = con.execute("""
            SELECT
                p.part_number,
                p.part_name,
                p.quantity,
                p.quantity_raw,
                p.note,
                cp.notes,
                cp.relation_type
            FROM component_parts cp
            JOIN parts p ON p.id = cp.part_id
            WHERE cp.component_id = ?
            ORDER BY CAST(
                REPLACE(cp.notes, 'REF ', '') AS INTEGER
            )
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
                SELECT notes FROM component_parts
                WHERE component_id = ?
                ORDER BY CAST(
                    REPLACE(notes, 'REF ', '') AS INTEGER
                )
            """, (component_id,))
        ]

        if new_counts != TARGET:
            stop(f"Total database tidak sesuai: {new_counts}")

        if linked_refs != EXPECTED_REFS:
            stop("Daftar REF relasi tidak sesuai")

        if actual_inserted != expected_inserted:
            stop("Data part, quantity, marker, atau relasi tidak sesuai")

        expected_snapshot = before + [
            (
                component_id,
                COMPONENT_NAME,
                DIAGRAM_PAGE,
                IMAGE_DB_PATH,
                28,
            )
        ]

        if snapshot(con) != expected_snapshot:
            stop("Komponen lama berubah atau snapshot baru tidak sesuai")

        # ----------------------------------------------------
        # SALIN DAN VALIDASI DIAGRAM
        # ----------------------------------------------------

        shutil.copy2(IMAGE_SRC, IMAGE_DST)
        image_copied = True

        image_info = con.execute("""
            SELECT image_path, diagram_page
            FROM components WHERE id = ?
        """, (component_id,)).fetchone()

        if not image_info or tuple(image_info) != (
            IMAGE_DB_PATH,
            DIAGRAM_PAGE,
        ):
            stop("Path diagram atau diagram_page tidak sesuai")

        if not IMAGE_DST.is_file() or IMAGE_DST.stat().st_size == 0:
            stop("File diagram hasil salin tidak valid")

        print("\n=== PREFLIGHT FINAL ===")
        print("Total parts:", new_counts[0])
        print("Total komponen:", new_counts[1])
        print("Total relasi:", new_counts[2])
        print("Relasi Section 26:", len(linked_refs))
        print("REF valid:", linked_refs == EXPECTED_REFS)
        print("Data part dan quantity_raw valid:", True)
        print("Marker #01 sampai #06 valid:", True)
        print("Komponen lama tidak berubah:", True)
        print("Diagram DB:", tuple(image_info))
        print("Ukuran diagram:", IMAGE_DST.stat().st_size, "bytes")

        con.commit()

        print("\n=== IMPOR SECTION 26 BERHASIL ===")
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
