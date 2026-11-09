import re
import sys
import sqlite3
import shutil

from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
IMAGE_SRC = Path("tmp/ams210en/section26_pdf50.png")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams210en1510_optional_part_components_2_page50.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 15
DOCUMENT_ID = 136

MODEL = "AMS-210EN-1510"
COMPONENT_NAME = "26. OPTIONAL PART COMPONENTS (2)"
CATALOG_REF = "26"
DIAGRAM_PAGE = 45

BASELINE = (729, 13, 166)
TARGET = (829, 14, 266)

EXPECTED_TEXT = """
1|-|B1601-210-D0B-A|INTERMEDIATE PRESSER B|1
2|-|B1601-210-D0C-A|INTERMEDIATE PRESSER C|1
3|-|B1601-210-D0E|INNER PRESSER E|1
4|-|B1601-210-D0F-A|INTERMEDIATE PRESSER F|1
5|-|141-03253|INNER HOOK PRESSER ASM. A|1
6|-|141-03659|SHUTTLE RACE RING ASM. C|1
7|-|B1817-210-DAD|SHUTTLE RACE RING ASM. D|1
8|-|400-35606|FEEDING FRAME BLANK|1
9|-|400-35607|FEEDING FRAME BLANK|1
10|-|400-35608|FEEDING FRAME BLANK|1
11|-|400-35609|FEEDING FRAME BLANK R|1
12|-|400-35610|FEEDING FRAME BLANK L|1
13|#03|B2556-210-D0A|LOWER PLATE BLANK|1
14|#03|B2556-210-D0B|LOWER PLATE BLANK|1
15|-|B2594-210-DA0|CASSETTE PRESSER ASM.|1
16|-|B2594-210-D00|CASSETTE PRESSER BASE PLATE|(1)
17|-|B2598-210-D00|CASSETTE PRESSER LOWER PLATE|(1)
18|-|B2599-210-D00|CASSETTE PRESSER UPPER PLATE|(1)
19|-|B2589-210-D00|CASSETTE PRESSER SPACER|(1)
20|-|B2572-229-000|FILAMENT TAPE|(1)
21|-|B2646-215-000|TAPE|(1)
22|-|B2587-210-000|MATERIAL PLATE A|(1)
23|-|B2593-210-DA0|CASSETTE HOLDER FIX PLATE ASM.|1
24|-|B2593-210-D00|CASSETTE HOLDER FIXING PLATE|(1)
25|-|B2560-372-000|BUTTON CLAMP STOP PIN|(2)
26|#01|400-89692|ONE-TOUCH CLAMP ASM.|1
27|-|400-89693|PRESSER PLATE ASM.|(1)
28|-|400-89694|PRESSER PLATE|(1)
29|-|B2587-210-D00|SLIDER HOLDING|(1)
30|-|B5038-206-000|SET SC|(1)
31|-|B5039-206-000|SET PLATE|(1)
32|-|161-08300|NUT B|(1)
33|-|SS-7110840-SP|SCREW 11/64-40 L=7.8|(2)
34|-|WP-0480856-SP|WASHER 4.8X8.4X0.8|(2)
35|-|WZ-0430200-KH|WAVED WASHER|(1)
36|-|B2595-210-DA0|SLIDER ASM.|(1)
37|-|B2595-210-D00|SLIDER|(1)
38|-|B1816-280-000|GUIDE PIN|(4)
39|-|B2597-210-D00|CLAMP PLATE|(1)
40|-|B5115-210-000|FEEDING FRAME CLAMP LEVER|(2)
41|#02|400-89695|ONE-TOUCH CLAMP ASM.|1
42|-|400-89696|PRESSER PLATE RIGHT ASM.|(1)
43|-|400-89697|PRESSER PLATE RIGHT|(1)
44|-|B2588-210-D00|SLIDER HOLDING|(1)
45|-|B5038-206-000|SET SC|(1)
46|-|B5039-206-000|SET PLATE|(1)
47|-|161-08300|NUT B|(1)
48|-|SS-7110840-SP|SCREW 11/64-40 L=7.8|(2)
49|-|WP-0480856-SP|WASHER 4.8X8.4X0.8|(2)
50|-|WZ-0430200-KH|WAVED WASHER|(1)
51|-|400-89698|PRESSER PLATE LEFT ASM.|(1)
52|-|400-89699|PRESSER PLATE LEFT|(1)
53|-|B2588-210-D00|SLIDER HOLDING|(1)
54|-|B5038-206-000|SET SC|(1)
55|-|B5039-206-000|SET PLATE|(1)
56|-|161-08300|NUT B|(1)
57|-|SS-7110840-SP|SCREW 11/64-40 L=7.8|(2)
58|-|WP-0480856-SP|WASHER 4.8X8.4X0.8|(2)
59|-|WZ-0430200-KH|WAVED WASHER|(1)
60|-|B2596-210-DA0|SLIDER ASM. RIGHT|(1)
61|-|B2596-210-D00|SLIDER|(1)
62|-|PS-0400082-KP|SPRING PIN|(3)
63|-|B2596-210-DAA|SLIDER ASM. LEFT|(1)
64|-|B2596-210-D00|SLIDER|(1)
65|-|PS-0400082-KP|SPRING PIN|(3)
66|-|B2597-210-D00|CLAMP PLATE|(1)
67|-|B5115-210-000|FEEDING FRAME CLAMP LEVER|(2)
68|-|B2535-210-000|TANK BASE|1
69|-|SM-4040855-SP|SCREW|2
70|-|400-72310|THREAD TENTION NO.3 ASSY|1
71|-|400-40560|THREAD TENSION NO.3 ASM.|(1)
72|-|B3114-771-000|THREAD GUIDE|(2)
73|-|NS-6090310-SP|NUT 9/64-40|(2)
74|-|PJ-3010405-02|HALF UNION 4XM5|(1)
75|-|NM-6160511-SE|NUT M16X1.5|(1)
76|-|PA-0600504-A0|AIR CYLINDER|(1)
77|-|G2302-309-000|THREAD TENSION ROD BASE|(1)
78|-|G2301-309-000|THREAD TENSION ROD|(1)
79|-|B3126-012-000|THREAD TENSION DISK|(2)
80|-|B3132-552-000|THREAD TENSION DISK PRESSER|(1)
81|-|B3121-352-000|TENSION SPRING|(1)
82|-|B3120-125-000|ROTATING STOPPER|(1)
83|-|110-72204|TENSION NUT|(1)
84|-|BT-0400251-EB|URETHANE HOSE BLACK|(2)
85|-|D4012-D10-N0H|THREAD TENSION NO.3 BASE|(1)
86|-|PV-1502090-00|5 PORT SOLENOID VALVE|(1)
87|-|PX-5000140-00|PLUG|(1)
88|-|400-35324|SOLENOID VALVE CONNECTER ASM|(1)
89|-|SM-6062002-TP|SCREW M6 L=20|(1)
90|-|WP-0612516-SD|WASHER 6.1X15.2X2.5|(1)
91|-|B3532-223-C00|SILICON TANK|1
92|-|B2426-210-00C|NEEDLE HOLE GUIDE D=1.6|1
93|-|B2426-210-00F|NEEDLE HOLE GUIDE D=3.0|1
94|-|B2426-210-00G|NEEDLE HOLE GUIDE D=3|1
95|-|B2426-210-00H|NEEDLE HOLE GUIDE D=3.0|1
96|-|400-14965|SHUTTLE(H)|1
97|-|400-98294|INNER_PRESSER|1
98|#04|400-99714|LOWER_PLATE_BLANK|1
99|#03|B2552-210-D00|LOWER PLATE|1
100|#05|400-36477|LOWER_PLATE|1
"""

def stop(message):
    raise RuntimeError(message)


def expected_values():
    result = {}
    for line in EXPECTED_TEXT.strip().splitlines():
        ref, marker, number, name, qty = line.split("|", 4)
        result[int(ref)] = (
            number, name, qty, None if marker == "-" else marker
        )
    return result


EXPECTED = expected_values()
EXPECTED_REFS = list(range(1, 101))


def parse_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    section = next(
        (i for i, line in enumerate(lines)
         if "26. OPTIONAL PART COMPONENTS (2)" in line
         and i > 200),
        None
    )
    if section is None:
        stop("Judul Section 26 tidak ditemukan")

    header = next(
        (i for i in range(section, len(lines))
         if "REF.NO" in lines[i].upper()),
        None
    )
    if header is None:
        stop("Header REF.NO Section 26 tidak ditemukan")

    next_section = next(
        (i for i in range(header + 1, len(lines))
         if "27. OPTIONAL PART COMPONENTS (3)" in lines[i]),
        None
    )
    if next_section is None:
        stop("Batas Section 27 tidak ditemukan")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+"
        r"(?:(#\d{2})\s+)?"
        r"([A-Z0-9_-]+)\s+"
        r"(.+?)\s+"
        r"(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    invalid = []

    for i in range(header + 1, next_section):
        line = lines[i]
        if not line.strip():
            continue

        match = pattern.match(line)
        if match:
            ref = int(match.group(1))
            marker = match.group(2)
            records.append({
                "ref": ref,
                "marker": marker,
                "number": match.group(3),
                "name": match.group(4).strip(),
                "qty_raw": match.group(5).strip(),
            })
        elif re.match(r"^\s*\d{1,3}\s+", line):
            invalid.append((i + 1, line.strip()))

    if invalid:
        stop(f"Ada baris tabel gagal diparse: {invalid[:5]}")

    return records, header + 1, next_section


def validate_source(records):
    refs = [r["ref"] for r in records]
    if len(records) != 100:
        stop(f"Jumlah REF bukan 100: {len(records)}")

    if refs != EXPECTED_REFS:
        stop("REF tidak berurutan atau tidak lengkap")

    counts = Counter(r["number"] for r in records)
    if len(counts) != 83:
        stop(f"PN unik bukan 83: {len(counts)}")

    for r in records:
        expected = EXPECTED.get(r["ref"])
        actual = (
            r["number"], r["name"],
            r["qty_raw"], r["marker"]
        )
        if actual != expected:
            stop(
                f"Data REF {r['ref']} berbeda dari validasi katalog.\n"
                f"Aktual: {actual}\n"
                f"Harus : {expected}"
            )

        raw = r["qty_raw"].strip("()")
        r["qty"] = float(raw) if "." in raw else int(raw)

    if set(EXPECTED) != set(refs):
        stop("EXPECTED_VALUES tidak cocok dengan REF sumber")

    print("Jumlah REF:", len(records))
    print("REF berurutan 1-100: VALID")
    print("PN unik:", len(counts))
    print("Marker:", [(r["ref"], r["marker"])
                      for r in records if r["marker"]])
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
    parts = con.execute(
        "SELECT COUNT(*) FROM parts WHERE machine_id=?",
        (MACHINE_ID,)
    ).fetchone()[0]

    components = con.execute(
        "SELECT COUNT(*) FROM components WHERE machine_id=?",
        (MACHINE_ID,)
    ).fetchone()[0]

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

        if not document:
            stop("Dokumen ID 136 tidak ditemukan")

        source_url = document["source_url"]
        if not source_url:
            stop("Source URL dokumen kosong")

        counts = get_counts(con)
        print("\nBaseline database:", counts)

        if counts != BASELINE:
            stop(f"Baseline harus {BASELINE}, aktual {counts}")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref
            FROM components
            WHERE machine_id=?
              AND (component_name=? OR catalog_ref=?)
        """, (MACHINE_ID, COMPONENT_NAME, CATALOG_REF)).fetchall()

        if existing:
            stop(f"Komponen Section 26 sudah ada: {[dict(x) for x in existing]}")

        before = snapshot(con)
        if len(before) != 13:
            stop("Jumlah komponen lama bukan 13")

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
            print("\nJika semua hasil sesuai, jalankan dengan --apply.")
            return

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        backup = Path(
            "database/garment-before-ams210en1510-section26-"
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
            "Official JUKI AMS-210EN Series Parts List, Section 26.",
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
            DIAGRAM_PAGE, IMAGE_DB_PATH, 100
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
        print("REF 1-100:", linked_refs == EXPECTED_REFS)
        print("Data part/quantity/marker: VALID")
        print("Komponen lama tidak berubah: VALID")
        print("Gambar:", IMAGE_DST)
        print("Ukuran gambar:", IMAGE_DST.stat().st_size, "bytes")

        con.commit()

        print("\n=== IMPOR SECTION 26 BERHASIL ===")
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
