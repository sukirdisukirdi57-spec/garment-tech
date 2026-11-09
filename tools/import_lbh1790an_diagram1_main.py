import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram1.png")
IMAGE_PATH = "component_images/lbh1790an_diagram1.png"

MACHINE = 6
PAGE = 1
TITLE = "1. FRAME & MISCELLANEOUS COVER COMPONENTS (1)"
APPLY = "--apply" in __import__("sys").argv

if not IMAGE.exists():
    raise SystemExit("ERROR: gambar Diagram 1 tidak ditemukan")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    parts = con.execute("""
        SELECT id, catalog_ref
        FROM parts
        WHERE machine_id=? AND diagram_page=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE, PAGE)).fetchall()

    refs = [int(p["catalog_ref"]) for p in parts
            if str(p["catalog_ref"]).isdigit()]

    if len(parts) != 86 or sorted(refs) != list(range(1, 87)):
        raise SystemExit("ERROR: REF Diagram 1 tidak lengkap atau duplikat")

    old = con.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND diagram_page=?
    """, (MACHINE, PAGE)).fetchall()

    conflict = con.execute("""
        SELECT id, component_name FROM components
        WHERE machine_id=? AND diagram_page=? AND component_name=?
    """, (MACHINE, PAGE, TITLE)).fetchone()

    if conflict:
        raise SystemExit(f"ERROR: komponen utama sudah ada: {dict(conflict)}")

    sub = con.execute("""
        SELECT id, component_name
        FROM components
        WHERE id=623 AND machine_id=? AND diagram_page=?
    """, (MACHINE, PAGE)).fetchone()

    if not sub or sub["component_name"] != "HOOK OIL SHIELD COVER COMPL":
        raise SystemExit("ERROR: subassembly ID 623 tidak sesuai")

    sub_count = con.execute("""
        SELECT COUNT(*) FROM component_parts WHERE component_id=623
    """).fetchone()[0]

    if sub_count != 13:
        raise SystemExit(f"ERROR: relasi subassembly ID 623 = {sub_count}, bukan 13")

    print("=== PREFLIGHT DIAGRAM 1 MAIN ===")
    print("Judul:", TITLE)
    print("Jumlah REF:", len(parts))
    print("Komponen lama:", [dict(x) for x in old])
    print("Subassembly ID 623:", sub_count, "relasi")
    print("Relasi komponen utama yang akan dibuat:", 86)

    if not APPLY:
        print("\nDRY-RUN BERHASIL. Database belum diubah.")
        raise SystemExit(0)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.with_name(f"garment-before-lbh1790an-diagram1-main-{stamp}.db")

    b = sqlite3.connect(backup)
    con.backup(b)
    b.close()
    print("Backup:", backup)

    try:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components
                (machine_id, component_name, catalog_ref,
                 diagram_page, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (MACHINE, TITLE, "1", PAGE, IMAGE_PATH))

        main_id = cur.lastrowid

        for p in parts:
            ref = int(p["catalog_ref"])
            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, ?, ?)
            """, (
                main_id, p["id"],
                "catalog_component_part", f"REF {ref}"
            ))

        con.commit()
        print("IMPORT BERHASIL")
        print("Komponen utama ID:", main_id)
        print("Jumlah relasi:", len(parts))

    except Exception:
        con.rollback()
        raise

finally:
    con.close()
