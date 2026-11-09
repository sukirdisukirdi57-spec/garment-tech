import re
import sqlite3
import sys
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
TEXT = Path("assets/documents/juki/ms1190-parts.txt")
IMAGE_DIR = Path("static/images/mechanisms/juki/ms1190")

MACHINE_ID = 14
DOCUMENT_ID = 134
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ms1190_1261/menu/ms_1190/pdf/partslist.pdf"
)

SECTIONS = [
    (1, "FRAME & MISCELLANEOUS COVER COMPONENTS", 1, 4, 5, 77),
    (2, "LOOPER THREAD GUIDE COMPONENTS", 3, 6, 7, 64),
    (5, "PRESSER BAR & LOWER SHAFT COMPONENTS", 9, 12, 13, 54),
    (6, "FEED MECHANISM COMPONENTS", 11, 14, 15, 64),
    (7, "KNEE LIFTER COMPONENTS", 13, 16, 17, 27),
    (8, "THREAD STAND COMPONENTS", 15, 18, 18, 1),
    (9, "OPTIONAL PARTS COMPONENTS (FOR MS-1190)", 16, 19, 19, 12),
]

PN_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)+$")
ROW_RE = re.compile(r"^\s*(\d+)\s+(.*?)\s*$")


def stop(message):
    raise RuntimeError(message)


def parse_page(page_text, expected_count, section):
    records = []
    for line_no, line in enumerate(page_text.splitlines(), 1):
        m = ROW_RE.match(line)
        if not m:
            continue

        ref = int(m.group(1))
        rest = m.group(2).split()
        pn_positions = [i for i, token in enumerate(rest) if PN_RE.fullmatch(token)]
        if not pn_positions:
            continue

        # PART NO berada sebelum DESCRIPTION; kata seperti O-RING
        # dan E-RING di deskripsi juga dapat cocok dengan pola PN.
        pos = pn_positions[0]
        if pos == len(rest) - 1:
            continue

        before = rest[:pos]
        pn = rest[pos]
        after = rest[pos + 1:]

        qty_raw = after[-1]
        if not re.fullmatch(r"\(?\d+\)?", qty_raw):
            continue

        name_tokens = after[:-1]
        if not name_tokens:
            continue

        marker = " ".join(before).strip()
        name = " ".join(name_tokens).strip()
        qty = int(qty_raw.strip("()"))

        records.append({
            "ref": ref,
            "marker": marker,
            "number": pn,
            "name": name,
            "qty": qty,
            "qty_raw": qty_raw,
            "line_no": line_no,
        })

    by_ref = {}
    for r in records:
        if r["ref"] in by_ref:
            stop(f"Section {section}: REF duplikat {r['ref']}")
        by_ref[r["ref"]] = r

    expected_refs = set(range(1, expected_count + 1))
    if set(by_ref) != expected_refs:
        missing = sorted(expected_refs - set(by_ref))
        extra = sorted(set(by_ref) - expected_refs)
        stop(
            f"Section {section}: REF tidak cocok; "
            f"missing={missing}, extra={extra}, parsed={len(records)}"
        )

    return [by_ref[n] for n in range(1, expected_count + 1)]


def main():
    apply = "--apply" in sys.argv[1:]
    if not TEXT.exists():
        stop(f"Teks katalog tidak ditemukan: {TEXT}")

    pages = TEXT.read_text(errors="replace").split("\f")
    if len(pages) < 19:
        stop(f"Jumlah halaman teks tidak cukup: {len(pages)}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id=?", (MACHINE_ID,)
        ).fetchone()
        if not machine or machine["model"] != "MS-1190":
            stop(f"Identitas mesin tidak cocok: {dict(machine) if machine else None}")

        doc = con.execute("""
            SELECT id, machine_id, title, source_url
            FROM documents WHERE id=?
        """, (DOCUMENT_ID,)).fetchone()
        if not doc or doc["machine_id"] != MACHINE_ID:
            stop(f"Dokumen {DOCUMENT_ID} tidak cocok dengan mesin {MACHINE_ID}")

        counts = {
            "parts": con.execute(
                "SELECT COUNT(*) FROM parts WHERE machine_id=?", (MACHINE_ID,)
            ).fetchone()[0],
            "components": con.execute(
                "SELECT COUNT(*) FROM components WHERE machine_id=?", (MACHINE_ID,)
            ).fetchone()[0],
            "relations": con.execute("""
                SELECT COUNT(*) FROM component_parts cp
                JOIN components c ON c.id=cp.component_id
                WHERE c.machine_id=?
            """, (MACHINE_ID,)).fetchone()[0],
        }
        print("MESIN:", dict(machine))
        print("DOKUMEN:", dict(doc))
        print("KONDISI AWAL:", counts)

        if any(counts.values()):
            stop("Mesin sudah memiliki data parts/components/relations; tidak ditimpa.")

        total = 0
        plan = []
        for sec, name, printed, diagram_pdf, table_pdf, expected in SECTIONS:
            image = IMAGE_DIR / f"pdf-page-{diagram_pdf}.jpg"
            if not image.is_file() or image.stat().st_size < 10000:
                stop(f"Gambar section {sec} tidak valid: {image}")

            records = parse_page(pages[table_pdf - 1], expected, sec)
            total += len(records)
            plan.append((sec, name, printed, diagram_pdf, image, records))

            print(
                f"Section {sec}: {name} | halaman katalog {printed} "
                f"| gambar PDF {diagram_pdf} | REF {len(records)}"
            )
            print(
                "  awal:", records[0]["ref"], records[0]["number"],
                records[0]["name"], records[0]["qty_raw"]
            )
            print(
                "  akhir:", records[-1]["ref"], records[-1]["number"],
                records[-1]["name"], records[-1]["qty_raw"]
            )
            repeated = {}
            for r in records:
                repeated.setdefault(r["number"], []).append(r["ref"])
            repeated = {k: v for k, v in repeated.items() if len(v) > 1}
            if repeated:
                print("  PN berulang dipertahankan:", repeated)

        if total != 299:
            stop(f"Total REF salah: {total}, target 299")

        print("\\nTOTAL SECTION:", len(plan))
        print("TOTAL REF:", total)
        print("GAMBAR:", sum(1 for x in plan if x[4].is_file()), "/", len(plan))

        if not apply:
            print("DRY-RUN OK: database dan file gambar tidak diubah.")
            print("Untuk menerapkan: python tools/import_ms1190_sections.py --apply")
            return

        backup = Path(
            "database/garment-before-ms1190-import-"
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

        copied_images = []
        try:
            con.execute("BEGIN IMMEDIATE")

            for sec, name, printed, diagram_pdf, image, records in plan:
                image_db_path = (
                    f"images/mechanisms/juki/ms1190/"
                    f"pdf-page-{diagram_pdf}.jpg"
                )

                cur = con.execute("""
                    INSERT INTO components (
                        machine_id, component_name, location, function,
                        notes, source_url, catalog_ref, diagram_page, image_path
                    )
                    VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID,
                    name,
                    f"Official JUKI MS-1190 Parts List, Section {sec}.",
                    SOURCE_URL,
                    str(sec),
                    printed,
                    image_db_path,
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
                        MACHINE_ID,
                        DOCUMENT_ID,
                        r["number"],
                        r["name"],
                        r["qty"],
                        str(r["ref"]),
                        r["marker"],
                        SOURCE_URL,
                        f"MS-1190 section: {name}",
                        r["qty_raw"],
                    ))
                    part_id = cur.lastrowid

                    con.execute("""
                        INSERT INTO component_parts (
                            component_id, part_id, relation_type, notes
                        )
                        VALUES (?, ?, 'catalog_component_part', ?)
                    """, (component_id, part_id, f"REF {r['ref']}"))

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
            }

            if actual != {"parts": 299, "components": 7, "relations": 299}:
                stop(f"Jumlah hasil impor salah: {actual}")

            audit = con.execute("""
                SELECT c.component_name, c.catalog_ref, c.diagram_page,
                       c.image_path, COUNT(cp.part_id) AS relasi
                FROM components c
                LEFT JOIN component_parts cp ON cp.component_id=c.id
                WHERE c.machine_id=?
                GROUP BY c.id
                ORDER BY CAST(c.catalog_ref AS INTEGER)
            """, (MACHINE_ID,)).fetchall()

            if len(audit) != 7 or any(row["relasi"] == 0 for row in audit):
                stop("Audit komponen/relasi gagal.")

            linked = con.execute("""
                SELECT COUNT(*)
                FROM component_parts cp
                JOIN components c ON c.id=cp.component_id
                JOIN parts p ON p.id=cp.part_id
                WHERE c.machine_id=? AND p.machine_id=?
                  AND cp.relation_type='catalog_component_part'
            """, (MACHINE_ID, MACHINE_ID)).fetchone()[0]

            if linked != 299:
                stop(f"Relasi valid lintas mesin salah: {linked}")

            con.commit()

            print("\\nAPPLY BERHASIL")
            print("HASIL:", actual)
            for row in audit:
                print(dict(row))
            print("Relasi valid:", linked)
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
        print("\nGAGAL:", exc)
        sys.exit(1)
