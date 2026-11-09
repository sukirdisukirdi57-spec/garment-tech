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

TXT = Path(
    "tmp/ams224en6030-section24/page48.txt"
)

IMAGE_SRC = Path(
    "tmp/ams224en6030-section24/page-48.png.png"
)

IMAGE_DIR = Path("static/component_images")

IMAGE_NAME = "ams224en6030_pedal_components_page48.png"

IMAGE_DST = IMAGE_DIR / IMAGE_NAME

IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "PEDAL COMPONENTS"

DIAGRAM_PAGE = 48

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (1021, 19, 1021)
TARGET = (1059, 20, 1059)

EXPECTED_REFS = list(range(1, 39))

EXPECTED_DUPLICATES = {
    "WP-0450801-SD": 2,
    "WS-0451040-KP": 2,
    "BT-0400251-EB": 8,
    "180-35204": 2,
    "180-35600": 2,
    "180-35709": 2,
}


# ============================================================
# VALIDASI DATA REF
# Format:
# REF: (PART NUMBER, DESCRIPTION, QTY RAW, MARKER)
# ============================================================

EXPECTED_VALUES = {
    1: ("400-33831", "PK78 PEDAL SWITCH ASM.", "1", None),
    2: ("400-42352", "MECHANICAL VALVE UNIT", "1", None),
    3: ("D8001-D15-A0Y", "PEDAL BASE", "(1)", None),
    4: ("WP-0450801-SD", "WASHER 4.5X10X0.8", "(2)", None),
    5: ("WS-0451040-KP", "SPRING WASHER 4.5X8.5X1", "(2)", None),
    6: ("SS-7111120-TP", "SCREW", "(2)", None),
    7: ("SS-6111210-SP", "SCREW 11/64-40 L=12", "(2)", None),
    8: ("WP-0450801-SD", "WASHER 4.5X10X0.8", "(2)", None),
    9: ("WS-0451040-KP", "SPRING WASHER 4.5X8.5X1", "(2)", None),
    10: ("WP-0553216-SD", "WASHER", "(2)", None),
    11: ("PX-0200020-00", "ACTUATOR", "(1)", None),
    12: ("PV-0105020-00", "AIR VALVE", "(1)", None),
    13: ("PJ-3010405-01", "HALF UNION M5 D=4", "(6)", None),
    14: ("PX-5000140-00", "PLUG", "(2)", None),
    15: ("BT-0400251-EB", "URETHANE HOSE BLACK", "(1.9)", None),
    16: ("BT-0400251-EB", "URETHANE HOSE BLACK", "(1.8)", None),
    17: ("BT-0400251-EB", "URETHANE HOSE BLACK", "(1.9)", None),
    18: ("HX-0031400-0A", "SPIRAL TUBE", "(0.6)", None),
    19: ("EA-9500B01-00", "CABLE BAND", "(3)", None),
    20: ("GEP-01013000", "VALVE", "(1)", None),
    21: ("BT-0400251-EB", "URETHANE HOSE BLACK", "(0.1)", None),
    22: ("BT-0400251-EB", "URETHANE HOSE BLACK", "(0.1)", None),
    23: ("180-35204", "WIRE MARK (3)", "(2)", None),
    24: ("180-35303", "WIRE MARK (4)", "(1)", None),
    25: ("180-35600", "WIRE MARK (7)", "(2)", None),
    26: ("180-35709", "WIRE MARK (8)", "(1)", None),
    27: ("PJ-3080400-02", "QUICK COUPLING", "(2)", None),
    28: ("D8002-D15-A0Y", "PEDAL CUSHION", "(2)", None),
    29: ("PJ-3030400-02", "STRAIGHT UNION", "3", None),
    30: ("BT-0400251-EB", "URETHANE HOSE BLACK", "1.6", None),
    31: ("BT-0400251-EB", "URETHANE HOSE BLACK", "1.6", None),
    32: ("BT-0400251-EB", "URETHANE HOSE BLACK", "1.6", None),
    33: ("180-35204", "WIRE MARK (3)", "1", None),
    34: ("180-35709", "WIRE MARK (8)", "1", None),
    35: ("180-35600", "WIRE MARK (7)", "1", None),
    36: ("401-11079", "PEDAL EXTENSION CABLE ASM.", "1", None),
    37: ("HX-0015000-0E", "CORD PRESSER 3-POLE (220/240V)", "1", None),
    38: ("SL-4040891-SC", "SCREW M4 L=8", "2", None),
}


# ============================================================
# POLA PARSING
# ============================================================

PATTERN = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"(?:(#\d{2})\s+)?"
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
        stop("Header REF.NO tidak ditemukan dalam teks sumber")

    if not records:
        stop("Tidak ada baris REF yang berhasil dibaca")

    return records, source_text


def make_records(source_records):
    records = []

    for r in source_records:
        raw = r["qty_raw"].strip("()")

        if "." in raw:
            qty = float(raw)
        else:
            qty = int(raw)

        records.append({
            **r,
            "qty": qty,
        })

    return records


# ============================================================
# SNAPSHOT DATABASE
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
    parts = con.execute(
        "SELECT COUNT(*) FROM parts WHERE machine_id = ?",
        (MACHINE_ID,)
    ).fetchone()[0]

    components = con.execute(
        "SELECT COUNT(*) FROM components WHERE machine_id = ?",
        (MACHINE_ID,)
    ).fetchone()[0]

    relations = con.execute("""
        SELECT COUNT(*)
        FROM component_parts cp
        JOIN components c ON c.id = cp.component_id
        WHERE c.machine_id = ?
    """, (MACHINE_ID,)).fetchone()[0]

    return parts, components, relations


# ============================================================
# VALIDASI SUMBER
# ============================================================

def validate_source(source_records, source_text):
    records = make_records(source_records)

    refs = [r["ref"] for r in records]

    number_counts = Counter(
        r["number"] for r in records
    )

    actual_duplicates = {
        k: v
        for k, v in number_counts.items()
        if v > 1
    }

    if len(records) != 38:
        stop(f"Jumlah occurrence bukan 38: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("Daftar REF tidak berurutan atau tidak lengkap")

    if len(number_counts) != 26:
        stop(
            f"Jumlah nomor part unik bukan 26: {len(number_counts)}"
        )

    if actual_duplicates != EXPECTED_DUPLICATES:
        stop(
            f"Pola duplikasi tidak sesuai: {actual_duplicates}"
        )

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
                f"Nomor part REF {r['ref']} "
                "tidak ditemukan dalam sumber"
            )

        if not r["qty_raw"]:
            stop(f"Quantity kosong pada REF {r['ref']}")

    print("Jumlah REF:", len(refs))
    print("REF berurutan:", refs == EXPECTED_REFS)
    print("Nomor part unik:", len(number_counts))
    print("Duplikasi:", actual_duplicates)
    print("Nama dan nomor part: VALID")
    print("Marker: VALID")
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
            SELECT id, model
            FROM machines
            WHERE id = ?
        """, (MACHINE_ID,)).fetchone()

        if not machine or machine["model"] != "AMS-224EN-6030":
            stop("Machine ID 47 tidak cocok dengan AMS-224EN-6030")

        document = con.execute("""
            SELECT id
            FROM documents
            WHERE id = ? AND machine_id = ?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

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
            WHERE machine_id = ?
              AND (
                  component_name = ?
                  OR catalog_ref = '24'
              )
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
        )).fetchone()

        if existing:
            stop(
                "Komponen Section 24 sudah ada: "
                f"ID {existing['id']}, "
                f"{existing['component_name']}, "
                f"catalog_ref={existing['catalog_ref']}"
            )

        before = snapshot(con)

        if len(before) != 19:
            stop("Jumlah komponen lama bukan 19")

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
            print("Nomor part unik :", 26)
            print("Duplikasi       :", actual_duplicates)
            print("Marker          :", sum(
                1 for r in records if r["marker"]
            ))
            print("Diagram page    :", DIAGRAM_PAGE)

            print(
                "\nJalankan dengan --apply "
                "untuk melakukan impor."
            )
            return

        # ----------------------------------------------------
        # BACKUP DATABASE
        # ----------------------------------------------------

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        backup = Path(
            "database/garment-before-section24-"
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
        # TRANSAKSI DATABASE
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
            "Official JUKI AMS-224EN-6030 parts catalog, Section 24.",
            SOURCE_URL,
            "24",
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
        # VALIDASI SETELAH INSERT
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

        actual_inserted = [
            tuple(r) for r in inserted
        ]

        linked_refs = [
            int(row["notes"].replace("REF ", ""))
            for row in con.execute("""
                SELECT notes
                FROM component_parts
                WHERE component_id = ?
                ORDER BY CAST(
                    REPLACE(notes, 'REF ', '') AS INTEGER
                )
            """, (component_id,))
        ]

        if new_counts != TARGET:
            stop(
                f"Total database tidak sesuai: {new_counts}"
            )

        if linked_refs != EXPECTED_REFS:
            stop("Daftar REF relasi tidak sesuai")

        if actual_inserted != expected_inserted:
            stop(
                "Data part, quantity, quantity_raw, "
                "marker, atau relasi tidak sesuai"
            )

        expected_snapshot = before + [
            (
                component_id,
                COMPONENT_NAME,
                DIAGRAM_PAGE,
                IMAGE_DB_PATH,
                38,
            )
        ]

        if snapshot(con) != expected_snapshot:
            stop(
                "Komponen lama berubah atau "
                "snapshot komponen baru tidak sesuai"
            )

        # ----------------------------------------------------
        # SALIN DAN VALIDASI DIAGRAM
        # ----------------------------------------------------

        shutil.copy2(IMAGE_SRC, IMAGE_DST)
        image_copied = True

        image_info = con.execute("""
            SELECT image_path, diagram_page
            FROM components
            WHERE id = ?
        """, (component_id,)).fetchone()

        if not image_info:
            stop("Komponen baru tidak ditemukan saat audit diagram")

        if tuple(image_info) != (
            IMAGE_DB_PATH,
            DIAGRAM_PAGE,
        ):
            stop("Path diagram atau diagram_page tidak sesuai")

        if (
            not IMAGE_DST.is_file()
            or IMAGE_DST.stat().st_size == 0
        ):
            stop("File diagram hasil salin tidak valid")

        # ----------------------------------------------------
        # HASIL AKHIR
        # ----------------------------------------------------

        print("\n=== PREFLIGHT FINAL ===")
        print("Total parts:", new_counts[0])
        print("Total komponen:", new_counts[1])
        print("Total relasi:", new_counts[2])
        print("Relasi Section 24:", len(linked_refs))
        print("REF valid:", linked_refs == EXPECTED_REFS)
        print("Data part dan quantity_raw valid:", True)
        print("Marker valid:", True)
        print("Duplikasi occurrence:", actual_duplicates)
        print("Komponen lama tidak berubah:", True)
        print("Diagram DB:", tuple(image_info))
        print(
            "Ukuran diagram:",
            IMAGE_DST.stat().st_size,
            "bytes"
        )

        con.commit()

        print("\n=== IMPOR SECTION 24 BERHASIL ===")
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
