import sqlite3
import os
import sys
from datetime import datetime

DB = "database/garment.db"
IMAGE = "component_images/lbh1790an_diagram7.png"
PAGE = 13
MACHINE_ID = 6
DOC_ID = 119

MAIN_NAME = "7. NEEDLE BAR ROCKING COMPONENTS"

ASSEMBLIES = [
    {
        "name": "ZIGZAG ROD ASM.",
        "parent": 2,
        "refs": [2, 3, 4],
    },
    {
        "name": "ZIGZAG LEVER SHAFT ASM.",
        "parent": 21,
        "refs": [21, 22, 23, 24],
    },
    {
        "name": "NEEDLE_BAR_FRAME_ASSY",
        "parent": 29,
        "refs": [29, 30, 31],
    },
]

def fail(message):
    raise RuntimeError(message)

if not os.path.exists(DB):
    fail(f"Database tidak ditemukan: {DB}")

if not os.path.exists("static/" + IMAGE):
    fail(f"Gambar tidak ditemukan: static/{IMAGE}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    print("=== PREFLIGHT DIAGRAM 7 ===")
    print("Judul:", MAIN_NAME)

    parts = con.execute("""
        SELECT id, catalog_ref, part_number, part_name
        FROM parts
        WHERE machine_id=? AND source_document_id=?
          AND diagram_page=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, DOC_ID, PAGE)).fetchall()

    refs = [int(p["catalog_ref"]) for p in parts]

    if len(parts) != 35:
        fail(f"Jumlah part harus 35, ditemukan {len(parts)}")

    if refs != list(range(1, 36)):
        fail(f"REF tidak lengkap/berurutan: {refs}")

    part_by_ref = {}
    for p in parts:
        ref = int(p["catalog_ref"])
        if ref in part_by_ref:
            fail(f"REF {ref} memiliki lebih dari satu baris part")
        part_by_ref[ref] = p

    print("Jumlah REF utama:", len(refs))
    print("REF:", refs)

    target_names = [MAIN_NAME] + [
        a["name"] for a in ASSEMBLIES
    ]

    for name in target_names:
        existing = con.execute("""
            SELECT id FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID, name)).fetchall()

        if existing:
            fail(f"Komponen target sudah ada: {name} { [r['id'] for r in existing] }")

    old = con.execute("""
        SELECT id, component_name, catalog_ref
        FROM components
        WHERE machine_id=? AND diagram_page=?
        ORDER BY id
    """, (MACHINE_ID, PAGE)).fetchall()

    print("\nKomponen lama:")
    for row in old:
        print(dict(row))

    print("\n=== VALIDASI SUBASSEMBLY ===")
    for a in ASSEMBLIES:
        expected = a["refs"]
        if a["parent"] not in expected:
            fail(f"REF induk tidak ada dalam kelompok: {a['name']}")

        for ref in expected:
            if ref not in part_by_ref:
                fail(f"Part REF {ref} tidak ditemukan")

        print(
            f"{a['name']} | induk REF {a['parent']} "
            f"| anggota REF {expected} | {len(expected)} relasi"
        )

    total = 35 + sum(len(a["refs"]) for a in ASSEMBLIES)

    print("\nRelasi komponen utama:", 35)
    print("Total relasi subassembly:", total - 35)
    print("Total seluruh relasi yang akan dibuat:", total)
    print("Gambar tersedia:", os.path.exists("static/" + IMAGE))

    if "--apply" not in sys.argv:
        print("\nDRY-RUN BERHASIL. Database belum diubah.")
        print("Jika benar, jalankan dengan --apply.")
        sys.exit(0)

    backup = (
        "database/garment-before-lbh1790an-diagram7-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".db"
    )

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()
    print("\nBackup:", backup)

    try:
        con.execute("BEGIN IMMEDIATE")

        def create_component(name, parent_ref, catalog_ref):
            parent = part_by_ref[parent_ref]

            cur = con.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, ?, NULL, NULL, NULL, ?, NULL, ?, ?)
            """, (
                MACHINE_ID,
                name,
                parent["part_number"],
                IMAGE,
                str(catalog_ref),
                PAGE,
            ))
            return cur.lastrowid

        main_id = create_component(MAIN_NAME, 1, "7")

        for ref in range(1, 36):
            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, 'catalog_component_part', ?)
            """, (main_id, part_by_ref[ref]["id"], f"REF {ref}"))

        print("\nKomponen utama ID:", main_id)

        for a in ASSEMBLIES:
            cid = create_component(
                a["name"], a["parent"], str(a["parent"])
            )

            for ref in a["refs"]:
                con.execute("""
                    INSERT INTO component_parts
                        (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, 'catalog_component_part', ?)
                """, (cid, part_by_ref[ref]["id"], f"REF {ref}"))

            print(
                f"Subassembly ID {cid}: {a['name']} "
                f"| {len(a['refs'])} relasi"
            )

        con.commit()
        print("\nIMPORT BERHASIL")
        print("Komponen utama ID:", main_id)
        print("Jumlah relasi utama: 35")

    except Exception:
        con.rollback()
        raise

except Exception as e:
    print("\nPREFLIGHT / IMPORT GAGAL:", e)
    sys.exit(1)

finally:
    con.close()
