import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
NOTE = "AMS-210EN catalog staging; section 2"
MACHINE_ID = 15
DOCUMENT_ID = 136
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

MISSING = {
    18: ("262-61503", "BTW_WHEEL_RUBBER", "(1)", "☆"),
    36: ("CM-6001001-01", "WEEE MARK LABEL S", "1", "#01"),
    48: ("400-05712", "EARTH CODE ASM", "1", "COMMON"),
    49: ("SL-4041891-SC", "SCREW M4 L=18", "1", "COMMON"),
    50: ("SL-4041091-SC", "SCREW M4 L=10", "5", "COMMON"),
}

def stop(msg):
    raise RuntimeError(msg)

if not DB.is_file():
    stop("Database tidak ditemukan")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    machine = con.execute(
        "SELECT model FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    if not machine or machine["model"] != "AMS-210EN-1510":
        stop("Identitas mesin tidak cocok")

    rows = con.execute("""
        SELECT * FROM parts
        WHERE machine_id=? AND notes=?
        ORDER BY id
    """, (MACHINE_ID, NOTE)).fetchall()

    refs = [int(r["catalog_ref"]) for r in rows]
    if len(rows) != 46 or len(refs) != len(set(refs)):
        stop(f"Baseline staging berubah: jumlah={len(rows)}, REF={refs}")

    wrong = [r for r in rows if r["catalog_ref"] == 63]
    if len(wrong) != 1:
        stop("Baris staging REF63 tidak ditemukan secara unik")

    bad = wrong[0]
    if (bad["part_number"], bad["part_name"], bad["quantity_raw"]) != (
        "SL-6084092-TN", "BOLT", "1"
    ):
        stop("Isi baris REF63 tidak sesuai dengan hasil audit")

    if con.execute(
        "SELECT COUNT(*) FROM component_parts WHERE part_id=?",
        (bad["id"],)
    ).fetchone()[0]:
        stop("REF63 memiliki relasi; tidak boleh dihapus")

    for ref, (pn, name, qty, marker) in MISSING.items():
        if ref in refs:
            stop(f"REF {ref} ternyata sudah ada")
        duplicate = con.execute("""
            SELECT COUNT(*) FROM parts
            WHERE machine_id=? AND notes=? AND catalog_ref=?
        """, (MACHINE_ID, NOTE, ref)).fetchone()[0]
        if duplicate:
            stop(f"REF {ref} duplikat")

    backup = DB.with_name(
        f"garment-before-ams210en1510-section2-staging-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    shutil.copy2(DB, backup)
    print("Backup:", backup)

    con.execute("BEGIN IMMEDIATE")

    con.execute("DELETE FROM parts WHERE id=?", (bad["id"],))

    for ref, (pn, name, qty, marker) in MISSING.items():
        raw = qty.strip("()")
        quantity = float(raw) if "." in raw else int(raw)

        con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number, part_name,
                quantity, catalog_ref, diagram_page, note,
                source_url, notes, quantity_raw
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, DOCUMENT_ID, pn, name, quantity, ref,
            3, marker, SOURCE_URL, NOTE, qty
        ))

    final = con.execute("""
        SELECT catalog_ref, part_number, part_name, quantity_raw, note
        FROM parts
        WHERE machine_id=? AND notes=?
        ORDER BY catalog_ref
    """, (MACHINE_ID, NOTE)).fetchall()

    final_refs = [r["catalog_ref"] for r in final]
    if final_refs != list(range(1, 51)):
        stop(f"Validasi REF gagal: {final_refs}")

    for ref, (pn, name, qty, marker) in MISSING.items():
        r = next(x for x in final if x["catalog_ref"] == ref)
        if (r["part_number"], r["part_name"], r["quantity_raw"], r["note"]) != (
            pn, name, qty, marker
        ):
            stop(f"Validasi isi REF {ref} gagal")

    con.commit()
    print("OK: staging Section 2 berhasil diperbaiki")
    print("Jumlah REF:", len(final))
    print("Rentang REF: 1–50 lengkap")
    print("REF 63 salah dihapus; 5 REF katalog ditambahkan")

except Exception:
    con.rollback()
    raise
finally:
    con.close()
