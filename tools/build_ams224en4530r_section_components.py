#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")

MACHINE_ID = 46
DOCUMENT_ID = 162

# Section: judul resmi, halaman diagram, ekstensi gambar
SECTIONS = {
    1: ("FRAME & MISCELLANEOUS COVER COMPONENTS (1)", 1, "jpg"),
    2: ("FRAME & MISCELLANEOUS COVER COMPONENTS (2)", 3, "jpg"),
    3: ("FRAME & MISCELLANEOUS COVER COMPONENTS (3)", 5, "jpg"),
    4: ("MAIN SHAFT & NEEDLE BAR COMPONENTS", 7, "png"),
    5: ("PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (1)", 9, "png"),
    6: ("PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (2)", 11, "png"),
    7: ("LOWER SHAFT COMPONENTS (1)", 13, "png"),
    8: ("LOWER SHAFT COMPONENTS (2)", 15, "png"),
    9: ("WIPER MECHANISM COMPONENTS", 17, "jpg"),
    10: ("TENSION RELEASE & THREAD TENSION COMPONENTS", 18, "jpg"),
    11: ("THREAD TRIMMER MECHANISM COMPONENTS", 19, "png"),
    12: ("X-Y COMPONENTS (1)", 21, "png"),
    13: ("X-Y COMPONENTS (2)", 23, "png"),
    14: ("CLOTH FEED MECHANISM COMPONENTS", 25, "jpg"),
    15: ("PNEUMATIC COMPONENTS", 27, "jpg"),
    16: ("THREAD STAND COMPONENTS", 28, "jpg"),
    17: ("OPERATION PANEL COMPONENTS", 29, "jpg"),
    18: ("CONTROL BOX COMPONENTS", 31, "png"),
    19: ("WIRING DIAGRAM", 33, "png"),
    20: ("TABLE COMPONENTS", 35, "png"),
    21: ("PEDAL COMPONENTS", 37, "jpg"),
    22: ("ACCESSORIE PARTS COMPONENTS", 38, "png"),
    23: ("SEPARATE STROKE TYPE EXCLUSIVE PARTS", 39, "png"),
}

EXPECTED_COUNTS = {
    1: 55, 2: 42, 3: 99, 4: 67, 5: 66, 6: 54,
    7: 35, 8: 70, 9: 42, 10: 47, 11: 56, 12: 98,
    13: 12, 14: 58, 15: 24, 16: 34, 17: 36, 18: 62,
    19: 67, 20: 46, 21: 38, 22: 21, 23: 25,
}

IMAGE_DIR = Path("static/component_images")
BACKUP_PREFIX = "garment-before-ams224en4530r-sections-"


def section_from_notes(notes):
    match = re.search(
        r"AMS-224EN-4530R section\s+(\d+)",
        notes or "",
        re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def audit_database(con):
    parts = con.execute("""
        SELECT id, part_number, catalog_ref, notes, source_url
        FROM parts
        WHERE machine_id = ? AND source_document_id = ?
        ORDER BY id
    """, (MACHINE_ID, DOCUMENT_ID)).fetchall()

    grouped = {n: [] for n in SECTIONS}
    errors = []

    for part in parts:
        section = section_from_notes(part["notes"])
        if section not in grouped:
            errors.append(
                f"Part ID {part['id']} memiliki section tidak valid: {section}"
            )
        else:
            grouped[section].append(part)

    if len(parts) != 1154:
        errors.append(f"Jumlah part berubah: {len(parts)}, target 1154")

    for section, expected in EXPECTED_COUNTS.items():
        actual = len(grouped[section])
        if actual != expected:
            errors.append(
                f"Section {section}: ditemukan {actual}, target {expected}"
            )

    document = con.execute("""
        SELECT id, machine_id, document_type, source_url
        FROM documents
        WHERE id = ? AND machine_id = ?
    """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

    source_url = None

    if document is None:
        errors.append(
            f"Dokumen ID {DOCUMENT_ID} tidak ditemukan untuk machine {MACHINE_ID}"
        )
    else:
        if document["document_type"] != "Parts List":
            errors.append(
                f"Tipe dokumen tidak sesuai: {document['document_type']}"
            )

        source_url = document["source_url"]

        if not source_url:
            errors.append(
                f"Source URL dokumen ID {DOCUMENT_ID} kosong"
            )

    for section, (_, page, ext) in SECTIONS.items():
        image = IMAGE_DIR / f"ams224en4530r_page{page}.{ext}"
        if not image.is_file() or image.stat().st_size == 0:
            errors.append(f"Gambar section {section} tidak valid: {image}")

    return parts, grouped, source_url, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Terapkan migrasi ke database",
    )
    args = parser.parse_args()

    if not DB.is_file():
        raise SystemExit(f"Database tidak ditemukan: {DB}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")

    try:
        print("=== PREFLIGHT AMS-224EN-4530R SECTION COMPONENTS ===")
        print("Mode:", "APPLY" if args.apply else "DRY-RUN")

        parts, grouped, source_url, errors = audit_database(con)

        existing_components = con.execute("""
            SELECT id, component_name, catalog_ref,
                   diagram_page, image_path
            FROM components
            WHERE machine_id = ?
            ORDER BY id
        """, (MACHINE_ID,)).fetchall()

        existing_by_name = {
            row["component_name"]: row
            for row in existing_components
        }

        print("Parts:", len(parts))
        print("Komponen lama:", len(existing_components))
        print("Relasi lama:", con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id = cp.component_id
            WHERE c.machine_id = ?
        """, (MACHINE_ID,)).fetchone()[0])

        print("\n=== RENCANA 23 SECTION ===")

        new_component_count = 0
        missing_relation_count = 0

        for section, (title, page, ext) in SECTIONS.items():
            image_path = f"component_images/ams224en4530r_page{page}.{ext}"
            existing = existing_by_name.get(title)

            if existing:
                if (
                    existing["diagram_page"] != page
                    or existing["image_path"] != image_path
                ):
                    errors.append(
                        f"Metadata komponen existing tidak cocok: {title}"
                    )
                component_id = existing["id"]
                status = f"SUDAH ADA ID {component_id}"
            else:
                component_id = None
                new_component_count += 1
                status = "BARU"

            linked = 0
            if component_id is not None:
                linked = con.execute("""
                    SELECT COUNT(*)
                    FROM component_parts
                    WHERE component_id = ?
                """, (component_id,)).fetchone()[0]

            missing_relation_count += len(grouped[section]) - linked

            print(
                f"Section {section:2} | {status:16} | "
                f"{len(grouped[section]):3} parts | "
                f"Diagram {page:2} | {title}"
            )

        if errors:
            print("\n=== PREFLIGHT GAGAL ===")
            for error in errors:
                print("ERROR:", error)
            raise SystemExit("Database tidak diubah.")

        print("\n=== RINGKASAN ===")
        print("Komponen baru:", new_component_count)
        print("Relasi section yang belum ada:", missing_relation_count)
        print("Target part:", len(parts))
        print("Source URL:", source_url)

        if not args.apply:
            print("\nDRY-RUN BERHASIL. Database belum diubah.")
            return

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = BACKUP_DIR / f"{BACKUP_PREFIX}{timestamp}.db"

        con.close()
        shutil.copy2(DB, backup)
        print("\nBackup:", backup)

        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")

        try:
            con.execute("BEGIN IMMEDIATE")

            component_ids = {}

            for section, (title, page, ext) in SECTIONS.items():
                image_path = (
                    f"component_images/ams224en4530r_page{page}.{ext}"
                )

                existing = con.execute("""
                    SELECT id
                    FROM components
                    WHERE machine_id = ? AND component_name = ?
                """, (MACHINE_ID, title)).fetchone()

                if existing:
                    component_id = existing["id"]
                else:
                    cursor = con.execute("""
                        INSERT INTO components (
                            machine_id,
                            component_name,
                            notes,
                            image_path,
                            source_url,
                            catalog_ref,
                            diagram_page
                        )
                        VALUES (?, ?, ?, ?, ?, NULL, ?)
                    """, (
                        MACHINE_ID,
                        title,
                        f"Main section component; official Parts List section {section}",
                        image_path,
                        source_url,
                        page,
                    ))
                    component_id = cursor.lastrowid

                component_ids[section] = component_id

            inserted_relations = 0

            for section, section_parts in grouped.items():
                component_id = component_ids[section]

                for part in section_parts:
                    cursor = con.execute("""
                        INSERT OR IGNORE INTO component_parts (
                            component_id,
                            part_id,
                            relation_type,
                            notes
                        )
                        VALUES (?, ?, 'catalog_component_part', ?)
                    """, (
                        component_id,
                        part["id"],
                        f"SECTION {section}; REF {part['catalog_ref']}",
                    ))
                    inserted_relations += cursor.rowcount

            # Validasi dalam transaksi sebelum commit.
            for section, section_parts in grouped.items():
                count = con.execute("""
                    SELECT COUNT(*)
                    FROM component_parts
                    WHERE component_id = ?
                """, (component_ids[section],)).fetchone()[0]

                if count != len(section_parts):
                    raise RuntimeError(
                        f"Relasi section {section}: {count}, "
                        f"seharusnya {len(section_parts)}"
                    )

            con.commit()

        except Exception:
            con.rollback()
            raise

        total_components = con.execute("""
            SELECT COUNT(*)
            FROM components
            WHERE machine_id = ?
        """, (MACHINE_ID,)).fetchone()[0]

        total_relations = con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id = cp.component_id
            WHERE c.machine_id = ?
        """, (MACHINE_ID,)).fetchone()[0]

        total_parts = con.execute("""
            SELECT COUNT(*)
            FROM parts
            WHERE machine_id = ? AND source_document_id = ?
        """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]

        print("\n=== HASIL APPLY ===")
        print("Relasi baru:", inserted_relations)
        print("Total komponen machine 46:", total_components)
        print("Total relasi machine 46:", total_relations)
        print("Total part Parts List:", total_parts)
        print("SQLite integrity:", integrity)

        if (
            total_components != 47
            or total_relations != 1358
            or total_parts != 1154
            or integrity != "ok"
        ):
            raise RuntimeError(
                "Hasil akhir tidak sesuai target. Backup tetap tersedia."
            )

        # Pertahankan maksimal 10 backup migrasi ini.
        backups = sorted(
            BACKUP_DIR.glob(f"{BACKUP_PREFIX}*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[10:]:
            old_backup.unlink()
            print("Backup lama dihapus:", old_backup)

        print("\nMIGRASI BERHASIL.")

    finally:
        con.close()


if __name__ == "__main__":
    main()
