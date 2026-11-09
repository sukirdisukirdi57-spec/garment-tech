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
TXT = Path("tmp/ams224en6030-section27/page51.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section27/page-51.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_separate_stroke_type_exclusive_parts_page51.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "SEPARATE STROKE TYPE EXCLUSIVE PARTS"
DIAGRAM_PAGE = 51

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (1107, 22, 1107)
TARGET = (1132, 23, 1132)

EXPECTED_REFS = list(range(1, 26))
EXPECTED_DUPLICATES = {
    "BT-0400251-EB": 2,
    "PJ-3080400-02": 2,
    "EA-9500B01-00": 2,
}


# ============================================================
# DATA RESMI KATALOG
# REF: (PART NUMBER, DESCRIPTION, QTY RAW, MARKER)
# ============================================================

EXPECTED_VALUES = {
    1: ("400-76736", "SOLENOID_INSTALLING_PLATE_A_ASM.", "1", None),
    2: ("400-76738", "SOLENOID_INSTALLING_PLATE", "(1)", None),
    3: ("PV-1352070-00", "3-PORT ELECTROMAGNETIC VALVE", "(1)", None),
    4: ("PJ-3040652-01", "ELBOW UNION 6XPT1/4", "(1)", None),
    5: ("PJ-3050652-04", "DOUBLE-ENDED T UNION", "(1)", None),
    6: ("PV-1551130-00", "5-PORT SOLENOID VALVE", "(1)", None),
    7: ("PJ-3050651-07", "DOUBLE-ENDED T UNION", "(1)", None),
    8: ("PJ-3080600-05", "DIFFERENT DIAMETER UNION Y", "(1)", None),
    9: ("PC-0124060-00", "SPEED CONTROLLER", "(2)", None),
    10: ("PJ-3080400-02", "QUICK COUPLING", "(4)", None),
    11: ("SL-4031691-SC", "SCREW M3 L=16", "(4)", None),
    12: ("SL-4032591-SC", "SCREW M3X25", "(4)", None),
    13: ("EA-9500B01-00", "CABLE BAND", "(3)", None),
    14: ("BT-0400251-EB", "URETHANE HOSE BLACK", "(0.6)", None),
    15: ("BT-0600401-EB", "TUBE", "(1.1)", None),
    16: ("SL-6051292-TN", "BOLT", "2", None),
    17: ("PX-9500010-00", "PLUG", "1", None),
    18: ("GPK-470010AB", "3-PEDAL ASM.", "1", None),
    19: ("BT-0400251-EB", "URETHANE HOSE BLACK", "1.7", None),
    20: ("PJ-3080400-02", "QUICK COUPLING", "4", None),
    21: ("EA-9500B01-00", "CABLE BAND", "3", None),
    22: ("400-74127", "AIR EXTENSION CODE ASM.", "1", None),
    23: ("400-33875", "PK47 RELAY CABLE ASM", "1", None),
    24: ("HX-0015000-0E", "CORD PRESSER 3-POLE (220/240V)", "1", None),
    25: ("SL-4040891-SC", "SCREW M4 L=8", "2", None),
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

    if len(records) != 25:
        stop(f"Jumlah REF bukan 25: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("REF tidak berurutan atau tidak lengkap")

    if len(number_counts) != 22:
        stop(f"Nomor part unik bukan 22: {len(number_counts)}")

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
    print("Marker katalog: VALID")
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
                  OR catalog_ref = '27'
              )
        """, (MACHINE_ID, COMPONENT_NAME)).fetchone()

        if existing:
            stop(
                "Komponen Section 27 sudah ada: "
                f"ID {existing['id']} "
                f"{existing['component_name']}"
            )

        before = snapshot(con)

        if len(before) != 22:
            stop("Jumlah komponen lama bukan 22")

        # ----------------------------------------------------
        # DRY RUN
        # ----------------------------------------------------

        if "--apply" not in sys.argv:
            qty_counts = Counter(r["qty_raw"] for r in records)
            print("\\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Target parts    :", TARGET[0])
            print("Target komponen :", TARGET[1])
            print("Target relasi   :", TARGET[2])
            print("REF baru        :", len(records))
            print("Nomor part unik :", len({r["number"] for r in records}))
            print("Duplikasi       :", actual_duplicates)
            print("Quantity raw    :", dict(qty_counts))
            print("Diagram page    :", DIAGRAM_PAGE)
            print("\\nJalankan --apply hanya setelah dry-run valid.")
            return

        # ----------------------------------------------------
        # BACKUP
        # ----------------------------------------------------

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        backup = Path(
            "database/garment-before-section27-"
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
            "Official JUKI AMS-224EN-6030 parts catalog, Section 27.",
            SOURCE_URL,
            "27",
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
                25,
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
        print("Relasi Section 27:", len(linked_refs))
        print("REF valid:", linked_refs == EXPECTED_REFS)
        print("Data part dan quantity_raw valid:", True)
        print("Marker katalog valid:", True)
        print("Komponen lama tidak berubah:", True)
        print("Diagram DB:", tuple(image_info))
        print("Ukuran diagram:", IMAGE_DST.stat().st_size, "bytes")

        con.commit()

        print("\n=== IMPOR SECTION 27 BERHASIL ===")
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
