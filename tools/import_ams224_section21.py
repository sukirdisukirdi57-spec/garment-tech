#!/usr/bin/env python3

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

TXT = Path("tmp/ams224en6030-section21/page43.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section21/page-42.png")

IMAGE_DIR = Path("static/component_images")

IMAGE_NAME = "ams224en6030_control_box_components_page42.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "CONTROL BOX COMPONENTS"
DIAGRAM_PAGE = 42

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (843, 16, 843)
TARGET = (905, 17, 905)

EXPECTED_REFS = list(range(1, 63))

EXPECTED_DUPLICATES = {
    "SL-4040891-SC": 4,
    "WP-0841601-SC": 2,
    "NM-6080001-SC": 2,
    "SL-4040881-SC": 3,
    "NM-3040520-SC": 2,
}

# ============================================================
# POLA BARIS TABEL
# REF | MARKER OPSIONAL | PART NUMBER | DESCRIPTION | QTY
# ============================================================

PATTERN = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"(?:(#\d{2})\s+)?"
    r"([A-Z0-9-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)

# ============================================================
# DATA VALIDASI RESMI KATALOG
# REF: (PART NUMBER, DESCRIPTION, QTY RAW, MARKER)
# ============================================================

EXPECTED_VALUES = {
    1:  ("400-55355", "CONTROL BOX", "1", None),
    2:  ("400-55356", "CONTROL BOX FRONT COVER", "1", None),
    3:  ("400-55357", "CONTROL BOX REAR COVER", "1", None),
    4:  ("SL-4040891-SC", "SCREW M4 L=8", "6", None),
    5:  ("SL-4040891-SC", "SCREW M4 L=8", "4", None),
    6:  ("M3801-476-000", "CONTROL BOX FITTING PLATE", "1", None),
    7:  ("SL-6083092-TN", "SCREW", "4", None),
    8:  ("WP-0841601-SC", "WASHER 8.4X17.4X1.6", "4", None),
    9:  ("NM-6080001-SC", "NUT M8X1.25", "8", None),
    10: ("M4206-461-000", "WASHER", "4", None),
    11: ("401-08274", "MAIN PCB C ASSY", "1", None),
    12: ("SL-4040891-SC", "SCREW M4 L=8", "6", None),
    13: ("400-82758", "SDC PCB A ASSY", "1", None),
    14: ("SL-4040881-SC", "SCREW M4 L=8", "10", None),
    15: ("400-00056", "FLT-T PCB A ASS'Y", "1", "#01"),
    16: ("400-00046", "FLT-S PCB A ASS'Y", "1", "#02"),
    17: ("SL-4040881-SC", "SCREW M4 L=8", "6", None),
    18: ("HX-0033900-00", "STUD", "6", None),
    19: ("NM-3040520-SC", "NUT M4", "6", None),
    20: ("400-05706", "MAIN PCB HOLDER PLATE", "1", None),
    21: ("SL-4040881-SC", "SCREW M4 L=8", "5", None),
    22: ("400-05401", "FAN MOTOR ASS'Y", "1", None),
    23: ("KM-0000004-80", "FAN MOTOR", "1", None),
    24: ("SL-4043591-SC", "SCREW", "4", None),
    25: ("NM-3040520-SC", "NUT M4", "4", None),
    26: ("HX-0040700-00", "BUSH", "1", None),
    27: ("178-45009", "CORD FITTING PLATE", "1", None),
    28: ("SL-4041091-SC", "SCREW M4 L=10", "2", None),
    29: ("400-96030", "POWER CORD 3P ASSY", "1", "#01"),
    30: ("400-96031", "POWER CORD JE ASSY", "1", "#03"),
    31: ("400-96032", "POWER CORD 1P ASSY", "1", "#04"),
    32: ("HX-0041000-0A", "STRAIN RELIEF BUSHING", "1", None),
    33: ("400-05393", "FLT-SDC CORD P ASS'Y", "1", None),
    34: ("WS-0820002-KN", "SPRING WASHER M8", "2", None),
    35: ("400-05394", "FLT-SDC CORD S ASS'Y", "1", None),
    36: ("400-05726", "SDC-MAIN CORD P ASSY", "1", None),
    37: ("400-05727", "SDC-MAIN CORD S ASSY", "1", None),
    38: ("SL-4040891-SC", "SCREW M4 L=8", "4", None),
    39: ("HX-0051100-00", "WIRE SADDLE", "3", None),
    40: ("E9607-603-000", "STICKER (SMALL)", "1", None),
    41: ("E9567-319-000", "EARTH MARK", "1", None),
    42: ("400-03458", "MASK SEAL", "16", None),
    43: (
        "400-51640",
        "ELECTRICAL_RATING_LABEL_UNIVERSAL",
        "1",
        "#05",
    ),
    44: ("NM-6080001-SC", "NUT M8X1.25", "2", None),
    45: ("HX-0032600-0K", "GROMMET", "1", None),
    46: ("400-73659", "SW RELAY CORD ASM.", "1", None),
    47: ("HN-0014900-00", "CLAMP FILTER(L)", "1", None),
    48: ("EA-9500B01-00", "CABLE BAND", "1", None),
    49: ("CM-2001000-01", "PE MARK LABEL", "1", "#03"),
    50: (
        "400-57278",
        "ELECTRICAL_RATING_LABEL_CE_UNIVERSAL",
        "1",
        "#03",
    ),
    51: ("SL-4041081-SC", "SCREW M4 L=10", "1", "#03"),
    52: ("CM-6001001-01", "WEEE MARK LABEL S", "1", "#03"),
    53: ("M9029-580-0A0", "FDD EARTH CORD ASM.", "1", None),
    54: ("400-73651", "SUB PCB ASSY", "1", None),
    55: ("400-62367", "SUB-MAIN CORD P ASSY", "1", None),
    56: ("400-62368", "SUB-MAIN CORD S ASSY", "1", None),
    57: ("HX-0041800-0E", "SPACER", "4", None),
    58: ("HX-0014700-0J", "SPACER", "1", None),
    59: ("SL-4030881-SC", "SCREW M3X8", "8", None),
    60: ("SL-6082092-TN", "BOLT", "1", None),
    61: ("SM-6087002-TN", "SCREW M8 L=70", "2", None),
    62: ("WP-0841601-SC", "WASHER 8.4X17.4X1.6", "4", None),
}

# ============================================================
# HELPER
# ============================================================

def stop(message):
    raise RuntimeError(message)


def parse_source():
    text = TXT.read_text(errors="replace")

    result = []
    started = False

    for line in text.splitlines():
        if "REF.NO" in line:
            started = True
            continue

        if not started:
            continue

        match = PATTERN.match(line)

        if match:
            ref, marker, number, name, qty_raw = match.groups()

            result.append({
                "ref": int(ref),
                "marker": marker,
                "number": number,
                "name": name.strip(),
                "qty_raw": qty_raw,
            })

        elif result:
            break

    return result, text


def make_records(source_records):
    result = []

    for r in source_records:
        numeric = float(r["qty_raw"].strip("()"))

        qty = (
            int(numeric)
            if numeric.is_integer()
            else numeric
        )

        result.append({
            **r,
            "qty": qty,
        })

    return result


def snapshot(con):
    return [
        tuple(r)
        for r in con.execute("""
            SELECT
                c.id,
                c.component_name,
                c.diagram_page,
                c.image_path,
                COUNT(cp.id)
            FROM components c
            LEFT JOIN component_parts cp
                ON cp.component_id = c.id
            WHERE c.machine_id = ?
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
            JOIN components c ON c.id = cp.component_id
            WHERE c.machine_id = ?
        """, (MACHINE_ID,)).fetchone()[0],
    )


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

    if len(records) != 62:
        stop(f"Jumlah occurrence bukan 62: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("Daftar REF tidak berurutan atau tidak lengkap")

    if len(number_counts) != 54:
        stop(
            f"Jumlah nomor part unik bukan 54: {len(number_counts)}"
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
                  OR catalog_ref = '21'
              )
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
        )).fetchone()

        if existing:
            stop(
                "Komponen Section 21 sudah ada: "
                f"ID {existing['id']}, "
                f"{existing['component_name']}, "
                f"catalog_ref={existing['catalog_ref']}"
            )

        before = snapshot(con)

        if len(before) != 16:
            stop("Jumlah komponen lama bukan 16")

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
            print("Nomor part unik :", 54)
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
            "database/garment-before-section21-"
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
            "Official JUKI AMS-224EN-6030 parts catalog, Section 21.",
            SOURCE_URL,
            "21",
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
                62,
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
        print("Relasi Section 21:", len(linked_refs))
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

        print("\n=== IMPOR SECTION 21 BERHASIL ===")
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
