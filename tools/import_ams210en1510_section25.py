import re
import sys
import sqlite3
import shutil

from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

IMAGE_DIR = Path("static/component_images")
IMAGE_NAME = "ams210en1510_optional_part_components_1.png"
IMAGE_DST = IMAGE_DIR / IMAGE_NAME
IMAGE_DB_PATH = "component_images/" + IMAGE_NAME

MACHINE_ID = 15
DOCUMENT_ID = 136
MODEL = "AMS-210EN-1510"

COMPONENT_NAME = "25. OPTIONAL PART COMPONENTS (1)"
CATALOG_REF = "25"
DIAGRAM_PAGE = 43

FIRST_PART_ID = 14824
LAST_PART_ID = 14916
WIPER_COMPONENT_ID = 696

BASELINE = (874, 15, 311)
TARGET = (874, 16, 404)
EXPECTED_REFS = list(range(1, 94))
STAGING_NOTES = "AMS-210EN catalog staging; section 25"


def stop(message):
    raise RuntimeError(message)


def parse_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    section = next(
        (i for i, line in enumerate(lines)
         if "25. OPTIONAL PART COMPONENTS (1)" in line
         and i > 200),
        None
    )
    if section is None:
        stop("Judul Section 25 tidak ditemukan")

    header = next(
        (i for i in range(section, len(lines))
         if "REF.NO" in lines[i].upper()),
        None
    )
    if header is None:
        stop("Header REF.NO Section 25 tidak ditemukan")

    next_section = next(
        (i for i in range(header + 1, len(lines))
         if "26. OPTIONAL PART COMPONENTS (2)" in lines[i]),
        None
    )
    if next_section is None:
        stop("Batas Section 26 tidak ditemukan")

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

    if len(records) != 93:
        stop(f"Jumlah REF bukan 93: {len(records)}")

    refs = [r["ref"] for r in records]
    if refs != EXPECTED_REFS:
        stop("REF sumber tidak berurutan 1-93")

    for r in records:
        raw = r["qty_raw"].strip("()")
        r["qty"] = float(raw) if "." in raw else int(raw)

    print("Jumlah REF sumber:", len(records))
    print("REF berurutan 1-93: VALID")
    print("Marker:", [
        (r["ref"], r["marker"])
        for r in records if r["marker"]
    ])

    return records, header + 1, next_section


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


def component_snapshot(con):
    rows = con.execute("""
        SELECT c.id, c.component_name, c.catalog_ref,
               c.diagram_page, c.image_path,
               COUNT(cp.part_id)
        FROM components c
        LEFT JOIN component_parts cp ON cp.component_id=c.id
        WHERE c.machine_id=?
        GROUP BY c.id
        ORDER BY c.id
    """, (MACHINE_ID,)).fetchall()

    return [tuple(r) for r in rows]


def main():
    for path in (DB, TXT, IMAGE_DST):
        if not path.is_file():
            stop(f"File tidak ditemukan: {path}")

    if IMAGE_DST.stat().st_size == 0:
        stop("Gambar Section 25 kosong")

    records, header_line, end_line = parse_source()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

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
        print("\\nBaseline database:", counts)

        if counts != BASELINE:
            stop(f"Baseline harus {BASELINE}, aktual {counts}")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref, diagram_page
            FROM components
            WHERE machine_id=?
              AND (component_name=? OR catalog_ref=?)
        """, (MACHINE_ID, COMPONENT_NAME, CATALOG_REF)).fetchall()

        if existing:
            stop(
                "Komponen Section 25 sudah ada: "
                + str([dict(x) for x in existing])
            )

        parts = con.execute("""
            SELECT id, source_document_id, part_number,
                   part_name, quantity, quantity_raw,
                   note, notes
            FROM parts
            WHERE machine_id=?
              AND id BETWEEN ? AND ?
            ORDER BY id
        """, (MACHINE_ID, FIRST_PART_ID, LAST_PART_ID)).fetchall()

        if len(parts) != 93:
            stop(f"Jumlah part target bukan 93: {len(parts)}")

        if [p["id"] for p in parts] != list(
            range(FIRST_PART_ID, LAST_PART_ID + 1)
        ):
            stop("ID part target tidak berurutan")

        mismatches = []

        for r, p in zip(records, parts):
            expected_note = r["marker"] or "COMMON"
            actual_core = (
                p["part_number"],
                p["part_name"],
                p["quantity_raw"]
            )
            expected_core = (
                r["number"],
                r["name"],
                r["qty_raw"]
            )

            if actual_core != expected_core:
                mismatches.append(
                    (r["ref"], p["id"], expected_core, actual_core)
                )

            if p["source_document_id"] != DOCUMENT_ID:
                mismatches.append(
                    (r["ref"], p["id"], "document 136",
                     p["source_document_id"])
                )

            if p["note"] != expected_note:
                mismatches.append(
                    (r["ref"], p["id"], expected_note, p["note"])
                )

            if p["notes"] != STAGING_NOTES:
                mismatches.append(
                    (r["ref"], p["id"], STAGING_NOTES, p["notes"])
                )

            if p["quantity"] is None:
                # Beberapa part desimal lama hanya menyimpan quantity_raw.
                if "." not in r["qty_raw"]:
                    mismatches.append(
                        (r["ref"], p["id"], r["qty"], p["quantity"])
                    )
            elif float(p["quantity"]) != float(r["qty"]):
                mismatches.append(
                    (r["ref"], p["id"], r["qty"], p["quantity"])
                )

        if mismatches:
            stop(
                "Validasi part database gagal: "
                + str(mismatches[:10])
            )

        wiper = con.execute("""
            SELECT id, component_name, catalog_ref, diagram_page
            FROM components
            WHERE id=? AND machine_id=?
        """, (WIPER_COMPONENT_ID, MACHINE_ID)).fetchone()

        if not wiper or wiper["component_name"] != "WIPER ASM.":
            stop("Komponen WIPER ID 696 tidak sesuai")

        old_wiper_relations = con.execute("""
            SELECT cp.part_id, cp.relation_type, cp.notes
            FROM component_parts cp
            WHERE cp.component_id=?
            ORDER BY cp.part_id
        """, (WIPER_COMPONENT_ID,)).fetchall()

        expected_wiper = [
            (FIRST_PART_ID + ref - 1,
             "REF " + str(ref))
            for ref in range(51, 68)
        ]

        actual_wiper = [
            (x["part_id"], x["notes"])
            for x in old_wiper_relations
        ]

        if len(old_wiper_relations) != 17:
            stop("Jumlah relasi WIPER lama bukan 17")

        if actual_wiper != expected_wiper:
            stop("Relasi WIPER lama tidak sesuai REF 51-67")

        linked = con.execute("""
            SELECT p.id, cp.component_id, cp.notes
            FROM parts p
            JOIN component_parts cp ON cp.part_id=p.id
            WHERE p.machine_id=?
              AND p.id BETWEEN ? AND ?
            ORDER BY p.id
        """, (MACHINE_ID, FIRST_PART_ID, LAST_PART_ID)).fetchall()

        if len(linked) != 17:
            stop(
                "Jumlah relasi awal pada 93 part bukan 17: "
                + str(len(linked))
            )

        if any(x["component_id"] != WIPER_COMPONENT_ID for x in linked):
            stop("Ada relasi lama di luar komponen WIPER")

        before = component_snapshot(con)

        if len(before) != 15:
            stop("Jumlah komponen awal bukan 15")

        print("Part database:", len(parts))
        print("PN/nama/quantity_raw: COCOK 93/93")
        print("Marker dan staging notes: VALID")
        print("Relasi WIPER REF 51-67: VALID")
        print("Relasi lama pada target:", len(linked))
        print("Relasi yang akan ditambahkan: 93")
        print("Komponen:", COMPONENT_NAME)
        print("Halaman katalog:", DIAGRAM_PAGE)
        print("Gambar:", IMAGE_DST)
        print("Ukuran gambar:", IMAGE_DST.stat().st_size, "bytes")
        print("Batas teks sumber:", header_line, "sampai", end_line)

        if "--apply" not in sys.argv:
            print("\\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Target parts    :", TARGET[0])
            print("Target komponen :", TARGET[1])
            print("Target relasi   :", TARGET[2])
            print("Jalankan dengan --apply jika hasil sudah sesuai.")
            return

        backup = Path(
            "database/garment-before-ams210en1510-section25-"
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

        print("\\nBACKUP:", backup)

        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components (
                machine_id, component_name, location, function,
                notes, source_url, catalog_ref, diagram_page, image_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, COMPONENT_NAME, None, None,
            "Official JUKI AMS-210EN Series Parts List, Section 25.",
            source_url, CATALOG_REF, DIAGRAM_PAGE, IMAGE_DB_PATH
        ))

        component_id = cur.lastrowid

        for r, p in zip(records, parts):
            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, ?, ?)
            """, (
                component_id, p["id"],
                "catalog_component_part", f"REF {r['ref']}"
            ))

        new_counts = get_counts(con)

        inserted = con.execute("""
            SELECT p.id, p.part_number, p.part_name,
                   p.quantity_raw, cp.notes, cp.relation_type
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY p.id
        """, (component_id,)).fetchall()

        expected_inserted = [
            (
                p["id"], r["number"], r["name"],
                r["qty_raw"], f"REF {r['ref']}",
                "catalog_component_part"
            )
            for r, p in zip(records, parts)
        ]

        if [tuple(x) for x in inserted] != expected_inserted:
            stop("Audit 93 relasi hasil insert gagal")

        if new_counts != TARGET:
            stop(f"Target jumlah database salah: {new_counts}")

        after = component_snapshot(con)
        expected_snapshot = before + [(
            component_id, COMPONENT_NAME, CATALOG_REF,
            DIAGRAM_PAGE, IMAGE_DB_PATH, 93
        )]

        if after != expected_snapshot:
            stop("Snapshot komponen lama atau komponen baru tidak sesuai")

        wiper_after = con.execute("""
            SELECT cp.part_id, cp.relation_type, cp.notes
            FROM component_parts cp
            WHERE cp.component_id=?
            ORDER BY cp.part_id
        """, (WIPER_COMPONENT_ID,)).fetchall()

        if [tuple(x) for x in wiper_after] != [
            tuple(x) for x in old_wiper_relations
        ]:
            stop("Relasi WIPER berubah")

        con.commit()

        print("\\n=== IMPOR SECTION 25 BERHASIL ===")
        print("Component ID:", component_id)
        print("Nama:", COMPONENT_NAME)
        print("REF:", len(inserted))
        print("Parts/Components/Relations:", new_counts)
        print("Relasi WIPER lama tetap:", len(wiper_after))
        print("Gambar:", IMAGE_DST)
        print("Backup:", backup)

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\\nGAGAL:", exc)
        sys.exit(1)
