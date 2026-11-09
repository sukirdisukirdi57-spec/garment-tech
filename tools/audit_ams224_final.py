import sqlite3
import re
from pathlib import Path

DB = "database/garment.db"
MACHINE_ID = 47

EXPECTED_SECTIONS = (
    [1, 2]
    + list(range(4, 14))
    + list(range(15, 28))
)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

components = con.execute("""
    SELECT *
    FROM components
    WHERE machine_id=?
    ORDER BY CAST(catalog_ref AS INTEGER)
""", (MACHINE_ID,)).fetchall()

errors = []
total_parts = 0
total_relations = 0

print("=== AUDIT FINAL AMS-224EN-6030 ===")
print("Jumlah komponen:", len(components))

actual_sections = [
    int(c["catalog_ref"])
    for c in components
]

print("Section yang tersedia:", actual_sections)
print("Section yang diharapkan:", EXPECTED_SECTIONS)

if sorted(actual_sections) != EXPECTED_SECTIONS:
    errors.append("Daftar section tidak sesuai")

for c in components:
    section = int(c["catalog_ref"])
    rows = con.execute("""
        SELECT
            cp.notes AS relation_note,
            cp.relation_type,
            p.part_number,
            p.part_name,
            p.catalog_ref,
            p.quantity_raw
        FROM component_parts cp
        JOIN parts p ON p.id=cp.part_id
        WHERE cp.component_id=?
        ORDER BY CAST(p.catalog_ref AS INTEGER)
    """, (c["id"],)).fetchall()

    refs = []
    section_errors = []

    for r in rows:
        match = re.fullmatch(
            r"(?:Catalog )?REF\s+0*(\d+)",
            (r["relation_note"] or "").strip()
        )

        if not match:
            section_errors.append(
                f"Format relasi REF salah: {r['relation_note']}"
            )
            continue

        ref = int(match.group(1))
        refs.append(ref)

        if r["catalog_ref"] is None or int(r["catalog_ref"]) != ref:
            section_errors.append(
                f"REF {ref}: parts.catalog_ref tidak cocok"
            )

        if r["relation_type"] != "catalog_component_part":
            section_errors.append(
                f"REF {ref}: relation_type salah"
            )

        if not r["part_number"] or not r["part_name"]:
            section_errors.append(
                f"REF {ref}: nomor/nama part kosong"
            )

        if r["quantity_raw"] is None:
            section_errors.append(
                f"REF {ref}: quantity_raw kosong"
            )

    if section == 17:
        expected_refs = [
            n for n in range(1, 63)
            if n not in (28, 46, 52)
        ]
    else:
        expected_refs = list(range(1, len(rows) + 1))

    if refs != expected_refs:
        section_errors.append(
            f"Daftar REF tidak sesuai: aktual {refs}"
        )

    image_path = c["image_path"]
    image_exists = bool(
        image_path and
        (Path("static") / image_path).is_file()
    )

    if not image_exists:
        section_errors.append(
            f"Diagram tidak ditemukan: {image_path}"
        )

    total_parts += len(rows)
    total_relations += len(rows)

    status = "VALID" if not section_errors else "MASALAH"

    print(
        f"Section {section:02d} | "
        f"ID {c['id']} | "
        f"REF {len(rows):02d} | "
        f"Diagram {'OK' if image_exists else 'GAGAL'} | "
        f"{status} | "
        f"{c['component_name']}"
    )

    for err in section_errors:
        errors.append(f"Section {section}: {err}")

orphan_parts = con.execute("""
    SELECT COUNT(*)
    FROM parts p
    WHERE p.machine_id=?
      AND NOT EXISTS (
          SELECT 1
          FROM component_parts cp
          WHERE cp.part_id=p.id
      )
""", (MACHINE_ID,)).fetchone()[0]

invalid_relations = con.execute("""
    SELECT COUNT(*)
    FROM component_parts cp
    JOIN components c ON c.id=cp.component_id
    WHERE c.machine_id=?
      AND cp.relation_type != 'catalog_component_part'
""", (MACHINE_ID,)).fetchone()[0]

db_parts = con.execute("""
    SELECT COUNT(*) FROM parts WHERE machine_id=?
""", (MACHINE_ID,)).fetchone()[0]

db_relations = con.execute("""
    SELECT COUNT(*)
    FROM component_parts cp
    JOIN components c ON c.id=cp.component_id
    WHERE c.machine_id=?
""", (MACHINE_ID,)).fetchone()[0]

print("\n=== RINGKASAN ===")
print("Total occurrence dari komponen:", total_parts)
print("Total parts database:", db_parts)
print("Total relasi database:", db_relations)
print("Parts tanpa relasi:", orphan_parts)
print("Relasi dengan tipe salah:", invalid_relations)

if total_parts != db_parts:
    errors.append("Jumlah occurrence tidak sama dengan jumlah parts")

if total_relations != db_relations:
    errors.append("Jumlah relasi tidak sama dengan jumlah occurrence")

if orphan_parts:
    errors.append("Ada parts tanpa relasi")

if invalid_relations:
    errors.append("Ada relation_type yang tidak sesuai")

print("\n=== HASIL AKHIR ===")

if errors:
    print("AUDIT BELUM LULUS")
    for e in errors:
        print("-", e)
else:
    print("AUDIT LULUS")
    print("Seluruh section, REF, relasi, dan diagram konsisten.")

con.close()
