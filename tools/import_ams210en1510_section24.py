import re
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
IMAGE = Path("static/component_images/ams210en_pdf47.png")

MACHINE_ID = 15
DOCUMENT_ID = 136
MODEL = "AMS-210EN-1510"

COMPONENT_NAME = "24. ACCESSORIE PARTS COMPONENTS"
CATALOG_REF = "24"
DIAGRAM_PAGE = 42
IMAGE_DB_PATH = "component_images/ams210en_pdf47.png"

BASELINE = (874, 16, 404)
TARGET = (900, 17, 430)
EXPECTED_REFS = list(range(1, 27))

EXPECTED_TEXT = """
1|☆|-|B1806-210-D00|BOBBIN|1
2|-|#02|EA-9500B01-00|CABLE BAND|1
3|-|#09|400-48664|HEAD_COVER|1
4|☆|#04|MDP-500B1402|NEEDLE DPX5#14-2|1
5|☆|#05|MDP-170B1802|NEEDLE DPZ17#18-2|1
6|☆|#06|MC-2005010-02|NEEDLE 134 #100-2|1
7|☆|#07|MC-3720011-02|NEEDLE SY3355 #110-2|1
8|-|-|229-33204|SCREW DRIVER SMALL|1
9|-|-|B9113-012-000|WRENCH (9X10)|1
10|-|-|B9140-372-000|HEXAGONAL WRENCH SMALL|1
11|-|-|400-32763|HEXAGONAL_DRIVER(1.5)|1
12|-|#08|131-60304|S SHAPED HOOK|2
13|-|#08|260-37903|CHAIN|1
14|-|#02|HX-0015000-0D|CABLE CLIP|1
15|-|#03|291-86403|EC DECLARATION|1
16|-|-|B9121-220-0A0|OILER (CONTAINING NO.2 OIL)|1
17|-|#02|229-32800|ACCESSORIE BAG|1
18|-|#02|PX-5000140-00|PLUG|2
19|-|-|229-33105|SCREW DRIVER MIDDLE|1
20|-|#01|262-34005|VINYL COVER|1
21|-|-|B1131-528-000|FELT|1
22|-|-|101-02200|THREAD GUIDE F|1
23|-|-|SM-6040860-TP|SCREW M4 L=8|1
24|-|-|B9101-490-000|DRIVER|1
25|-|-|229-32800|ACCESSORIE BAG|1
26|-|#03|CM-6001002-01|WEEE INFORMATION SHEET|1
"""

def stop(message):
    raise RuntimeError(message)

def expected_values():
    result = {}
    for line in EXPECTED_TEXT.strip().splitlines():
        ref, star, marker, number, name, qty = line.split("|", 5)
        note_parts = []
        if star == "☆":
            note_parts.append("☆")
        if marker != "-":
            note_parts.append(marker)
        result[int(ref)] = (
            number, name, qty,
            " ".join(note_parts) or None
        )
    return result

EXPECTED = expected_values()

def parse_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    section = next(
        (i for i, line in enumerate(lines)
         if "24. ACCESSORIE PARTS COMPONENTS" in line
         and i > 200),
        None
    )
    if section is None:
        stop("Judul Section 24 tidak ditemukan")

    header = next(
        (i for i in range(section, len(lines))
         if "REF.NO" in lines[i].upper()),
        None
    )
    if header is None:
        stop("Header REF.NO Section 24 tidak ditemukan")

    next_section = next(
        (i for i in range(header + 1, len(lines))
         if "25. OPTIONAL PART COMPONENTS (1)" in lines[i]),
        None
    )
    if next_section is None:
        stop("Batas Section 25 tidak ditemukan")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+"
        r"(☆)?\s*"
        r"(#\d{2})?\s+"
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
            records.append({
                "ref": int(match.group(1)),
                "star": bool(match.group(2)),
                "marker": match.group(3),
                "number": match.group(4),
                "name": match.group(5).strip(),
                "qty_raw": match.group(6).strip(),
            })
        elif re.match(r"^\s*\d{1,3}\s+", line):
            invalid.append((i + 1, line.strip()))

    if invalid:
        stop(f"Ada baris gagal parse: {invalid[:5]}")

    return records

def validate_source(records):
    refs = [r["ref"] for r in records]
    if refs != EXPECTED_REFS:
        stop(f"REF sumber tidak sesuai: {refs}")

    if len(records) != 26:
        stop(f"Jumlah REF bukan 26: {len(records)}")

    for r in records:
        raw = r["qty_raw"].strip("()")
        r["qty"] = float(raw) if "." in raw else int(raw)

        note_parts = []
        if r["star"]:
            note_parts.append("☆")
        if r["marker"]:
            note_parts.append(r["marker"])
        r["note"] = " ".join(note_parts) or None

        expected = EXPECTED[r["ref"]]
        actual = (
            r["number"], r["name"], r["qty_raw"], r["note"]
        )
        if actual != expected:
            stop(
                f"Data REF {r['ref']} tidak cocok.\n"
                f"Sumber: {actual}\n"
                f"Harapan: {expected}"
            )

    return records

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
        """, (MACHINE_ID,)).fetchone()[0]
    )

def old_snapshot(con):
    components = [
        tuple(r) for r in con.execute("""
            SELECT id, component_name, catalog_ref,
                   diagram_page, image_path
            FROM components
            WHERE machine_id=?
            ORDER BY id
        """, (MACHINE_ID,))
    ]
    relations = [
        tuple(r) for r in con.execute("""
            SELECT cp.component_id, cp.part_id,
                   cp.relation_type, cp.notes
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
            ORDER BY cp.component_id, cp.part_id
        """, (MACHINE_ID,))
    ]
    return components, relations

def main():
    if not TXT.is_file():
        stop(f"File teks tidak ditemukan: {TXT}")
    if not IMAGE.is_file() or IMAGE.stat().st_size == 0:
        stop(f"Gambar Section 24 tidak valid: {IMAGE}")

    records = validate_source(parse_source())

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        machine = con.execute("""
            SELECT id, model FROM machines WHERE id=?
        """, (MACHINE_ID,)).fetchone()

        if not machine or machine["model"] != MODEL:
            stop("Machine ID 15 tidak cocok dengan AMS-210EN-1510")

        document = con.execute("""
            SELECT id, source_url
            FROM documents
            WHERE id=? AND machine_id=?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

        if not document or not document["source_url"]:
            stop("Dokumen ID 136 atau source_url tidak valid")

        counts = get_counts(con)
        print("Baseline database:", counts)
        if counts != BASELINE:
            stop(f"Baseline harus {BASELINE}, aktual {counts}")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref, diagram_page
            FROM components
            WHERE machine_id=?
              AND (component_name=? OR
                   (catalog_ref=? AND diagram_page=?))
        """, (
            MACHINE_ID, COMPONENT_NAME,
            CATALOG_REF, DIAGRAM_PAGE
        )).fetchall()

        if existing:
            stop(f"Komponen Section 24 sudah ada: {[dict(x) for x in existing]}")

        old_parts = con.execute("""
            SELECT id FROM parts
            WHERE machine_id=? AND source_document_id=?
              AND notes=?
        """, (
            MACHINE_ID, DOCUMENT_ID,
            f"AMS-210EN-1510 section: {COMPONENT_NAME}"
        )).fetchall()

        if old_parts:
            stop("Ditemukan part staging Section 24; hentikan untuk audit manual")

        before = old_snapshot(con)

        print("REF tervalidasi:", len(records))
        print("REF dengan ☆:", [r["ref"] for r in records if r["star"]])
        print("REF dengan marker #:", [
            (r["ref"], r["marker"])
            for r in records if r["marker"]
        ])
        print("PN 229-32800:", [
            r["ref"] for r in records
            if r["number"] == "229-32800"
        ])
        print("Gambar:", IMAGE)
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
            return

        backup = Path(
            "database/garment-before-ams210en1510-section24-"
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
                notes, source_url, catalog_ref, diagram_page,
                image_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, COMPONENT_NAME, None, None,
            "Official JUKI AMS-210EN Series Parts List, Section 24.",
            document["source_url"], CATALOG_REF,
            DIAGRAM_PAGE, IMAGE_DB_PATH
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
                MACHINE_ID, DOCUMENT_ID, r["number"],
                r["name"], r["qty"], str(r["ref"]),
                r["note"], document["source_url"],
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

        inserted = con.execute("""
            SELECT p.catalog_ref, p.part_number, p.part_name,
                   p.quantity_raw, p.note, cp.notes,
                   cp.relation_type
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY CAST(p.catalog_ref AS INTEGER)
        """, (component_id,)).fetchall()

        expected_inserted = [
            (
                str(r["ref"]), r["number"], r["name"],
                r["qty_raw"], r["note"], f"REF {r['ref']}",
                "catalog_component_part"
            )
            for r in records
        ]

        actual_inserted = [
            (str(x[0]), *tuple(x)[1:])
            for x in inserted
        ]
        if actual_inserted != expected_inserted:
            print("\\n=== DIAGNOSTIK AUDIT INSERT ===")
            print("Jumlah aktual:", len(actual_inserted))
            print("Jumlah harapan:", len(expected_inserted))
            for i, (actual, expected) in enumerate(
                zip(actual_inserted, expected_inserted), 1
            ):
                if actual != expected:
                    print("REF/baris:", i)
                    print("AKTUAL  :", repr(actual))
                    print("HARAPAN :", repr(expected))
                    print("PER KOLOM:", [
                        (j, repr(a), repr(e))
                        for j, (a, e) in enumerate(zip(actual, expected), 1)
                        if a != e
                    ])
                    break
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

        new_counts = get_counts(con)
        if new_counts != TARGET:
            stop(f"Total database tidak sesuai: {new_counts}")

        after_components, after_relations = old_snapshot(con)

        after_components = [
            r for r in after_components if r[0] != component_id
        ]
        after_relations = [
            r for r in after_relations if r[0] != component_id
        ]

        if (after_components, after_relations) != before:
            stop("Komponen atau relasi lama berubah")

        image_check = con.execute("""
            SELECT image_path FROM components WHERE id=?
        """, (component_id,)).fetchone()

        if not image_check or image_check["image_path"] != IMAGE_DB_PATH:
            stop("Path gambar komponen tidak sesuai")

        con.commit()

        print("\n=== AUDIT SELESAI ===")
        print("Component ID:", component_id)
        print("Parts:", new_counts[0])
        print("Komponen:", new_counts[1])
        print("Relasi:", new_counts[2])
        print("REF 1-26:", linked_refs == EXPECTED_REFS)
        print("Tanda ☆ dan marker #:", "VALID")
        print("PN duplikat REF 17/25 tetap terpisah:", "VALID")
        print("Komponen dan relasi lama tidak berubah:", "VALID")
        print("Gambar:", IMAGE_DB_PATH)
        print("Backup:", backup)

    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nSTOP:", e)
        sys.exit(1)
