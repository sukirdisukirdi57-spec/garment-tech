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
TXT = Path("tmp/ams224en6030-section25/page49.txt")
IMAGE_SRC = Path("tmp/ams224en6030-section25/page-49.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams224en6030_accessorie_parts_page49.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = "ACCESSORIE PARTS COMPONENTS"
DIAGRAM_PAGE = 49

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

BASELINE = (1059, 20, 1059)
TARGET = (1079, 21, 1079)

EXPECTED_REFS = list(range(1, 21))

EXPECTED_DUPLICATES = {}


# ============================================================
# VALIDASI DATA KATALOG
# Format:
# REF: (PART NUMBER, DESCRIPTION, QTY RAW, MARKER)
# ============================================================

EXPECTED_VALUES = {
    1: ("B1806-210-D00", "BOBBIN", "1", "☆"),
    2: ("B1131-528-000", "FELT", "1", None),
    3: ("101-02200", "THREAD GUIDE F", "1", None),
    4: ("MDP-170B1802", "NEEDLE DPZ17#18-2", "1", "☆ #01"),
    5: ("MC-3720011-02", "NEEDLE SY3355 #110-2", "1", "☆ #02"),
    6: ("137-04705", "BELT SIDE COVER SHAFT", "1", None),
    7: ("SM-6040860-TP", "SCREW M4 L=8", "1", None),
    8: ("B9101-490-000", "DRIVER", "1", None),
    9: ("B9113-012-000", "WRENCH (9X10)", "1", None),
    10: ("B9140-372-000", "HEXAGONAL WRENCH SMALL", "1", None),
    11: ("400-32763", "HEXAGONAL_DRIVER(1.5)", "1", None),
    12: ("CM-6001002-01", "WEEE INFORMATION SHEET", "1", "#02"),
    13: ("400-06323", "JUKI GREASE A TUBE", "1", None),
    14: ("229-33204", "SCREW DRIVER SMALL", "1", None),
    15: ("229-32800", "ACCESSORIE BAG", "1", None),
    16: ("B9121-220-0A0", "OILER (CONTAINING NO.2 OIL)", "1", None),
    17: ("B8601-WP1-0A0", "TOOL BOX ASM.", "1", None),
    18: ("400-50647", "COMPACTFLASH(TM) SET AMS-221E", "1", None),
    19: ("229-33105", "SCREW DRIVER MIDDLE", "1", None),
    20: ("400-72154", "COVER", "1", None),
}


# ============================================================
# PARSING
# ============================================================

PATTERN = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"(☆\s+)?"
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
        star = bool(match.group(2))
        hash_marker = match.group(3)
        number = match.group(4)
        name = match.group(5).strip()
        qty_raw = match.group(6).strip()

        marker_parts = []

        if star:
            marker_parts.append("☆")

        if hash_marker:
            marker_parts.append(hash_marker)

        marker = " ".join(marker_parts) or None

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

    number_counts = Counter(
        r["number"] for r in records
    )

    actual_duplicates = {
        k: v
        for k, v in number_counts.items()
        if v > 1
    }

    if len(records) != 20:
        stop(f"Jumlah REF bukan 20: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("REF tidak berurutan atau tidak lengkap")

    if len(number_counts) != 20:
        stop(
            f"Nomor part unik bukan 20: {len(number_counts)}"
        )

    if actual_duplicates != EXPECTED_DUPLICATES:
        stop(
            f"Duplikasi tidak sesuai: {actual_duplicates}"
        )

    if set(EXPECTED_VALUES) != set(refs):
        stop("Daftar EXPECTED_VALUES tidak cocok dengan REF")

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
    print("Marker bintang dan #01/#02: VALID")
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
                  OR catalog_ref = '25'
              )
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
        )).fetchone()

        if existing:
            stop(
                "Komponen Section 25 sudah ada: "
                f"ID {existing['id']}, "
                f"{existing['component_name']}, "
                f"catalog_ref={existing['catalog_ref']}"
            )

        before = snapshot(con)

        if len(before) != 20:
            stop("Jumlah komponen lama bukan 20")

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
            print("Nomor part unik :", 20)
            print("Duplikasi       :", actual_duplicates)
            print("Simbol bintang  :", sum(
                1 for r in records
                if r["marker"] and "☆" in r["marker"]
            ))
            print("Marker #01/#02  :", sum(
                1 for r in records
                if r["marker"] and "#" in r["marker"]
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
            "database/garment-before-section25-"
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
            "Official JUKI AMS-224EN-6030 parts catalog, Section 25.",
            SOURCE_URL,
            "25",
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
            stop(f"Total database tidak sesuai: {new_counts}")

        if linked_refs != EXPECTED_REFS:
            stop("Daftar REF relasi tidak sesuai")

        if actual_inserted != expected_inserted:
            stop(
                "Data part, quantity, quantity_raw, marker, "
                "atau relasi tidak sesuai"
            )

        expected_snapshot = before + [
            (
                component_id,
                COMPONENT_NAME,
                DIAGRAM_PAGE,
                IMAGE_DB_PATH,
                20,
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
        print("Relasi Section 25:", len(linked_refs))
        print("REF valid:", linked_refs == EXPECTED_REFS)
        print("Data part dan quantity_raw valid:", True)
        print("Marker bintang dan #01/#02 valid:", True)
        print("Duplikasi occurrence:", actual_duplicates)
        print("Komponen lama tidak berubah:", True)
        print("Diagram DB:", tuple(image_info))
        print(
            "Ukuran diagram:",
            IMAGE_DST.stat().st_size,
            "bytes"
        )

        con.commit()

        print("\n=== IMPOR SECTION 25 BERHASIL ===")
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
