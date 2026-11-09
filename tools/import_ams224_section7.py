import re
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section7/page19.txt")

MACHINE_ID = 47
DOCUMENT_ID = 583

COMPONENT_NAME = (
    "PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (2)"
)

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

PATTERN = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"([A-Z0-9][A-Z0-9-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)


def parse_source():
    rows = []

    for line_no, line in enumerate(
        TXT.read_text(errors="replace").splitlines(), 1
    ):
        m = PATTERN.match(line)

        if not m:
            continue

        ref, number, name, qty_raw = m.groups()

        rows.append({
            "ref": int(ref),
            "number": number,
            "name": name.strip(),
            "qty_raw": qty_raw,
            "qty": int(qty_raw.strip("()")),
            "line": line_no,
        })

    return rows


def snapshot(con, exclude_id=None):
    sql = """
        SELECT c.id, c.component_name, c.diagram_page,
               c.image_path, COUNT(cp.id)
        FROM components c
        LEFT JOIN component_parts cp ON cp.component_id=c.id
        WHERE c.machine_id=?
    """

    params = [MACHINE_ID]

    if exclude_id is not None:
        sql += " AND c.id != ?"
        params.append(exclude_id)

    sql += """
        GROUP BY c.id
        ORDER BY c.id
    """

    return [tuple(r) for r in con.execute(sql, params)]


def main():
    if not DB.is_file() or not TXT.is_file():
        raise SystemExit("Database atau file sumber tidak ditemukan.")

    rows = parse_source()

    refs = [r["ref"] for r in rows]
    unique_numbers = len({r["number"] for r in rows})

    print("=== VALIDASI SUMBER ===")
    print("REF terbaca:", len(rows))
    print("Nomor part unik:", unique_numbers)
    print("REF berurutan:", refs == list(range(1, 55)))

    if len(rows) != 54 or refs != list(range(1, 55)):
        raise SystemExit("BATAL: sumber harus berisi REF 01-54.")

    if unique_numbers != 48:
        raise SystemExit("BATAL: jumlah nomor part unik tidak sesuai.")

    ref54 = next(r for r in rows if r["ref"] == 54)

    if (
        ref54["number"] != "SM-6041402-TP"
        or ref54["name"] != "SCREW M4 L=14"
        or ref54["qty_raw"] != "4"
    ):
        raise SystemExit("BATAL: data REF 54 tidak sesuai.")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    backup = Path("database") / (
        "garment-before-section7-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".db"
    )

    try:
        parts_before = con.execute("""
            SELECT COUNT(*)
            FROM parts
            WHERE machine_id=? AND source_document_id=?
        """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

        components_before = con.execute("""
            SELECT COUNT(*)
            FROM components
            WHERE machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        relations_before = con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        if (
            parts_before,
            components_before,
            relations_before
        ) != (320, 4, 320):
            raise RuntimeError(
                "Preflight gagal. Target kondisi: "
                "320 part, 4 komponen, 320 relasi."
            )

        if con.execute("""
            SELECT 1
            FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID, COMPONENT_NAME)).fetchone():
            raise RuntimeError("Komponen Section 7 sudah ada.")

        old_snapshot = snapshot(con)

        backup_con = sqlite3.connect(backup)
        con.backup(backup_con)
        backup_con.close()

        print("\nBACKUP:", backup)
        print("PRE-FLIGHT LULUS")

        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components (
                machine_id, component_name, part_number,
                location, function, notes, image_path,
                source_url, catalog_ref, diagram_page
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID,
            COMPONENT_NAME,
            None,
            COMPONENT_NAME,
            COMPONENT_NAME,
            "Official JUKI AMS-224EN/IP-420 Parts List No.1575-03; "
            "diagram page 18; parts list page 19; model 6030.",
            None,
            SOURCE_URL,
            None,
            18,
        ))

        component_id = cur.lastrowid

        for r in rows:
            cur = con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id,
                    part_number, part_name, quantity,
                    catalog_ref, diagram_page, note,
                    source_url, notes, quantity_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                DOCUMENT_ID,
                r["number"],
                r["name"],
                r["qty"],
                r["ref"],
                None,
                None,
                SOURCE_URL,
                f"AMS-224EN-6030 section: {COMPONENT_NAME}",
                r["qty_raw"],
            ))

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                ) VALUES (?, ?, ?, ?)
            """, (
                component_id,
                cur.lastrowid,
                "catalog_component_part",
                f"Catalog REF {r['ref']:02d}",
            ))

        parts_after = con.execute("""
            SELECT COUNT(*)
            FROM parts
            WHERE machine_id=? AND source_document_id=?
        """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

        new_relations = con.execute("""
            SELECT COUNT(*)
            FROM component_parts
            WHERE component_id=?
        """, (component_id,)).fetchone()[0]

        new_refs = [
            r[0] for r in con.execute("""
                SELECT p.catalog_ref
                FROM parts p
                JOIN component_parts cp ON cp.part_id=p.id
                WHERE cp.component_id=?
                ORDER BY p.catalog_ref
            """, (component_id,))
        ]

        components_after = con.execute("""
            SELECT COUNT(*)
            FROM components
            WHERE machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        relations_after = con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        if parts_after != 374:
            raise RuntimeError(f"Total part salah: {parts_after}")

        if new_relations != 54:
            raise RuntimeError("Jumlah relasi baru bukan 54.")

        if new_refs != list(range(1, 55)):
            raise RuntimeError("Verifikasi REF baru gagal.")

        if (components_after, relations_after) != (5, 374):
            raise RuntimeError("Verifikasi total akhir gagal.")

        if snapshot(con, exclude_id=component_id) != old_snapshot:
            raise RuntimeError("Komponen lama berubah.")

        con.commit()

        print("\n=== IMPOR SECTION 7 BERHASIL ===")
        print("Component ID :", component_id)
        print("Nama         :", COMPONENT_NAME)
        print("Diagram page :", 18)
        print("REF baru     :", new_relations)
        print("Part total   :", parts_after)
        print("Komponen     :", components_after)
        print("Relasi total :", relations_after)
        print("Nomor unik   :", unique_numbers)
        print("Komponen 598-601: TIDAK BERUBAH")
        print("STATUS: COMMIT BERHASIL")

    except Exception as e:
        if con.in_transaction:
            con.rollback()

        print("\n=== IMPOR DIBATALKAN ===")
        print(e)
        print("Transaksi di-ROLLBACK.")
        raise

    finally:
        con.close()


if __name__ == "__main__":
    main()
