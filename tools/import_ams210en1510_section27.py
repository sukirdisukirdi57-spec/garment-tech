import re
import sys
import sqlite3
import shutil

from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
IMAGE_SRC = Path("tmp/ams210en/section27_pdf52.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams210en1510_optional_part_components_3_page52.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 15
DOCUMENT_ID = 136
MODEL = "AMS-210EN-1510"

COMPONENT_NAME = "27. OPTIONAL PART COMPONENTS (3)"
CATALOG_REF = "27"
DIAGRAM_PAGE = 47

BASELINE = (829, 14, 266)
TARGET = (874, 15, 311)

EXPECTED_TEXT = """
1|#01|400-42352|MECHANICAL VALVE UNIT|1
2|-|D8001-D15-A0Y|PEDAL BASE|(1)
3|-|D8002-D15-A0Y|PEDAL CUSHION|(2)
4|-|SS-6111210-SP|SCREW 11/64-40 L=12|(2)
5|-|WP-0450801-SD|WASHER 4.5X10X0.8|(2)
6|-|WS-0451040-KP|SPRING WASHER 4.5X8.5X1|(2)
7|-|WP-0553216-SD|WASHER|(2)
8|-|PX-0200020-00|ACTUATOR|(1)
9|-|PV-0105020-00|AIR VALVE|(1)
10|-|PJ-3010405-01|HALF UNION M5 D=4|(6)
11|-|PX-5000140-00|PLUG|(2)
12|-|BT-0400251-EB|URETHANE HOSE BLACK|(1.9)
13|-|BT-0400251-EB|URETHANE HOSE BLACK|(1.8)
14|-|BT-0400251-EB|URETHANE HOSE BLACK|(1.9)
15|-|HX-0031400-0A|SPIRAL TUBE|(0.6)
16|-|EA-9500B01-00|CABLE BAND|(3)
17|-|GEP-01013000|VALVE|(1)
18|-|BT-0400251-EB|URETHANE HOSE BLACK|(0.1)
19|-|BT-0400251-EB|URETHANE HOSE BLACK|(0.1)
20|-|180-35204|WIRE MARK (3)|(2)
21|-|180-35303|WIRE MARK (4)|(1)
22|-|180-35600|WIRE MARK (7)|(2)
23|-|180-35709|WIRE MARK (8)|(1)
24|-|PJ-3080400-02|QUICK COUPLING|(2)
25|-|WP-0450801-SD|WASHER 4.5X10X0.8|(2)
26|-|WS-0451040-KP|SPRING WASHER 4.5X8.5X1|(2)
27|-|SS-7111120-TP|SCREW|(2)
28|#01|400-89848|AIR UNIT ASM.|1
29|-|PV-9150050-00|SOLENOID VALVE INSTALLING BASE|(1)
30|-|SK-3412001-SE|WOOD SCREW D=4.1 L=20|(2)
31|-|PJ-3040600-01|ELBOW|(1)
32|-|PX-0500030-00|SILENCER|(1)
33|-|BT-0600401-EB|TUBE|(1.3)
34|-|400-30951|FILTER_REGULATOR_ASM.|(1)
35|-|SL-4051091-SC|SCREW M5X0.8 L=10|(2)
36|-|400-23662|FILTER INSTALLING PLATE|(1)
37|-|SL-9082093-SE|SCREW|(1)
38|-|WP-0871602-SE|WASHER 8.7X18X1.6|(1)
39|-|NM-6080721-SE|NUT M8|(1)
40|-|400-48529|VALVE RELAY CORD ASM|(1)
41|-|400-81601|AIR RELAY CABLE ASM|(1)
42|-|PJ-3095200-01|SOCKET|(1)
43|-|PB-0000100-00|HOSE BAND|(1)
44|-|EA-9500B01-00|CABLE BAND|(1)
45|-|400-93109|AIR SW CABLE ASM|(1)
"""


def stop(message):
    raise RuntimeError(message)


def load_expected():
    result = {}
    for line in EXPECTED_TEXT.strip().splitlines():
        ref, marker, number, name, qty = line.split("|", 4)
        result[int(ref)] = (
            number, name, qty,
            None if marker == "-" else marker
        )
    return result


EXPECTED = load_expected()
EXPECTED_REFS = list(range(1, 46))


def parse_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    section = next(
        (i for i, line in enumerate(lines)
         if "27. OPTIONAL PART COMPONENTS (3)" in line
         and i > 200),
        None
    )
    if section is None:
        stop("Judul Section 27 tidak ditemukan")

    header = next(
        (i for i in range(section, len(lines))
         if "REF.NO" in lines[i].upper()),
        None
    )
    if header is None:
        stop("Header REF.NO Section 27 tidak ditemukan")

    end = next(
        (i for i in range(header + 1, len(lines))
         if re.match(r"^\s*28\.", lines[i])),
        None
    )
    if end is None:
        stop("Batas Section 28 tidak ditemukan")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+"
        r"(?:(#\d{2})\s+)?"
        r"([A-Z0-9_-]+)\s+"
        r"(.+?)\s+"
        r"(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    invalid = []

    for i in range(header + 1, end):
        line = lines[i]
        if not line.strip():
            continue

        match = pattern.match(line)
        if match:
            records.append({
                "ref": int(match.group(1)),
                "marker": match.group(2),
                "number": match.group(3),
                "name": match.group(4).strip(),
                "qty_raw": match.group(5).strip(),
            })
        elif re.match(r"^\s*\d{1,3}\s+", line):
            invalid.append((i + 1, line.strip()))

    if invalid:
        stop(f"Baris tabel gagal diparse: {invalid[:5]}")

    return records, header + 1, end


def validate_source(records):
    refs = [r["ref"] for r in records]

    if len(records) != 45:
        stop(f"Jumlah REF bukan 45: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("REF tidak berurutan atau tidak lengkap")

    unique_pn = len(set(r["number"] for r in records))
    if unique_pn != 38:
        stop(f"PN unik bukan 38: {unique_pn}")

    for r in records:
        actual = (
            r["number"], r["name"],
            r["qty_raw"], r["marker"]
        )
        expected = EXPECTED.get(r["ref"])

        if actual != expected:
            stop(
                f"Data REF {r['ref']} berbeda.\n"
                f"Aktual: {actual}\n"
                f"Harus : {expected}"
            )

        raw = r["qty_raw"].strip("()")
        r["qty"] = float(raw) if "." in raw else int(raw)

    if set(refs) != set(EXPECTED):
        stop("EXPECTED_VALUES tidak cocok dengan sumber")

    print("Jumlah REF:", len(records))
    print("REF berurutan 1-45: VALID")
    print("PN unik:", unique_pn)
    print("Marker:", [
        (r["ref"], r["marker"])
        for r in records if r["marker"]
    ])
    print("Nama, PN, quantity_raw: VALID")

    return records


def snapshot(con):
    rows = con.execute("""
        SELECT c.id, c.component_name, c.catalog_ref,
               c.diagram_page, c.image_path,
               COUNT(cp.part_id) AS relasi
        FROM components c
        LEFT JOIN component_parts cp ON cp.component_id=c.id
        WHERE c.machine_id=?
        GROUP BY c.id
        ORDER BY c.id
    """, (MACHINE_ID,)).fetchall()

    return [tuple(r) for r in rows]


def get_counts(con):
    parts = con.execute("""
        SELECT COUNT(*) FROM parts WHERE machine_id=?
    """, (MACHINE_ID,)).fetchone()[0]

    components = con.execute("""
        SELECT COUNT(*) FROM components WHERE machine_id=?
    """, (MACHINE_ID,)).fetchone()[0]

    relations = con.execute("""
        SELECT COUNT(*)
        FROM component_parts cp
        JOIN components c ON c.id=cp.component_id
        WHERE c.machine_id=?
    """, (MACHINE_ID,)).fetchone()[0]

    return parts, components, relations


def main():
    for path in (DB, TXT, IMAGE_SRC):
        if not path.is_file():
            stop(f"File tidak ditemukan: {path}")

    if IMAGE_DST.exists():
        stop(f"Gambar tujuan sudah ada, tidak akan ditimpa: {IMAGE_DST}")

    records, header_line, end_line = parse_source()
    records = validate_source(records)

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    image_copied = False

    try:
        machine = con.execute("""
            SELECT id, model FROM machines WHERE id=?
        """, (MACHINE_ID,)).fetchone()

        if not machine or machine["model"] != MODEL:
            stop("Machine ID 15 tidak cocok dengan AMS-210EN-1510")

        document = con.execute("""
            SELECT id, title, source_url
            FROM documents
            WHERE id=? AND machine_id=?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

        if not document or not document["source_url"]:
            stop("Dokumen ID 136 atau source URL tidak valid")

        source_url = document["source_url"]
        counts = get_counts(con)

        print("\nBaseline database:", counts)
        if counts != BASELINE:
            stop(f"Baseline harus {BASELINE}, aktual {counts}")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref
            FROM components
            WHERE machine_id=?
              AND (
                component_name=?
                OR (catalog_ref=? AND diagram_page=?)
            )
        """, (MACHINE_ID, COMPONENT_NAME, CATALOG_REF, DIAGRAM_PAGE)).fetchall()

        if existing:
            stop(f"Komponen Section 27 sudah ada: {[dict(x) for x in existing]}")

        before = snapshot(con)
        if len(before) != 14:
            stop("Jumlah komponen lama bukan 14")

        print("Batas sumber: baris", header_line, "sampai", end_line)
        print("Gambar sumber:", IMAGE_SRC)
        print("Nama komponen:", COMPONENT_NAME)
        print("Halaman katalog:", DIAGRAM_PAGE)

        if "--apply" not in sys.argv:
            print("\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Part baru       :", len(records))
            print("Komponen baru   : 1")
            print("Relasi baru     :", len(records))
            print("Target parts    :", TARGET[0])
            print("Target komponen :", TARGET[1])
            print("Target relasi   :", TARGET[2])
            print("Gambar tujuan   :", IMAGE_DB_PATH)
            print("\nJika hasil sesuai, jalankan dengan --apply.")
            return

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        backup = Path(
            "database/garment-before-ams210en1510-section27-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        if backup.exists():
            stop(f"Backup sudah ada: {backup}")

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
            MACHINE_ID, COMPONENT_NAME, None, None,
            "Official JUKI AMS-210EN Series Parts List, Section 27.",
            source_url, CATALOG_REF, DIAGRAM_PAGE, IMAGE_DB_PATH
        ))
        component_id = cur.lastrowid

        for r in records:
            cur = con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number,
                    part_name, quantity, catalog_ref, diagram_page,
                    note, source_url, notes, quantity_raw
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
            """, (
                MACHINE_ID, DOCUMENT_ID, r["number"], r["name"],
                r["qty"], r["ref"], r["marker"], source_url,
                f"AMS-210EN-1510 section: {COMPONENT_NAME}",
                r["qty_raw"]
            ))
            part_id = cur.lastrowid

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, ?, ?)
            """, (
                component_id, part_id,
                "catalog_component_part", f"REF {r['ref']}"
            ))

        new_counts = get_counts(con)

        inserted = con.execute("""
            SELECT p.catalog_ref, p.part_number, p.part_name,
                   p.quantity, p.quantity_raw, p.note,
                   cp.notes, cp.relation_type
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY CAST(p.catalog_ref AS INTEGER)
        """, (component_id,)).fetchall()

        expected_inserted = [
            (
                r["ref"], r["number"], r["name"], r["qty"],
                r["qty_raw"], r["marker"], f"REF {r['ref']}",
                "catalog_component_part"
            )
            for r in records
        ]

        if [tuple(x) for x in inserted] != expected_inserted:
            stop("Audit data part dan relasi hasil insert gagal")

        linked_refs = [
            int(x["notes"].replace("REF ", ""))
            for x in con.execute("""
                SELECT notes FROM component_parts
                WHERE component_id=?
                ORDER BY CAST(REPLACE(notes, 'REF ', '') AS INTEGER)
            """, (component_id,))
        ]

        if linked_refs != EXPECTED_REFS:
            stop("Audit REF relasi gagal")

        if new_counts != TARGET:
            stop(f"Total database tidak sesuai: {new_counts}")

        expected_snapshot = before + [(
            component_id, COMPONENT_NAME, CATALOG_REF,
            DIAGRAM_PAGE, IMAGE_DB_PATH, 45
        )]

        if snapshot(con) != expected_snapshot:
            stop("Komponen lama berubah atau snapshot baru tidak sesuai")

        shutil.copy2(IMAGE_SRC, IMAGE_DST)
        image_copied = True

        if not IMAGE_DST.is_file() or IMAGE_DST.stat().st_size == 0:
            stop("Salinan gambar tidak valid")

        print("\n=== AUDIT SEBELUM COMMIT ===")
        print("Parts:", new_counts[0])
        print("Komponen:", new_counts[1])
        print("Relasi:", new_counts[2])
        print("REF 1-45:", linked_refs == EXPECTED_REFS)
        print("Data part/quantity/marker: VALID")
        print("Komponen lama tidak berubah: VALID")
        print("Gambar:", IMAGE_DST)
        print("Ukuran gambar:", IMAGE_DST.stat().st_size, "bytes")

        con.commit()

        print("\n=== IMPOR SECTION 27 BERHASIL ===")
        print("Component ID:", component_id)
        print("Nama:", COMPONENT_NAME)
        print("REF:", len(linked_refs))
        print("Database:", new_counts)
        print("Backup:", backup)

    except Exception:
        con.rollback()
        if image_copied and IMAGE_DST.exists():
            IMAGE_DST.unlink()
        raise

    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nGAGAL:", exc)
        sys.exit(1)
