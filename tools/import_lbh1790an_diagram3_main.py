import sqlite3
from pathlib import Path
from datetime import datetime
import sys

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram3.png")
IMAGE_PATH = "component_images/lbh1790an_diagram3.png"

MACHINE = 6
PAGE = 5
TITLE = "3. MAIN SHAFT COMPONENTS"
APPLY = "--apply" in sys.argv

EXPECTED_GROUPS = {
    625: list(range(2, 10)),
    626: list(range(10, 15)),
    627: list(range(15, 18)),
    628: list(range(29, 32)),
}

if not DB.exists():
    raise SystemExit("ERROR: database tidak ditemukan")
if not IMAGE.exists():
    raise SystemExit("ERROR: gambar Diagram 3 tidak ditemukan")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    parts = con.execute("""
        SELECT id, catalog_ref
        FROM parts
        WHERE machine_id=? AND diagram_page=?
        ORDER BY CAST(catalog_ref AS INTEGER), id
    """, (MACHINE, PAGE)).fetchall()

    refs = [
        int(p["catalog_ref"])
        for p in parts
        if str(p["catalog_ref"]).isdigit()
    ]

    if len(parts) != 39 or sorted(refs) != list(range(1, 40)):
        raise SystemExit("ERROR: REF Diagram 3 tidak lengkap atau duplikat")

    print("=== PREFLIGHT DIAGRAM 3 MAIN ===")
    print("Judul:", TITLE)
    print("Jumlah REF utama:", len(parts))

    existing = con.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND diagram_page=?
        ORDER BY id
    """, (MACHINE, PAGE)).fetchall()
    print("Komponen lama:", [dict(x) for x in existing])

    conflict = con.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND diagram_page=? AND component_name=?
    """, (MACHINE, PAGE, TITLE)).fetchone()

    if conflict:
        raise SystemExit(f"ERROR: komponen utama sudah ada: {dict(conflict)}")

    for cid, expected in EXPECTED_GROUPS.items():
        c = con.execute("""
            SELECT id, component_name
            FROM components
            WHERE id=? AND machine_id=? AND diagram_page=?
        """, (cid, MACHINE, PAGE)).fetchone()

        if not c:
            raise SystemExit(f"ERROR: subassembly ID {cid} tidak ditemukan")

        actual = con.execute("""
            SELECT p.catalog_ref
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY CAST(p.catalog_ref AS INTEGER)
        """, (cid,)).fetchall()

        actual_refs = [
            int(r["catalog_ref"])
            for r in actual
            if str(r["catalog_ref"]).isdigit()
        ]

        if actual_refs != expected:
            raise SystemExit(
                f"ERROR: REF subassembly ID {cid} tidak sesuai: {actual_refs}"
            )

        print(
            f"Subassembly ID {cid}: {c['component_name']} "
            f"| {len(actual_refs)} relasi | REF {expected[0]}-{expected[-1]}"
        )

    print("Relasi komponen utama yang akan dibuat:", len(parts))

    if not APPLY:
        print("\nDRY-RUN BERHASIL. Database belum diubah.")
        print("Jika benar, jalankan dengan --apply.")
        raise SystemExit(0)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.with_name(
        f"garment-before-lbh1790an-diagram3-main-{stamp}.db"
    )

    b = sqlite3.connect(backup)
    con.backup(b)
    b.close()
    print("\nBackup:", backup)

    try:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components
                (machine_id, component_name, catalog_ref,
                 diagram_page, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (MACHINE, TITLE, "3", PAGE, IMAGE_PATH))

        main_id = cur.lastrowid

        for p in parts:
            ref = int(p["catalog_ref"])
            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, ?, ?)
            """, (
                main_id,
                p["id"],
                "catalog_component_part",
                f"REF {ref}"
            ))

        con.commit()

        print("\nIMPORT BERHASIL")
        print("Komponen utama ID:", main_id)
        print("Jumlah relasi:", len(parts))

    except Exception:
        con.rollback()
        raise

finally:
    con.close()
