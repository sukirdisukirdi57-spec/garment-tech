import sqlite3
import os
import sys
import shutil
from datetime import datetime
from collections import Counter

DB = "database/garment.db"

# component_id: (part_id, part_number, catalog_ref, diagram_page, image_path)
FIXES = {
    222: (1753, "225-28764", "41", 1, "component_images/lbh1790an_diagram1.png"),
    223: (1754, "225-02504", "42", 1, "component_images/lbh1790an_diagram1.png"),
    224: (1759, "139-22208", "47", 1, "component_images/lbh1790an_diagram1.png"),
    225: (1781, "137-05405", "69", 1, "component_images/lbh1790an_diagram1.png"),
    226: (1785, "401-11214", "73", 1, "component_images/lbh1790an_diagram1.png"),

    227: (1821, "400-06265", "23", 3, "component_images/lbh1790an_diagram2.png"),
    228: (1857, "225-29481", "59", 3, "component_images/lbh1790an_diagram2.png"),
    229: (1850, "400-37008", "52", 3, "component_images/lbh1790an_diagram2.png"),

    230: (1883, "401-38137", "22", 5, "component_images/lbh1790an_diagram3.png"),

    231: (1913, "137-29066", "13", 7, "component_images/lbh1790an_diagram4.png"),
    232: (1928, "B1811-771-000", "28", 7, "component_images/lbh1790an_diagram4.png"),
    233: (1929, "137-29769", "29", 7, "component_images/lbh1790an_diagram4.png"),

    237: (1935, "HD-0005700-0A", "2", 9, "component_images/lbh1790an_diagram5.png"),
    238: (2004, "B1511-771-000-B", "71", 9, "component_images/lbh1790an_diagram5.png"),

    239: (2029, "MDP-5J0B1100", "16", 13, "component_images/lbh1790an_diagram7.png"),

    234: (2333, "402-58041", "14", 27, "component_images/lbh1790an_diagram15.png"),
    235: (2334, "402-58042", "15", 27, "component_images/lbh1790an_diagram15.png"),
    236: (2332, "402-58040", "13", 27, "component_images/lbh1790an_diagram15.png"),
    240: (2337, "402-58043", "18", 27, "component_images/lbh1790an_diagram15.png"),
}

APPLY = "--apply" in sys.argv

def main():
    if not os.path.isfile(DB):
        raise SystemExit(f"Database tidak ditemukan: {DB}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    errors = []
    image_updates = []
    relation_inserts = []
    already_linked = []

    print("=== PREFLIGHT LEGACY COMPONENTS LBH-1790AN ===")
    print("Mode:", "APPLY" if APPLY else "DRY-RUN")
    print("Jumlah target:", len(FIXES))

    for cid, data in FIXES.items():
        part_id, part_number, ref, page, image_path = data

        c = cur.execute("""
            SELECT id, machine_id, component_name, part_number,
                   catalog_ref, diagram_page, image_path
            FROM components WHERE id = ?
        """, (cid,)).fetchone()

        if not c:
            errors.append(f"Komponen ID {cid} tidak ditemukan")
            continue

        if c["machine_id"] != 6:
            errors.append(f"Komponen ID {cid} bukan machine_id 6")
            continue

        if c["part_number"] != part_number:
            errors.append(
                f"Part number komponen {cid} tidak sesuai: {c['part_number']}"
            )
            continue

        if str(c["catalog_ref"]) != ref or c["diagram_page"] != page:
            errors.append(
                f"REF/diagram komponen {cid} tidak sesuai: "
                f"REF {c['catalog_ref']} page {c['diagram_page']}"
            )
            continue

        p = cur.execute("""
            SELECT id, machine_id, part_number, part_name,
                   catalog_ref, diagram_page
            FROM parts WHERE id = ?
        """, (part_id,)).fetchone()

        if not p:
            errors.append(f"Part ID {part_id} tidak ditemukan")
            continue

        if (
            p["machine_id"] != 6
            or p["part_number"] != part_number
            or str(p["catalog_ref"]) != ref
            or p["diagram_page"] != page
        ):
            errors.append(f"Data part ID {part_id} tidak cocok dengan komponen {cid}")
            continue

        full_image = os.path.join("static", image_path)
        if not os.path.isfile(full_image):
            errors.append(f"Gambar tidak ditemukan: {full_image}")
            continue

        if c["image_path"] != image_path:
            image_updates.append((cid, image_path))

        existing = cur.execute("""
            SELECT id FROM component_parts
            WHERE component_id = ? AND part_id = ?
        """, (cid, part_id)).fetchone()

        if existing:
            already_linked.append((cid, part_id))
        else:
            relation_inserts.append((cid, part_id, f"REF {ref}"))

        print(
            f"OK | Component {cid} | {c['component_name']} "
            f"| Part {part_id} | REF {ref} | {image_path}"
        )

    print("\n=== RINGKASAN PREFLIGHT ===")
    print("Gambar yang perlu diisi :", len(image_updates))
    print("Relasi yang perlu dibuat:", len(relation_inserts))
    print("Relasi sudah ada        :", len(already_linked))
    print("Kesalahan               :", len(errors))

    if errors:
        for e in errors:
            print("ERROR:", e)
        conn.close()
        raise SystemExit("PREFLIGHT GAGAL. Database tidak diubah.")

    if not APPLY:
        print("\nDRY-RUN LULUS. Belum ada perubahan database.")
        print("Jika hasil ini sesuai, jalankan dengan --apply.")
        conn.close()
        return

    # Backup sebelum perubahan
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"database/garment-before-lbh-legacy-fix-{stamp}.db"
    conn.commit()
    conn.close()
    shutil.copy2(DB, backup)
    print("\nBackup dibuat:", backup)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("BEGIN IMMEDIATE")

        for cid, image_path in image_updates:
            cur.execute("""
                UPDATE components
                SET image_path = ?
                WHERE id = ? AND machine_id = 6
            """, (image_path, cid))

        for cid, part_id, note in relation_inserts:
            cur.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, 'catalog_component_part', ?)
            """, (cid, part_id, note))

        conn.commit()
        print("Perubahan berhasil disimpan.")

    except Exception:
        conn.rollback()
        raise

    # Validasi hasil
    print("\n=== VALIDASI SETELAH APPLY ===")
    failed = []

    for cid, data in FIXES.items():
        part_id, part_number, ref, page, image_path = data

        c = cur.execute("""
            SELECT image_path FROM components
            WHERE id = ? AND machine_id = 6
        """, (cid,)).fetchone()

        rel = cur.execute("""
            SELECT COUNT(*) FROM component_parts
            WHERE component_id = ? AND part_id = ?
        """, (cid, part_id)).fetchone()[0]

        if not c or c["image_path"] != image_path or rel != 1:
            failed.append(cid)

    integrity = cur.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()

    print("Target komponen:", len(FIXES))
    print("Validasi gagal :", failed)
    print("Integrity check:", integrity)

    if failed or integrity != "ok":
        raise SystemExit("PERHATIAN: validasi akhir gagal. Periksa backup.")

    print("HASIL: LULUS")

if __name__ == "__main__":
    main()
