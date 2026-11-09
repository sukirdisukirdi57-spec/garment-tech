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

TXT = Path("tmp/ams224en6030-section23/page47.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section23/page-46.png")

IMAGE_DIR = Path("static/component_images")

IMAGE_NAME = "ams224en6030_table_components_page46.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "TABLE COMPONENTS"
DIAGRAM_PAGE = 46

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (973, 18, 973)
TARGET = (1021, 19, 1021)

EXPECTED_REFS = list(range(1, 49))

EXPECTED_DUPLICATES = {
    "SL-4041091-SC": 2,
    "WP-0841601-SC": 2,
    "WS-0820002-KN": 2,
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
# DATA VALIDASI KATALOG
# REF: (PART NUMBER, DESCRIPTION, QTY RAW, MARKER)
# ============================================================

EXPECTED_VALUES = {
    1:  ("400-72145", "STAND ASM", "1", None),
    2:  ("400-72077", "CASTER", "(4)", None),
    3:  ("400-72087", "ADJUSTER", "(4)", None),
    4:  ("400-72206", "BOLT", "(3)", None),
    5:  ("400-72223", "WASHER LARGE", "(24)", None),
    6:  ("400-73222", "UPPER_STAND", "(1)", None),
    7:  ("400-73224", "TOP_BASE_L", "(1)", None),
    8:  ("400-73225", "TOP_BASE_R", "(1)", None),
    9:  ("400-73226", "CROSS_LEG", "(6)", None),
    10: ("WP-1302501-SC", "WASHER 13X24X2.5", "(6)", None),
    11: ("WS-1220002-KN", "SPRING WASHER", "(15)", None),
    12: ("400-73227", "BASE", "(1)", None),
    13: ("400-73230", "BRACKET_BT", "(1)", None),
    14: ("400-73231", "BRACKET_B", "(1)", None),
    15: ("NM-6100001-SE", "NUT FOR SPRING ADJUSTING BOLT", "(16)", None),
    16: ("NM-6120001-SE", "NUT M12", "(15)", None),
    17: ("NM-6160001-SC", "NUT", "(4)", None),
    18: ("SL-9082093-SE", "SCREW", "(12)", None),
    19: ("SM-9129013-SB", "SCREW M12 L=90", "(12)", None),
    20: ("400-73216", "SW_BASE_JE", "1", "#01"),
    21: ("SM-1061201-SN", "SCREW M6 L=12", "2", "#01"),
    22: ("B8117-223-C00", "BOLT", "4", None),
    23: ("B8118-223-C00", "COVER INSTALLING STAY", "4", None),
    24: ("B8171-220-000", "RUBBER ABSORBER", "4", None),
    25: ("400-72146", "TABLE", "2", None),
    26: ("HX-0032600-0B", "BUSH", "5", None),
    27: ("HX-0032600-0M", "DOME PLUG", "3", None),
    28: ("HX-0032600-0G", "PLUG", "3", None),
    29: ("PS-0400141-KH", "SPRING PIN 4X14", "8", None),
    30: ("SL-4041091-SC", "SCREW M4 L=10", "8", None),
    31: ("SM-9087533-SC", "SCREW M8 L=75", "2", None),
    32: ("WP-0841601-SC", "WASHER 8.4X17.4X1.6", "2", None),
    33: ("WP-0841601-SC", "WASHER 8.4X17.4X1.6", "4", None),
    34: ("WS-0820002-KN", "SPRING WASHER M8", "2", None),
    35: ("WS-0820002-KN", "SPRING WASHER M8", "4", None),
    36: ("168-70206", "GRAVITY SEAL", "2", None),
    37: ("NM-6080001-SC", "NUT M8X1.25", "2", None),
    38: ("HX-0015000-0H", "CABLE CLIP", "3", None),
    39: ("SL-4040891-SC", "SCREW M4 L=8", "3", None),
    40: ("EA-9500B01-00", "CABLE BAND", "2", None),
    41: ("400-72231", "STOPPER_RUBBER", "2", None),
    42: ("SK-3271301-SE", "WOOD SCREW D=2.7 L=13", "2", None),
    43: ("400-81603", "SWITCH INSTALLATION BOARD", "1", "#02"),
    44: ("SK-3512001-SE", "WOOD SCREW D=5.1 L=20", "2", "#02"),
    45: ("HX-0015000-0B", "CABLE CLIP", "1", None),
    46: ("SL-4041091-SC", "SCREW M4 L=10", "1", None),
    47: ("400-89584", "TABLE ASM.", "2", "#03"),
    48: ("400-90431", "RUBBER", "4", None),
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

    if len(records) != 48:
        stop(f"Jumlah occurrence bukan 48: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("Daftar REF tidak berurutan atau tidak lengkap")

    if len(number_counts) != 45:
        stop(
            f"Jumlah nomor part unik bukan 45: {len(number_counts)}"
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
                  OR catalog_ref = '23'
              )
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
        )).fetchone()

        if existing:
            stop(
                "Komponen Section 23 sudah ada: "
                f"ID {existing['id']}, "
                f"{existing['component_name']}, "
                f"catalog_ref={existing['catalog_ref']}"
            )

        before = snapshot(con)

        if len(before) != 18:
            stop("Jumlah komponen lama bukan 18")

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
            print("Nomor part unik :", 45)
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
            "database/garment-before-section23-"
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
            "Official JUKI AMS-224EN-6030 parts catalog, Section 23.",
            SOURCE_URL,
            "23",
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
                48,
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
        print("Relasi Section 23:", len(linked_refs))
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

        print("\n=== IMPOR SECTION 23 BERHASIL ===")
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
