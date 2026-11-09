import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 45
DOC_ID = 159

TARGETS = [
    (404, "1-13468", "141-13468", 28, 8445, "BOBBIN THREAD TENSION ASM.", 9, "1"),
    (409, "0-34846", "400-34846", 12, 8807, "SHUTTLE_ASM", 21, "1"),
    (411, "0-86363", "400-86363", 1, 8864, "WIPER_ASM", 22, "1"),
    (423, "0-30951", "400-30951", 17, 9400, "FILTER_REGULATOR_ASM.", 38, "1"),
    (424, "0-96354", "400-96354", 1, 9422, "THREAD STAND ASM.", 39, "1"),
    (425, "0-86485", "400-86485", 1, 9446, "IP-420F PANEL ASSY", 41, "1"),
    (426, "0-81602", "400-81602", 16, 9461, "POWER SWITCH ASM", 41, "1"),
    (427, "2-68713", "402-68713", 15, 9509, "MAIN PCB B ASSY", 43, "(1)"),
]

def check(condition, message):
    if not condition:
        raise RuntimeError(message)

check(DB.exists(), f"Database tidak ditemukan: {DB}")

backup = DB.with_name(
    "garment-before-ams221en-mainpart-" +
    datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)
check(not backup.exists(), f"Backup sudah ada: {backup}")

shutil.copy2(DB, backup)
print("BACKUP:", backup)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("BEGIN IMMEDIATE")

    validated = []

    for cid, oldpn, newpn, ref, pid, pname, page, qty in TARGETS:
        c = con.execute("""
            SELECT * FROM components
            WHERE id=? AND machine_id=?
        """, (cid, MACHINE_ID)).fetchone()

        check(c is not None, f"Komponen {cid} tidak ditemukan")
        check(c["part_number"] == oldpn,
              f"Part number komponen {cid} tidak sesuai")
        check(str(c["catalog_ref"]) == str(ref),
              f"Catalog ref komponen {cid} tidak sesuai")
        check(c["diagram_page"] in (None, page),
              f"Diagram page komponen {cid} sudah berbeda")

        p = con.execute("""
            SELECT * FROM parts
            WHERE id=? AND machine_id=? AND source_document_id=?
        """, (pid, MACHINE_ID, DOC_ID)).fetchone()

        check(p is not None, f"Part ID {pid} tidak ditemukan")
        check(p["part_number"] == newpn, f"Part number part {pid} berbeda")
        check(p["part_name"] == pname, f"Nama part {pid} berbeda")
        check(str(p["catalog_ref"]) == str(ref),
              f"Catalog ref part {pid} berbeda")

        o = con.execute("""
            SELECT 1 FROM catalog_occurrences
            WHERE machine_id=?
              AND source_document_id=?
              AND pdf_page=?
              AND CAST(catalog_ref AS TEXT)=?
              AND part_number=?
              AND part_name=?
              AND COALESCE(quantity_raw,'')=?
        """, (MACHINE_ID, DOC_ID, page, str(ref),
              newpn, pname, qty)).fetchone()

        check(o is not None,
              f"Occurrence katalog tidak cocok: komponen {cid}")

        existing = con.execute("""
            SELECT part_id FROM component_parts
            WHERE component_id=? AND relation_type='main-part'
        """, (cid,)).fetchall()

        check(
            all(r["part_id"] == pid for r in existing),
            f"Komponen {cid} memiliki main-part lain"
        )

        validated.append((cid, newpn, page, pid))

    print("VALIDASI BERHASIL:", len(validated), "komponen")

    for cid, newpn, page, pid in validated:
        con.execute("""
            UPDATE components
            SET part_number=?, diagram_page=?
            WHERE id=? AND machine_id=?
        """, (newpn, page, cid, MACHINE_ID))

        exists = con.execute("""
            SELECT 1 FROM component_parts
            WHERE component_id=? AND part_id=?
              AND relation_type='main-part'
        """, (cid, pid)).fetchone()

        if not exists:
            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, 'main-part', ?)
            """, (
                cid, pid,
                "Verified against JUKI AMS-221EN Parts List."
            ))

    con.commit()
    print("PEMBARUAN BERHASIL:", len(validated), "komponen")
    print("Relasi sub-part tidak diubah.")
    print("BACKUP TERSIMPAN:", backup)

except Exception as e:
    con.rollback()
    print("PEMBARUAN DIBATALKAN:", e)
    print("Transaksi di-rollback. Backup:", backup)
    raise

finally:
    con.close()
