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

TXT = Path("tmp/ams224en6030-section22/page45.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section22/page-44.png")

IMAGE_DIR = Path("static/component_images")

IMAGE_NAME = "ams224en6030_wiring_diagram_page44.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "WIRING DIAGRAM"
DIAGRAM_PAGE = 44

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (905, 17, 905)
TARGET = (973, 18, 973)

EXPECTED_REFS = list(range(1, 69))

EXPECTED_DUPLICATES = {}

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
# DATA VALIDASI KATALOG
# REF: (PART NUMBER, DESCRIPTION, QTY RAW, MARKER)
# ============================================================

EXPECTED_VALUES = {
    1:  ("401-08274", "MAIN PCB C ASSY", "1", None),
    2:  ("400-82758", "SDC PCB A ASSY", "1", None),
    3:  ("400-00056", "FLT-T PCB A ASS'Y", "1", "#01"),
    4:  ("400-00046", "FLT-S PCB A ASS'Y", "1", "#02"),
    5:  ("400-73651", "SUB PCB ASSY", "1", None),
    6:  ("400-86485", "IP-420F PANEL ASSY", "1", None),
    7:  ("400-96051", "PANEL CABLE L ASM", "1", None),
    8:  ("400-05401", "FAN MOTOR ASS'Y", "1", None),
    9:  ("400-96030", "POWER CORD 3P ASSY", "1", "#01"),
    10: ("400-96031", "POWER CORD JE ASSY", "1", "#03"),
    11: ("400-96032", "POWER CORD 1P ASSY", "1", "#04"),
    12: ("HD-0005700-0A", "PHOTO SENSOR", "3", None),
    13: ("HA-0058200-00", "SWITCH", "1", None),
    14: ("400-86468", "POWER CABLE 1P PLUG ASSY", "1", "#07"),
    15: ("400-96034", "POWER CABLE 3P ASSY", "1", "#05"),
    16: ("400-96035", "POWER CABLE 1P ASSY", "1", "#02"),
    17: ("HD-0020400-0A", "SENSOR", "1", None),
    18: ("400-05393", "FLT-SDC CORD P ASS'Y", "1", None),
    19: ("HD-0020400-0B", "SENSOR", "1", None),
    20: ("400-05394", "FLT-SDC CORD S ASS'Y", "1", None),
    21: ("400-05726", "SDC-MAIN CORD P ASSY", "1", None),
    22: ("400-05727", "SDC-MAIN CORD S ASSY", "1", None),
    23: ("400-52937", "550W_SERVO_MOTOR", "1", None),
    24: ("400-62367", "SUB-MAIN CORD P ASSY", "1", None),
    25: ("400-62368", "SUB-MAIN CORD S ASSY", "1", None),
    26: ("400-73659", "SW RELAY CORD ASM", "1", None),
    27: ("HD-0027800-00", "SENSOR", "4", None),
    28: ("401-03969", "ENCODER MOTOR ASM.(IP)", "1", None),
    29: ("400-73623", "IP MOTOR CABLE ASM", "1", None),
    30: ("400-73640", "IP ENCODER CABLE ASM", "1", None),
    31: ("401-03968", "ENCODER MOTOR ASM.(TC)", "1", None),
    32: ("400-73622", "TT MOTOR CABLE ASM", "1", None),
    33: ("400-73639", "TT ENCODER CABLE ASM", "1", None),
    34: ("401-04419", "ENCODER MOTOR ASM.(X-Y)", "2", None),
    35: ("400-73620", "X MOTOR CABLE ASM", "1", None),
    36: ("400-73621", "Y MOTOR CABLE ASM", "1", None),
    37: ("400-73632", "X ENCODER CABLE ASM", "1", None),
    38: ("400-73638", "Y ENCODER CABLE ASM", "1", None),
    39: ("400-75079", "STEPPING MOTOR", "1", None),
    40: ("400-73626", "TH MOTOR CABLE ASM", "1", None),
    41: ("400-73660", "AT SOLENOID", "1", None),
    42: ("400-72151", "WIPER ASM", "1", None),
    43: ("401-08280", "AIR RELAY CABLE ASM", "1", None),
    44: ("141-15554", "HEAD GROUND CABLE A ASM.", "1", None),
    45: ("400-48529", "VALVE RERAY CORD ASM", "1", None),
    46: ("400-75391", "AIR SW CABLE ASM", "1", None),
    47: ("400-73671", "X SENSOR CABLE ASM", "1", None),
    48: ("400-73672", "Y SENSOR CABLE ASM", "1", None),
    49: ("400-40238", "PF_SENSOR_CABLE_ASM", "1", None),
    50: ("400-73674", "TH SENSOR ASM", "1", None),
    51: ("400-73675", "IP_SENSOR_CABLE_ASM.", "1", None),
    52: ("400-73676", "STOP SW ASM", "1", None),
    53: ("400-73678", "THB SENSOR CABLE ASM", "1", None),
    54: ("400-40230", "INT PCB ASM", "1", None),
    55: ("400-33831", "PK78 PEDAL SWITCH ASM", "1", None),
    56: ("400-33875", "PK47 RELAY CABLE ASM", "1", "#06"),
    57: ("GPK-470010AB", "3-PEDAL ASM.", "1", "#06"),
    58: ("400-40237", "SHORT CONNECTOR", "3", None),
    59: ("401-11079", "PEDAL EXTENSION CABLE ASM.", "1", None),
    60: ("400-90484", "VALVE CORD ASM.", "1", None),
    61: ("401-63253", "X MOTOR CABLE ASM", "1", "#03"),
    62: ("401-63254", "Y MOTOR CABLE ASM", "1", "#03"),
    63: ("401-63255", "TT MOTOR CABLE ASM", "1", "#03"),
    64: ("401-63256", "IP MOTOR CABLE ASM", "1", "#03"),
    65: ("401-63257", "TH MOTOR CABLE ASM", "1", "#03"),
    66: ("401-63258", "AIR RELAY CABLE ASM.", "1", "#03"),
    67: ("401-63063", "EARTH CODE ASM", "1", "#03"),
    68: ("401-63025", "REACTOR CORD ASSY", "1", "#03"),
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

    if len(records) != 68:
        stop(f"Jumlah occurrence bukan 68: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("Daftar REF tidak berurutan atau tidak lengkap")

    if len(number_counts) != 68:
        stop(
            f"Jumlah nomor part unik bukan 68: {len(number_counts)}"
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
                  OR catalog_ref = '22'
              )
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
        )).fetchone()

        if existing:
            stop(
                "Komponen Section 22 sudah ada: "
                f"ID {existing['id']}, "
                f"{existing['component_name']}, "
                f"catalog_ref={existing['catalog_ref']}"
            )

        before = snapshot(con)

        if len(before) != 17:
            stop("Jumlah komponen lama bukan 17")

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
            print("Nomor part unik :", 68)
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
            "database/garment-before-section22-"
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
            "Official JUKI AMS-224EN-6030 parts catalog, Section 22.",
            SOURCE_URL,
            "22",
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
                68,
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
        print("Relasi Section 22:", len(linked_refs))
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

        print("\n=== IMPOR SECTION 22 BERHASIL ===")
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
