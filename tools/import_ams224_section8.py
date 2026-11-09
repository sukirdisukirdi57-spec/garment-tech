import re
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("tmp/ams224en6030-section8/page21.txt")

MACHINE_ID = 47
DOCUMENT_ID = 583
COMPONENT_NAME = "SHUTTLE DRIVER SHAFT COMPONENTS (1)"
SOURCE_URL = "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/j/u/juki_ams224en_parts_book.pdf"

PATTERN = re.compile(
    r'^\s*(\d{1,2})\s+'
    r'(?:(#01|☆)\s+)?'
    r'([A-Z0-9][A-Z0-9-]+)\s+'
    r'(.+?)\s+'
    r'(\(?\d+(?:\.\d+)?\)?)\s*$'
)

def parse_records():
    records = []
    for line in TXT.read_text(errors="replace").splitlines():
        m = PATTERN.match(line)
        if not m:
            continue

        ref, marker, number, name, qty_raw = m.groups()
        raw = qty_raw.strip()
        numeric = float(raw.strip("()"))
        qty = int(numeric) if numeric.is_integer() else numeric

        records.append({
            "ref": int(ref),
            "marker": marker or None,
            "number": number,
            "name": name.strip(),
            "qty": qty,
            "qty_raw": raw,
        })
    return records

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
    sql += " GROUP BY c.id ORDER BY c.id"
    return [tuple(r) for r in con.execute(sql, params)]

if not DB.is_file() or not TXT.is_file():
    raise SystemExit("GAGAL: database atau file sumber tidak ditemukan")

records = parse_records()
refs = [r["ref"] for r in records]
unique_numbers = len({r["number"] for r in records})

print("=== VALIDASI SUMBER ===")
print("REF terbaca:", len(records))
print("Nomor part unik:", unique_numbers)
print("REF berurutan:", refs == list(range(1, 50)))

if len(records) != 49 or refs != list(range(1, 50)):
    raise SystemExit("GAGAL: struktur REF tidak sesuai")

if unique_numbers != 48:
    raise SystemExit("GAGAL: jumlah nomor part unik tidak sesuai")

expected = {
    13: ("CQ-2000000-00", "(8.9)"),
    14: ("236-30007", "(3.9)"),
    54: None,
}

for ref, expected_value in expected.items():
    if expected_value is None:
        continue
    r = records[ref - 1]
    if (r["number"], r["qty_raw"]) != expected_value:
        raise SystemExit(f"GAGAL: data REF {ref} tidak sesuai")

for ref in (21, 22, 23, 24, 46, 47, 48, 49):
    if records[ref - 1]["marker"] != "#01":
        raise SystemExit(f"GAGAL: penanda #01 REF {ref} hilang")

for ref in (28, 29, 30, 31):
    if records[ref - 1]["marker"] != "☆":
        raise SystemExit(f"GAGAL: penanda ☆ REF {ref} hilang")

print("Penanda katalog: VALID")
print("Kuantitas desimal: VALID")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    machine = con.execute(
        "SELECT id FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    if machine is None:
        raise RuntimeError("Machine ID 47 tidak ditemukan")

    doc = con.execute(
        "SELECT id FROM documents WHERE id=? AND machine_id=?",
        (DOCUMENT_ID, MACHINE_ID)
    ).fetchone()
    if doc is None:
        raise RuntimeError("Dokumen sumber ID 583 tidak ditemukan")

    counts = (
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
        """, (MACHINE_ID,)).fetchone()[0],
    )

    print("\nKondisi database:", counts)

    if counts != (374, 5, 374):
        raise RuntimeError(
            "Preflight gagal: kondisi database tidak sesuai target"
        )

    existing = con.execute(
        "SELECT id FROM components WHERE machine_id=? AND component_name=?",
        (MACHINE_ID, COMPONENT_NAME)
    ).fetchone()

    if existing:
        raise RuntimeError(
            f"Komponen sudah ada dengan ID {existing['id']}; hentikan impor"
        )

    before = snapshot(con)

    backup = Path(
        "database/garment-before-section8-"
        + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
    )
    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()
    print("BACKUP:", backup)

    con.execute("BEGIN IMMEDIATE")

    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, location, function,
            notes, source_url, catalog_ref, diagram_page, image_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
    """, (
        MACHINE_ID,
        COMPONENT_NAME,
        COMPONENT_NAME,
        COMPONENT_NAME,
        "Official JUKI parts catalog. Diagram page 20, parts list page 21. Model 6030.",
        SOURCE_URL,
        None,
        20,
    ))

    component_id = cur.lastrowid

    for r in records:
        cur = con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number, part_name,
                quantity, catalog_ref, diagram_page, note,
                source_url, notes, quantity_raw
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
                component_id, part_id, relation_type, notes
            )
            VALUES (?, ?, ?, ?)
        """, (
            component_id,
            part_id,
            "catalog_component_part",
            f"Catalog REF {r['ref']:02d}",
        ))

    new_counts = (
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
        """, (MACHINE_ID,)).fetchone()[0],
    )

    linked = con.execute("""
        SELECT COUNT(*)
        FROM component_parts
        WHERE component_id=?
    """, (component_id,)).fetchone()[0]

    refs_db = [
        r[0] for r in con.execute("""
            SELECT p.catalog_ref
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY p.catalog_ref
        """, (component_id,))
    ]

    old_unchanged = snapshot(con, exclude_id=component_id) == before

    print("\n=== PREFLIGHT FINAL ===")
    print("Total parts:", new_counts[0])
    print("Total komponen:", new_counts[1])
    print("Total relasi:", new_counts[2])
    print("Relasi Section 8:", linked)
    print("REF 1-49 valid:", refs_db == list(range(1, 50)))
    print("Komponen lama tidak berubah:", old_unchanged)

    if new_counts != (423, 6, 423):
        raise RuntimeError("Jumlah akhir database tidak sesuai")

    if linked != 49 or refs_db != list(range(1, 50)):
        raise RuntimeError("Verifikasi relasi Section 8 gagal")

    if not old_unchanged:
        raise RuntimeError("Data komponen lama berubah")

    con.commit()

    print("\n=== IMPOR SECTION 8 BERHASIL ===")
    print("Component ID :", component_id)
    print("Nama         :", COMPONENT_NAME)
    print("Diagram page : 20")
    print("REF baru     :", linked)
    print("Part total   :", new_counts[0])
    print("Komponen     :", new_counts[1])
    print("Relasi total :", new_counts[2])
    print("Nomor unik   :", unique_numbers)
    print("STATUS: COMMIT BERHASIL")

except Exception:
    if con.in_transaction:
        con.rollback()
    raise
finally:
    con.close()
