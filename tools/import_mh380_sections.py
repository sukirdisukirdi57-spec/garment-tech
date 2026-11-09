import re
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TEXT = Path("assets/documents/juki/mh380-parts.txt")
IMAGE_DIR = Path("static/images/mechanisms/juki/mh380")

MACHINE_ID = 13
DOCUMENT_ID = 131
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "mh380_480/menu/mh380%2C382/pdf/partslist.pdf"
)

SECTIONS = [
    (1, "MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS", 1, 4, 5, 76),
    (2, "MAIN SHAFT & NEEDLE BAR COMPONENTS", 3, 6, 7, 46),
    (3, "PRESSER BAR, UPRIGHT SHAFT & LOWER SHAFT COMPONENTS", 5, 8, 9, 63),
    (4, "FEED MECHANISM COMPONENTS (1)", 7, 10, 11, 64),
    (5, "FEED MECHANISM COMPONENTS (2)", 9, 12, 13, 45),
    (6, "LOOPER & NEEDLE GUARD COMPONENTS", 11, 14, 15, 56),
    (7, "THREAD TENSION CONTROLLER COMPONENTS", 13, 16, 17, 66),
    (8, "OIL LUBRICATION MECHANISM COMPONENTS", 15, 18, 18, 35),
    (9, "OIL RESERVOIR & KNEE LIFTER COMPONENTS", 16, 19, 19, 26),
    (10, "THREAD STAND COMPONENTS", 17, 20, 21, 29),
    (11, "SILICON OIL LUBRICANT & BELT COVER COMPONENTS", 19, 22, 23, 27),
]

ROW_RE = re.compile(
    r"^\s*(\d{1,3})\s+"
    r"(.*?)\s+"
    r"([A-Z0-9]+(?:-[A-Z0-9]+)+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)


def stop(message):
    raise RuntimeError(message)


def parse_page(page_text, expected_count, section):
    records = []
    for line_no, line in enumerate(page_text.splitlines(), 1):
        if not re.match(r"^\s*\d{1,3}\s+", line):
            continue

        m = ROW_RE.match(line)
        if not m:
            stop(
                f"Section {section}, baris {line_no}: "
                f"gagal parse: {line!r}"
            )

        ref, prefix, pn, name, qty_raw = m.groups()
        marker = " ".join(re.findall(r"＊|#\d+", prefix))
        qty_value = qty_raw.strip("()")

        records.append({
            "ref": int(ref),
            "marker": marker,
            "number": pn,
            "name": name.strip(),
            "qty_raw": qty_raw,
            "qty": (int(float(qty_value)) if float(qty_value).is_integer() else None),
            "line_no": line_no,
            "original": line.rstrip(),
        })

    refs = [r["ref"] for r in records]
    expected_refs = list(range(1, expected_count + 1))
    if refs != expected_refs:
        stop(
            f"Section {section}: REF tidak cocok; "
            f"parsed={len(refs)}, expected={expected_count}, refs={refs}"
        )

    return records


def main():
    apply = "--apply" in sys.argv[1:]
    if not TEXT.is_file():
        stop(f"Teks katalog tidak ditemukan: {TEXT}")

    pages = TEXT.read_text(errors="replace").split("\f")
    if len(pages) < 23:
        stop(f"Halaman teks tidak cukup: {len(pages)}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id=?",
            (MACHINE_ID,)
        ).fetchone()
        if not machine or machine["model"] != "MH-380":
            stop(f"Identitas mesin tidak cocok: {dict(machine) if machine else None}")

        doc = con.execute("""
            SELECT id, machine_id, title, source_url
            FROM documents WHERE id=?
        """, (DOCUMENT_ID,)).fetchone()
        if not doc or doc["machine_id"] != MACHINE_ID:
            stop("Dokumen Parts List tidak cocok dengan MH-380")

        counts = {
            "parts": con.execute(
                "SELECT COUNT(*) FROM parts WHERE machine_id=?",
                (MACHINE_ID,)
            ).fetchone()[0],
            "components": con.execute(
                "SELECT COUNT(*) FROM components WHERE machine_id=?",
                (MACHINE_ID,)
            ).fetchone()[0],
            "relations": con.execute("""
                SELECT COUNT(*) FROM component_parts cp
                JOIN components c ON c.id=cp.component_id
                WHERE c.machine_id=?
            """, (MACHINE_ID,)).fetchone()[0],
            "occurrences": con.execute(
                "SELECT COUNT(*) FROM catalog_occurrences WHERE machine_id=?",
                (MACHINE_ID,)
            ).fetchone()[0],
            "gauge_maps": con.execute(
                "SELECT COUNT(*) FROM catalog_gauge_maps WHERE machine_id=?",
                (MACHINE_ID,)
            ).fetchone()[0],
        }

        print("MESIN:", dict(machine))
        print("DOKUMEN:", dict(doc))
        print("KONDISI AWAL:", counts)

        if any(counts.values()):
            stop("Data MH-380 tidak kosong; tidak ditimpa.")

        plan = []
        total = 0
        for sec, name, printed, diagram_pdf, table_pdf, expected in SECTIONS:
            image = IMAGE_DIR / f"pdf-page-{diagram_pdf}.jpg"
            if not image.is_file() or image.stat().st_size < 10000:
                stop(f"Gambar section {sec} tidak valid: {image}")

            records = parse_page(
                pages[table_pdf - 1], expected, sec
            )
            plan.append((sec, name, printed, diagram_pdf, table_pdf, image, records))
            total += len(records)

            print(
                f"Section {sec:02}: {name} | katalog p.{printed} "
                f"| gambar PDF {diagram_pdf} | REF {len(records)}"
            )
            print("  AWAL:", records[0])
            print("  AKHIR:", records[-1])

        if total != 533:
            stop(f"Total REF salah: {total}, target 533")

        print("\nTOTAL SECTION:", len(plan))
        print("TOTAL REF:", total)
        print("GAMBAR VALID:", len(plan), "/", len(plan))

        if not apply:
            print("DRY-RUN OK: database tidak diubah.")
            print("Untuk menerapkan: python tools/import_mh380_sections.py --apply")
            return

        backup = Path(
            "database/garment-before-mh380-import-"
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
        print("BACKUP:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")

            for sec, name, printed, diagram_pdf, table_pdf, image, records in plan:
                image_db_path = (
                    f"images/mechanisms/juki/mh380/"
                    f"pdf-page-{diagram_pdf}.jpg"
                )

                cur = con.execute("""
                    INSERT INTO components (
                        machine_id, component_name, location, function,
                        notes, source_url, catalog_ref, diagram_page, image_path
                    )
                    VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID, name,
                    f"Official JUKI MH-380 Parts List, Section {sec}.",
                    SOURCE_URL, str(sec), printed, image_db_path,
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
                        r["marker"], SOURCE_URL,
                        f"MH-380 Section {sec}: {name}",
                        r["qty_raw"],
                    ))
                    part_id = cur.lastrowid

                    con.execute("""
                        INSERT INTO component_parts (
                            component_id, part_id, relation_type, notes
                        )
                        VALUES (?, ?, 'catalog_component_part', ?)
                    """, (component_id, part_id, f"REF {r['ref']}"))

                    con.execute("""
                        INSERT INTO catalog_occurrences (
                            machine_id, source_document_id, pdf_page,
                            catalog_ref, marker, part_number, part_name,
                            quantity_raw, catalog_line_original, source_url
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        MACHINE_ID, DOCUMENT_ID, table_pdf,
                        str(r["ref"]), r["marker"], r["number"],
                        r["name"], r["qty_raw"], r["original"],
                        SOURCE_URL,
                    ))

            actual = {
                "parts": con.execute(
                    "SELECT COUNT(*) FROM parts WHERE machine_id=?",
                    (MACHINE_ID,)
                ).fetchone()[0],
                "components": con.execute(
                    "SELECT COUNT(*) FROM components WHERE machine_id=?",
                    (MACHINE_ID,)
                ).fetchone()[0],
                "relations": con.execute("""
                    SELECT COUNT(*) FROM component_parts cp
                    JOIN components c ON c.id=cp.component_id
                    WHERE c.machine_id=?
                """, (MACHINE_ID,)).fetchone()[0],
                "occurrences": con.execute(
                    "SELECT COUNT(*) FROM catalog_occurrences WHERE machine_id=?",
                    (MACHINE_ID,)
                ).fetchone()[0],
            }

            expected = {
                "parts": 533, "components": 11,
                "relations": 533, "occurrences": 533,
            }
            if actual != expected:
                stop(f"Hasil impor salah: {actual}, target {expected}")

            invalid = con.execute("""
                SELECT COUNT(*)
                FROM component_parts cp
                JOIN components c ON c.id=cp.component_id
                JOIN parts p ON p.id=cp.part_id
                WHERE c.machine_id=? AND (
                    p.machine_id != c.machine_id
                    OR cp.relation_type != 'catalog_component_part'
                )
            """, (MACHINE_ID,)).fetchone()[0]
            if invalid:
                stop(f"Relasi tidak valid: {invalid}")

            con.commit()
            print("\nAPPLY BERHASIL:", actual)
            print("BACKUP:", backup)

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nGAGAL:", exc)
        sys.exit(1)
