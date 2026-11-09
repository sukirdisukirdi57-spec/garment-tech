import re
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
SOURCE = Path("assets/documents/juki/mh380-parts.txt")
MACHINE_ID = 13
DOC_ID = 131

GAUGES = {
    "B": "1/8", "C": "5/32", "D": "3/16", "E": "7/32",
    "F": "1/4", "H": "5/16", "K": "3/8", "L": "1/2",
}

SEQ = "BCDEFHKL"
MAPS = {
    25: {
        **{i: c for i, c in enumerate(SEQ, 1)},
        **{i: c for i, c in enumerate(SEQ, 10)},
        **{i: c for i, c in enumerate(SEQ, 19)},
        28: "B", 29: "E", 30: "F", 31: "H", 32: "K", 33: "L",
        35: "C", 36: "E", 37: "H", 38: "L",
        40: "E", 41: "E",
    },
    27: {
        1: "E", 2: "E", 3: "E", 4: "L",
        5: "D", 6: "H", 7: "L",
        8: "B", 9: "C", 10: "D", 11: "E",
        12: "F", 13: "H",
    },
}

def extract(page_no):
    pages = SOURCE.read_text(errors="replace").split("\f")
    rows = []
    for line in pages[page_no - 1].splitlines():
        m = re.match(
            r'\s*(\d{1,2})\s+(\S{8,})\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$',
            line
        )
        if m:
            rows.append({
                "ref": int(m.group(1)),
                "pn": m.group(2),
                "name": m.group(3).strip(),
                "qty": m.group(4),
                "line": line.strip(),
            })
    return rows

if not DB.exists() or not SOURCE.exists():
    raise SystemExit("DB atau sumber teks tidak ditemukan.")

rows_by_page = {}
for page, expected in ((25, 42), (27, 17)):
    rows = extract(page)
    refs = [r["ref"] for r in rows]
    if len(rows) != expected or refs != list(range(1, expected + 1)):
        raise SystemExit(f"Validasi REF halaman {page} gagal: {refs}")
    if not set(MAPS[page]).issubset(set(refs)):
        raise SystemExit(f"Mapping halaman {page} memiliki REF tidak valid.")
    rows_by_page[page] = rows

if sum(map(len, rows_by_page.values())) != 59:
    raise SystemExit("Jumlah occurrences bukan 59.")
if sum(map(len, MAPS.values())) != 49:
    raise SystemExit("Jumlah mapping bukan 49.")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.execute("PRAGMA foreign_keys=OFF")

try:
    # Pemeriksaan keadaan awal — hentikan jika berbeda dari preflight.
    doc = con.execute(
        "SELECT id, machine_id, source_url FROM documents WHERE id=?",
        (DOC_ID,)
    ).fetchone()
    if not doc or doc["machine_id"] != MACHINE_ID:
        raise RuntimeError("Dokumen Parts List ID131 tidak cocok.")

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
        "occurrences": con.execute(
            "SELECT COUNT(*) FROM catalog_occurrences WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],
        "maps_total": con.execute(
            "SELECT COUNT(*) FROM catalog_gauge_maps"
        ).fetchone()[0],
        "maps_ms1190": con.execute(
            "SELECT COUNT(*) FROM catalog_gauge_maps WHERE machine_id=14"
        ).fetchone()[0],
    }
    expected = {
        "parts": 533, "components": 11, "relations": 533,
        "occurrences": 533, "maps_total": 69, "maps_ms1190": 69,
    }
    if counts != expected:
        raise RuntimeError(f"Keadaan awal berubah: {counts}")

    for page in (25, 27):
        existing = con.execute("""
            SELECT COUNT(*) FROM catalog_occurrences
            WHERE machine_id=? AND pdf_page=?
        """, (MACHINE_ID, page)).fetchone()[0]
        if existing:
            raise RuntimeError(f"Halaman {page} sudah memiliki {existing} occurrences.")

    schema = con.execute("""
        SELECT sql FROM sqlite_master
        WHERE type='table' AND name='catalog_gauge_maps'
    """).fetchone()
    if not schema or "'K'" in schema["sql"] or "'L'" in schema["sql"]:
        raise RuntimeError("Skema gauge map tidak sesuai kondisi awal.")

    # Backup konsisten sebelum perubahan.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.with_name(f"garment-before-mh380-gauge-{stamp}.db")
    dst = sqlite3.connect(backup)
    con.backup(dst)
    dst.close()
    print("BACKUP:", backup)

    con.execute("BEGIN IMMEDIATE")

    con.execute("""
        CREATE TABLE catalog_gauge_maps_new (
            occurrence_id INTEGER PRIMARY KEY,
            machine_id INTEGER NOT NULL,
            source_document_id INTEGER NOT NULL,
            gauge_code TEXT NOT NULL
                CHECK(gauge_code IN ('B','C','D','E','F','H','K','L')),
            gauge_size_inch TEXT NOT NULL,
            source_pdf_page INTEGER NOT NULL,
            FOREIGN KEY(occurrence_id) REFERENCES catalog_occurrences(id),
            FOREIGN KEY(machine_id) REFERENCES machines(id),
            FOREIGN KEY(source_document_id) REFERENCES documents(id)
        )
    """)
    con.execute("""
        INSERT INTO catalog_gauge_maps_new
        SELECT occurrence_id, machine_id, source_document_id,
               gauge_code, gauge_size_inch, source_pdf_page
        FROM catalog_gauge_maps
    """)
    con.execute("DROP TABLE catalog_gauge_maps")
    con.execute("""
        ALTER TABLE catalog_gauge_maps_new RENAME TO catalog_gauge_maps
    """)

    inserted_occ = 0
    inserted_maps = 0
    source_url = doc["source_url"]

    for page, rows in rows_by_page.items():
        matrix_page = 24 if page == 25 else 26
        for r in rows:
            cur = con.execute("""
                INSERT INTO catalog_occurrences (
                    machine_id, source_document_id, pdf_page, catalog_ref,
                    marker, part_number, part_name, quantity_raw,
                    catalog_line_original, source_url
                ) VALUES (?, ?, ?, ?, '', ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, DOC_ID, page, str(r["ref"]),
                r["pn"], r["name"], r["qty"], r["line"], source_url
            ))
            occurrence_id = cur.lastrowid
            inserted_occ += 1

            code = MAPS[page].get(r["ref"])
            if code:
                con.execute("""
                    INSERT INTO catalog_gauge_maps (
                        occurrence_id, machine_id, source_document_id,
                        gauge_code, gauge_size_inch, source_pdf_page
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    occurrence_id, MACHINE_ID, DOC_ID,
                    code, GAUGES[code], matrix_page
                ))
                inserted_maps += 1

    if inserted_occ != 59 or inserted_maps != 49:
        raise RuntimeError(
            f"Jumlah insert tidak sesuai: occurrences={inserted_occ}, maps={inserted_maps}"
        )

    fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        raise RuntimeError(f"Foreign key check gagal: {fk_errors[:5]}")

    con.commit()
    con.execute("PRAGMA foreign_keys=ON")

    print("APPLY BERHASIL")
    print("Occurrences ditambahkan:", inserted_occ)
    print("Gauge maps ditambahkan:", inserted_maps)
    print("Backup tersimpan:", backup)

except Exception:
    con.rollback()
    con.close()
    raise

# Audit pasca-commit.
con.execute("PRAGMA foreign_keys=ON")
print("\n=== AUDIT MH-380 ===")
for table in ("parts", "components", "catalog_occurrences", "catalog_gauge_maps"):
    print(table, con.execute(
        f"SELECT COUNT(*) FROM {table} WHERE machine_id=?", (MACHINE_ID,)
    ).fetchone()[0])

for page in (25, 27):
    row = con.execute("""
        SELECT COUNT(*), MIN(CAST(catalog_ref AS INTEGER)),
               MAX(CAST(catalog_ref AS INTEGER))
        FROM catalog_occurrences
        WHERE machine_id=? AND pdf_page=?
    """, (MACHINE_ID, page)).fetchone()
    print(f"Page {page}: count={row[0]}, REF={row[1]}-{row[2]}")

print("Total gauge maps:", con.execute(
    "SELECT COUNT(*) FROM catalog_gauge_maps"
).fetchone()[0])
print("Gauge maps MH-1190:", con.execute(
    "SELECT COUNT(*) FROM catalog_gauge_maps WHERE machine_id=14"
).fetchone()[0])
print("Gauge maps MH-380:", con.execute(
    "SELECT COUNT(*) FROM catalog_gauge_maps WHERE machine_id=13"
).fetchone()[0])
print("Kode MH-380:", [
    tuple(r) for r in con.execute("""
        SELECT gauge_code, gauge_size_inch, COUNT(*)
        FROM catalog_gauge_maps
        WHERE machine_id=13
        GROUP BY gauge_code, gauge_size_inch
        ORDER BY gauge_code
    """)
])
print("Foreign key errors:", con.execute("PRAGMA foreign_key_check").fetchall())
con.close()
