import re
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict


DB = Path("database/garment.db")
TXT = Path("tmp/ddl8700-partslist.txt")

MACHINE_ID = 3
DOCUMENT_ID = 5
MODEL = "DDL-8700"

SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/"
    "manual_j/ddl8700/menu/ddl8700/pdf/partslist.pdf"
)

BASELINE = (276, 25, 10)
TARGET = (429, 12, 429)

# section, official title, diagram page, table page, REF count
SECTIONS = [
    (1, "MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS", 4, 5, 53),
    (2, "MAIN SHAFT & THREAD TAKE-UP LEVER COMPONENTS", 6, 7, 37),
    (3, "NEEDLE BAR, UPRIGHT SHAFT & HOOK DRIVING SHAFT COMPONENTS", 8, 9, 42),
    (4, "HAND LIFTER COMPONENTS", 10, 11, 35),
    (5, "FEED MECHANISM COMPONENTS", 12, 13, 68),
    (6, "OIL LUBRICATION COMPONENTS", 14, 15, 26),
    (7, "OIL RESERVOIR COMPONENTS", 16, 17, 27),
    (8, "BELT COVER & BOBBIN COMPONENTS", 18, 18, 31),
    (9, "THREAD STAND COMPONENTS", 19, 19, 24),
    (10, "EXCLUSIVE PARTS FOR DDL-8700H", 20, 20, 22),
    (11, "EXCLUSIVE PARTS FOR DDL-8700A", 21, 21, 10),
    (12, "EXCLUSIVE PARTS FOR DDL-8700L", 22, 23, 54),
]

PATTERN = re.compile(
    r"^\s*(\d+)\s+"
    r"(?:(#\d+|[#＊*])\s+)?"
    r"([A-Z0-9]+(?:-[A-Z0-9]+)+)\s{2,}"
    r"(.+?)\s{2,}"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)


def stop(message):
    raise RuntimeError(message)


def parse_source():
    if not TXT.is_file():
        stop(f"Teks katalog tidak ditemukan: {TXT}")

    pages = TXT.read_text(
        encoding="utf-8",
        errors="replace"
    ).split("\f")

    records = []

    for section, title, diagram_page, table_page, expected in SECTIONS:
        if table_page > len(pages):
            stop(f"Halaman tabel {table_page} tidak tersedia")

        page_records = []

        for line in pages[table_page - 1].splitlines():
            m = PATTERN.match(line)
            if not m:
                continue

            ref = int(m.group(1))
            marker = m.group(2)
            number = m.group(3)
            name = m.group(4).strip()
            qty_raw = m.group(5).strip()

            raw_qty = qty_raw.strip("()")
            qty = float(raw_qty) if "." in raw_qty else int(raw_qty)

            page_records.append({
                "section": section,
                "title": title,
                "diagram_page": diagram_page,
                "table_page": table_page,
                "ref": ref,
                "marker": marker,
                "number": number,
                "name": name,
                "qty": qty,
                "qty_raw": qty_raw,
            })

        refs = [r["ref"] for r in page_records]
        expected_refs = list(range(1, expected + 1))

        if len(page_records) != expected:
            stop(
                f"Section {section}: jumlah REF {len(page_records)}, "
                f"seharusnya {expected}"
            )

        if refs != expected_refs:
            stop(f"Section {section}: REF tidak lengkap/berurutan: {refs}")

        records.extend(page_records)

        print(
            f"Section {section:02d}: {len(page_records):2d} REF | "
            f"diagram p.{diagram_page} | tabel p.{table_page}"
        )

    if len(records) != 429:
        stop(f"Total REF bukan 429: {len(records)}")

    return records, pages


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


def old_component_snapshot(con):
    return con.execute("""
        SELECT
            id, machine_id, component_name, part_number,
            location, function, notes, image_path,
            source_url, catalog_ref, diagram_page
        FROM components
        WHERE machine_id = ?
        ORDER BY id
    """, (MACHINE_ID,)).fetchall()


def old_relation_snapshot(con, component_ids):
    if not component_ids:
        return []

    marks = ",".join("?" for _ in component_ids)

    return con.execute(f"""
        SELECT id, component_id, part_id, relation_type, notes
        FROM component_parts
        WHERE component_id IN ({marks})
        ORDER BY id
    """, component_ids).fetchall()


def validate_database(con, records):
    machine = con.execute("""
        SELECT id, model FROM machines WHERE id = ?
    """, (MACHINE_ID,)).fetchone()

    if not machine or machine["model"] != MODEL:
        stop("Machine ID 3 tidak cocok dengan DDL-8700")

    document = con.execute("""
        SELECT id, machine_id, title
        FROM documents
        WHERE id = ? AND machine_id = ?
    """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

    if not document:
        stop("Dokumen Parts List ID 5 tidak cocok dengan mesin 3")

    counts = get_counts(con)
    print("\nBaseline database:", counts)

    if counts != BASELINE:
        stop(f"Baseline harus {BASELINE}, aktual {counts}")

    wrong_source = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id = ?
          AND (source_document_id IS NULL OR source_document_id != ?)
    """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

    if wrong_source:
        stop(f"Ada {wrong_source} part dengan dokumen sumber berbeda")

    old_parts = con.execute("""
        SELECT id, part_number, part_name
        FROM parts
        WHERE machine_id = ?
        ORDER BY id
    """, (MACHINE_ID,)).fetchall()

    if len({r["part_number"] for r in old_parts}) != len(old_parts):
        stop("Nomor part lama tidak unik; pemetaan otomatis dibatalkan")

    catalog_by_number = defaultdict(list)
    for r in records:
        catalog_by_number[r["number"]].append(r)

    used = set()

    for old in old_parts:
        candidates = catalog_by_number.get(old["part_number"], [])

        match = next(
            (
                r for r in candidates
                if r["name"] == old["part_name"]
                and (r["section"], r["ref"]) not in used
            ),
            None
        )

        if not match:
            stop(
                "Part lama tidak memiliki pasangan nama dan nomor "
                f"yang persis di katalog: ID {old['id']} "
                f"{old['part_number']} / {old['part_name']}"
            )

        used.add((match["section"], match["ref"]))

    titles = [s[1] for s in SECTIONS]
    marks = ",".join("?" for _ in titles)

    existing_titles = con.execute(f"""
        SELECT id, component_name
        FROM components
        WHERE machine_id = ?
          AND component_name IN ({marks})
    """, (MACHINE_ID, *titles)).fetchall()

    if existing_titles:
        stop(f"Judul komponen resmi sudah ada: {existing_titles}")

    old_components = old_component_snapshot(con)

    if len(old_components) != 25:
        stop("Jumlah komponen lama bukan 25")

    old_ids = [r["id"] for r in old_components]
    old_relations = old_relation_snapshot(con, old_ids)

    if len(old_relations) != 10:
        stop("Jumlah relasi lama bukan 10")

    return old_components, old_relations


def main():
    apply = "--apply" in sys.argv

    unknown = [
        arg for arg in sys.argv[1:]
        if arg != "--apply"
    ]
    if unknown:
        stop(f"Argumen tidak dikenal: {unknown}")

    if not DB.is_file():
        stop(f"Database tidak ditemukan: {DB}")

    records, pages = parse_source()

    duplicates = Counter(r["number"] for r in records)
    duplicates = {
        number: count
        for number, count in duplicates.items()
        if count > 1
    }

    print("\nTotal REF:", len(records))
    print("Nomor part unik:", len(set(r["number"] for r in records)))
    print("Nomor part berulang:", len(duplicates))
    print("Kemunculan ekstra:", sum(v - 1 for v in duplicates.values()))

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        old_components, old_relations = validate_database(con, records)

        old_parts = con.execute("""
            SELECT id, part_number, part_name
            FROM parts
            WHERE machine_id = ?
            ORDER BY id
        """, (MACHINE_ID,)).fetchall()

        old_by_number = {
            r["part_number"]: r
            for r in old_parts
        }

        used_old_ids = set()
        reuse_count = 0

        for r in records:
            old = old_by_number.get(r["number"])

            if old and old["id"] not in used_old_ids:
                if old["part_name"] != r["name"]:
                    continue
                used_old_ids.add(old["id"])
                reuse_count += 1

        new_parts = len(records) - reuse_count

        if reuse_count != 276 or new_parts != 153:
            stop(
                f"Pemetaan part tidak sesuai: reuse={reuse_count}, "
                f"baru={new_parts}"
            )

        print("\n=== RENCANA MIGRASI ===")
        print("Part lama digunakan kembali:", reuse_count)
        print("Part baru:", new_parts)
        print("Komponen baru:", len(SECTIONS))
        print("Komponen lama diarsipkan:", len(old_components))
        print("Relasi baru:", len(records))
        print("Relasi lama dipertahankan:", len(old_relations))

        if not apply:
            print("\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Jalankan --apply hanya setelah hasil dry-run diperiksa.")
            return

        backup = Path(
            "database/garment-before-ddl8700-"
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

        # Arsipkan komponen lama tanpa menghapus komponen/relasinya.
        old_ids = [r["id"] for r in old_components]

        con.execute("""
            UPDATE components
            SET machine_id = NULL
            WHERE machine_id = ?
        """, (MACHINE_ID,))

        component_ids = {}

        for section, title, diagram_page, table_page, expected in SECTIONS:
            cur = con.execute("""
                INSERT INTO components (
                    machine_id, component_name, notes,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                title,
                f"Official JUKI DDL-8700 Parts List, Section {section}.",
                SOURCE_URL,
                str(section),
                diagram_page,
            ))

            component_ids[section] = cur.lastrowid

        used_old_ids = set()
        reused_ids = set()

        for r in records:
            old = old_by_number.get(r["number"])

            reuse = (
                old is not None
                and old["id"] not in used_old_ids
                and old["part_name"] == r["name"]
            )

            if reuse:
                part_id = old["id"]
                used_old_ids.add(part_id)
                reused_ids.add(part_id)

                con.execute("""
                    UPDATE parts
                    SET source_document_id = ?,
                        part_name = ?,
                        quantity = ?,
                        catalog_ref = ?,
                        diagram_page = ?,
                        note = ?,
                        source_url = ?,
                        quantity_raw = ?
                    WHERE id = ? AND machine_id = ?
                """, (
                    DOCUMENT_ID,
                    r["name"],
                    r["qty"],
                    r["ref"],
                    r["diagram_page"],
                    r["marker"],
                    SOURCE_URL,
                    r["qty_raw"],
                    part_id,
                    MACHINE_ID,
                ))
            else:
                cur = con.execute("""
                    INSERT INTO parts (
                        machine_id, source_document_id,
                        part_number, part_name, quantity,
                        catalog_ref, diagram_page, note,
                        source_url, notes, quantity_raw
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID,
                    DOCUMENT_ID,
                    r["number"],
                    r["name"],
                    r["qty"],
                    r["ref"],
                    r["diagram_page"],
                    r["marker"],
                    SOURCE_URL,
                    f"DDL-8700 Section {r['section']}: {r['title']}",
                    r["qty_raw"],
                ))
                part_id = cur.lastrowid

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, ?, ?)
            """, (
                component_ids[r["section"]],
                part_id,
                "catalog_component_part",
                f"REF {r['ref']}",
            ))

        # Audit total aktif.
        counts = get_counts(con)

        if counts != TARGET:
            stop(f"Target database tidak sesuai: {counts}, target {TARGET}")

        # Pastikan seluruh REF dan data katalog tersimpan tepat.
        inserted = con.execute("""
            SELECT
                c.catalog_ref AS section,
                p.catalog_ref AS ref,
                p.part_number,
                p.part_name,
                p.quantity,
                p.quantity_raw,
                p.note,
                p.diagram_page,
                cp.notes AS relation_notes,
                cp.relation_type
            FROM component_parts cp
            JOIN components c ON c.id = cp.component_id
            JOIN parts p ON p.id = cp.part_id
            WHERE c.machine_id = ?
            ORDER BY CAST(c.catalog_ref AS INTEGER), p.catalog_ref
        """, (MACHINE_ID,)).fetchall()

        if len(inserted) != 429:
            stop(f"Jumlah relasi hasil audit bukan 429: {len(inserted)}")

        for actual, expected in zip(inserted, records):
            wanted = (
                str(expected["section"]),
                expected["ref"],
                expected["number"],
                expected["name"],
                expected["qty"],
                expected["qty_raw"],
                expected["marker"],
                expected["diagram_page"],
                f"REF {expected['ref']}",
                "catalog_component_part",
            )

            if tuple(actual) != wanted:
                stop(
                    "Data hasil impor berbeda dari katalog pada "
                    f"Section {expected['section']} REF {expected['ref']}\n"
                    f"Aktual: {tuple(actual)}\n"
                    f"Harus : {wanted}"
                )

        # Pastikan arsip lama dan 10 relasi lama tetap utuh.
        archived = con.execute("""
            SELECT
                id, machine_id, component_name, part_number,
                location, function, notes, image_path,
                source_url, catalog_ref, diagram_page
            FROM components
            WHERE id IN ({})
            ORDER BY id
        """.format(",".join("?" for _ in old_ids)), old_ids).fetchall()

        for before, after in zip(old_components, archived):
            expected = list(before)
            expected[1] = None
            if tuple(after) != tuple(expected):
                stop(f"Data komponen arsip berubah: ID {before['id']}")

        after_relations = old_relation_snapshot(con, old_ids)

        if [tuple(r) for r in after_relations] != [
            tuple(r) for r in old_relations
        ]:
            stop("Relasi komponen lama berubah")

        print("\n=== PREFLIGHT FINAL ===")
        print("Parts aktif:", counts[0])
        print("Komponen aktif:", counts[1])
        print("Relasi aktif:", counts[2])
        print("Part lama digunakan kembali:", len(reused_ids))
        print("Part baru:", len(records) - len(reused_ids))
        print("Komponen lama diarsipkan:", len(archived))
        print("Relasi lama tetap utuh:", len(after_relations))
        print("429 REF sesuai katalog:", True)

        con.commit()

        print("\n=== IMPOR DDL-8700 BERHASIL ===")
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
