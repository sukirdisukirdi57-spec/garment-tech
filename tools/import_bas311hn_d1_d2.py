#!/usr/bin/env python3
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
MACHINE_ID = 227
DOCUMENT_ID = 582
SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/"
    "-/media/ap2/ism/pdf/parts-book-download/"
    "bas311hn_326h_pb.pdf?rev=-1"
)
PARENT_COMPONENT_ID = 528

TARGETS = (
    {
        "page": 23,
        "name": "D1 - Work clamp lifter mechanism",
        "expected_parts": 58,
        "expected_linked": 21,
        "function": "Work clamp lifter mechanism",
    },
    {
        "page": 25,
        "name": "D2 - Work clamp lifter mechanism (311HN-0[]S)",
        "expected_parts": 59,
        "expected_linked": 18,
        "function": "Work clamp lifter mechanism",
    },
)


def stop(message):
    raise RuntimeError(message)


def validate(con):
    doc = con.execute("""
        SELECT machine_id, document_type, source_url
        FROM documents
        WHERE id = ?
    """, (DOCUMENT_ID,)).fetchone()

    if not doc:
        stop(f"Dokumen ID {DOCUMENT_ID} tidak ditemukan.")
    if doc["machine_id"] != MACHINE_ID:
        stop("Dokumen sumber bukan milik mesin ID 227.")
    if doc["document_type"] != "parts_catalog":
        stop("Dokumen sumber bukan parts_catalog.")
    if doc["source_url"] != SOURCE_URL:
        stop("URL dokumen sumber tidak cocok.")

    parent = con.execute("""
        SELECT id FROM components
        WHERE id = ? AND machine_id = ?
    """, (PARENT_COMPONENT_ID, MACHINE_ID)).fetchone()
    if not parent:
        stop("Komponen induk ID 528 tidak ditemukan.")

    for target in TARGETS:
        page = target["page"]
        expected = target["expected_parts"]

        existing_component = con.execute("""
            SELECT id FROM components
            WHERE machine_id = ? AND component_name = ?
        """, (MACHINE_ID, target["name"])).fetchone()
        if existing_component:
            stop(f"Komponen target sudah ada: {target['name']}.")

        rows = con.execute("""
            SELECT p.id, p.catalog_ref, p.source_document_id,
                   COUNT(cp.id) AS rel_count,
                   SUM(CASE WHEN cp.component_id = ? THEN 1 ELSE 0 END)
                       AS parent_rel_count
            FROM parts p
            LEFT JOIN component_parts cp ON cp.part_id = p.id
            WHERE p.machine_id = ? AND p.diagram_page = ?
            GROUP BY p.id, p.catalog_ref, p.source_document_id
            ORDER BY p.catalog_ref
        """, (PARENT_COMPONENT_ID, MACHINE_ID, page)).fetchall()

        if len(rows) != expected:
            stop(
                f"Halaman {page}: ditemukan {len(rows)} part, "
                f"seharusnya {expected}."
            )

        refs = [r["catalog_ref"] for r in rows]
        if refs != list(range(1, expected + 1)):
            stop(f"Halaman {page}: catalog_ref tidak berurutan 1–{expected}.")

        linked = 0
        for r in rows:
            if r["source_document_id"] != DOCUMENT_ID:
                stop(
                    f"Part ID {r['id']} halaman {page} "
                    "memiliki source_document_id berbeda."
                )
            if r["rel_count"] > 1:
                stop(f"Part ID {r['id']} memiliki relasi ganda.")
            if r["rel_count"] == 1:
                if r["parent_rel_count"] != 1:
                    stop(
                        f"Part ID {r['id']} terhubung ke komponen selain "
                        "komponen induk 528."
                    )
                linked += 1

        if linked != target["expected_linked"]:
            stop(
                f"Halaman {page}: relasi lama {linked}, "
                f"seharusnya {target['expected_linked']}."
            )

        print(
            f"Halaman {page}: {len(rows)} part; "
            f"{linked} relasi lama; "
            f"{len(rows) - linked} belum terhubung — LULUS"
        )

    # Pastikan relasi halaman 15 tidak disentuh oleh rencana ini.
    page15 = con.execute("""
        SELECT COUNT(*)
        FROM parts p
        JOIN component_parts cp ON cp.part_id = p.id
        WHERE p.machine_id = ? AND p.diagram_page = 15
          AND cp.component_id = ?
    """, (MACHINE_ID, PARENT_COMPONENT_ID)).fetchone()[0]

    if page15 != 53:
        stop(
            f"Relasi halaman 15 pada komponen 528 berjumlah {page15}, "
            "bukan 53; hentikan untuk pemeriksaan manual."
        )

    print("Dokumen sumber: LULUS")
    print("Komponen induk: LULUS")
    print("Relasi halaman 15: 53 tetap terjaga — LULUS")


def main():
    parser = argparse.ArgumentParser(
        description="Validasi dan relasi ulang part D1/D2 BAS-311HN-03S."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Terapkan perubahan setelah validasi.",
    )
    args = parser.parse_args()

    if not DB.is_file():
        stop(f"Database tidak ditemukan: {DB}")

    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")

    try:
        print("=== VALIDASI AWAL ===")
        validate(con)

        print("\n=== RENCANA ===")
        print("- Buat 2 komponen: D1 dan D2.")
        print("- Pertahankan semua 117 baris part.")
        print("- Pindahkan 39 relasi lama dari komponen 528.")
        print("- Tambahkan 78 relasi yang belum ada.")
        print("- Target akhir: D1 = 58 relasi; D2 = 59 relasi.")
        print("- Tidak mengubah relasi halaman 15.")

        if not args.apply:
            print("\nDRY-RUN LULUS — database tidak diubah.")
            print("Periksa hasil ini sebelum menjalankan dengan --apply.")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / (
            "garment-before-bas311hn-d1-d2-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        backup = sqlite3.connect(backup_path)
        try:
            con.backup(backup)
        finally:
            backup.close()
        print("\nCadangan database:", backup_path)

        try:
            con.execute("BEGIN IMMEDIATE")
            validate(con)

            component_ids = {}
            for target in TARGETS:
                cur = con.execute("""
                    INSERT INTO components (
                        machine_id, component_name, function, notes,
                        source_url, diagram_page
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID,
                    target["name"],
                    target["function"],
                    (
                        "Brother BAS-311HN/326H Parts Book, "
                        f"halaman cetak {target['page']}. "
                        "Relasi dipisahkan dari komponen induk 528."
                    ),
                    SOURCE_URL,
                    target["page"],
                ))
                component_ids[target["page"]] = cur.lastrowid

            for target in TARGETS:
                page = target["page"]
                component_id = component_ids[page]

                # Pindahkan relasi yang sudah ada, tanpa membuat part baru.
                con.execute("""
                    UPDATE component_parts
                    SET component_id = ?
                    WHERE component_id = ?
                      AND part_id IN (
                          SELECT id FROM parts
                          WHERE machine_id = ? AND diagram_page = ?
                      )
                """, (
                    component_id, PARENT_COMPONENT_ID, MACHINE_ID, page
                ))

                # Tambahkan relasi hanya untuk part yang belum terhubung.
                con.execute("""
                    INSERT INTO component_parts
                        (component_id, part_id, relation_type, notes)
                    SELECT ?, p.id, 'catalog_section', ?
                    FROM parts p
                    WHERE p.machine_id = ? AND p.diagram_page = ?
                      AND NOT EXISTS (
                          SELECT 1 FROM component_parts cp
                          WHERE cp.part_id = p.id
                      )
                """, (
                    component_id,
                    f"Brother BAS-311HN/326H Parts Book, halaman {page}.",
                    MACHINE_ID,
                    page,
                ))

                count = con.execute("""
                    SELECT COUNT(*)
                    FROM component_parts cp
                    JOIN parts p ON p.id = cp.part_id
                    WHERE cp.component_id = ?
                      AND p.machine_id = ? AND p.diagram_page = ?
                """, (component_id, MACHINE_ID, page)).fetchone()[0]

                if count != target["expected_parts"]:
                    stop(
                        f"Verifikasi akhir halaman {page} gagal: {count} relasi."
                    )

            # Pastikan jumlah part tidak berubah dan halaman 15 tetap aman.
            for target in TARGETS:
                count = con.execute("""
                    SELECT COUNT(*) FROM parts
                    WHERE machine_id = ? AND diagram_page = ?
                """, (MACHINE_ID, target["page"])).fetchone()[0]
                if count != target["expected_parts"]:
                    stop(f"Jumlah part halaman {target['page']} berubah.")

            page15 = con.execute("""
                SELECT COUNT(*)
                FROM parts p
                JOIN component_parts cp ON cp.part_id = p.id
                WHERE p.machine_id = ? AND p.diagram_page = 15
                  AND cp.component_id = ?
            """, (MACHINE_ID, PARENT_COMPONENT_ID)).fetchone()[0]
            if page15 != 53:
                stop("Verifikasi akhir halaman 15 gagal.")

            con.commit()
            print("\nAPPLY BERHASIL")
            for target in TARGETS:
                print(
                    f"{target['name']}: "
                    f"component_id={component_ids[target['page']]}, "
                    f"relasi={target['expected_parts']}"
                )
            print("Jumlah part halaman 23/25 tidak berubah.")
            print("Relasi halaman 15 tetap 53.")
        except Exception:
            con.rollback()
            raise
    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nGAGAL: {exc}", file=sys.stderr)
        sys.exit(1)
