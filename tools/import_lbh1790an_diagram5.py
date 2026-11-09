import sqlite3
import shutil
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram5.png")
IMAGE_PATH = "component_images/lbh1790an_diagram5.png"

MACHINE_ID = 6
PAGE = 9
TITLE = "5. PRESSER & FEED COMPONENT"

GROUPS = [
    (12, "FEED_BASE_ASM", "400-04203", list(range(12, 15))),
    (15, "THRUST_COLLAR_ASM.", "400-10434", list(range(15, 18))),
    (29, "LIFTING_LINK_ASSY", "401-42161", list(range(29, 34))),
    (70, "WORK CLAMP CHECK HOLDER ASM.", "D1511-771-KA0-A", list(range(70, 75))),
]

APPLY = "--apply" in sys.argv

if not DB.exists():
    raise SystemExit("ERROR: database tidak ditemukan")
if not IMAGE.exists():
    raise SystemExit("ERROR: gambar diagram tidak ditemukan")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    rows = con.execute("""
        SELECT id, catalog_ref, part_number, part_name
        FROM parts
        WHERE machine_id=? AND diagram_page=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, PAGE)).fetchall()

    refs = [int(r["catalog_ref"]) for r in rows
            if str(r["catalog_ref"]).isdigit()]

    if len(rows) != 80 or sorted(refs) != list(range(1, 81)):
        raise SystemExit(
            f"ERROR: data REF tidak lengkap/duplikat. "
            f"Baris={len(rows)}, REF unik={len(set(refs))}"
        )

    part_by_ref = {int(r["catalog_ref"]): r for r in rows}

    for ref, name, part_number, members in GROUPS:
        row = part_by_ref[ref]
        if row["part_number"] != part_number:
            raise SystemExit(f"ERROR: part number REF {ref} tidak cocok")
        if row["part_name"] != name:
            raise SystemExit(f"ERROR: nama REF {ref} tidak cocok: {row['part_name']}")

    existing = con.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND diagram_page=?
    """, (MACHINE_ID, PAGE)).fetchall()

    print("=== PREFLIGHT IMPORT DIAGRAM 5 ===")
    print("Judul:", TITLE)
    print("Jumlah REF:", len(rows))
    print("Komponen lama:", [dict(x) for x in existing])
    print("Komponen utama baru:", TITLE)
    print("Subassembly:", len(GROUPS))
    print("Relasi komponen utama:", 80)
    print("Relasi subassembly:", sum(len(g[3]) for g in GROUPS))
    print("Total relasi baru:", 80 + sum(len(g[3]) for g in GROUPS))

    for ref, name, pn, members in GROUPS:
        print(f"  REF {ref}: {name} -> REF {members[0]}-{members[-1]}")

    if not APPLY:
        print("\nDRY-RUN BERHASIL. Database belum diubah.")
        print("Jika hasil sudah benar, jalankan dengan --apply.")
        raise SystemExit(0)

    target_names = [TITLE] + [g[1] for g in GROUPS]
    conflicts = con.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND diagram_page=?
          AND component_name IN ({})
    """.format(",".join("?" for _ in target_names)),
        (MACHINE_ID, PAGE, *target_names)
    ).fetchall()

    if conflicts:
        raise SystemExit(
            f"ERROR: komponen target sudah ada: {[dict(x) for x in conflicts]}"
        )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.with_name(f"garment-before-lbh1790an-diagram5-{stamp}.db")

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()
    print("\nBackup:", backup)

    try:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components
                (machine_id, component_name, catalog_ref,
                 diagram_page, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (MACHINE_ID, TITLE, "5", PAGE, IMAGE_PATH))

        main_id = cur.lastrowid

        for r in rows:
            ref = int(r["catalog_ref"])
            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, ?, ?)
            """, (main_id, r["id"], "catalog_component_part", f"REF {ref}"))

        sub_ids = {}

        for ref, name, pn, members in GROUPS:
            cur = con.execute("""
                INSERT INTO components
                    (machine_id, component_name, part_number,
                     catalog_ref, diagram_page, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (MACHINE_ID, name, pn, str(ref), PAGE, IMAGE_PATH))

            sub_id = cur.lastrowid
            sub_ids[ref] = sub_id

            for member_ref in members:
                part = part_by_ref[member_ref]
                con.execute("""
                    INSERT INTO component_parts
                        (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, ?, ?)
                """, (
                    sub_id, part["id"],
                    "catalog_component_part",
                    f"REF {member_ref}"
                ))

        con.commit()

        print("\nIMPORT BERHASIL")
        print("Komponen utama ID:", main_id)
        print("Subassembly IDs:", sub_ids)

    except Exception:
        con.rollback()
        print("IMPORT GAGAL: transaksi dibatalkan.")
        raise

finally:
    con.close()
