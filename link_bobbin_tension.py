import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db_path = Path("database/garment.db")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_path = Path(f"database/garment-before-bobbin-tension-{timestamp}.db")

component_id = 569

targets = [
    (7182, "NS-6110310-SP", 29),
    (7184, "B3126-012-000", 31),
    (7185, "D7133-555-B00", 32),
    (7186, "110-72402", 33),
]

# Buat backup sebelum perubahan
shutil.copy2(db_path, backup_path)
print(f"Backup: {backup_path}")

db = sqlite3.connect(db_path)

try:
    db.execute("BEGIN IMMEDIATE")

    component = db.execute("""
        SELECT id, component_name
        FROM components
        WHERE id = ? AND machine_id = 44
    """, (component_id,)).fetchone()

    if not component or component[1] != "BOBBIN THREAD TENSION ASM.":
        raise RuntimeError("Component 569 tidak sesuai. Dibatalkan.")

    for part_id, part_number, catalog_ref in targets:
        part = db.execute("""
            SELECT id, part_number, catalog_ref
            FROM parts
            WHERE id = ? AND machine_id = 44
        """, (part_id,)).fetchone()

        if not part or part[1] != part_number or part[2] != catalog_ref:
            raise RuntimeError(
                f"Data part tidak cocok: ID {part_id}. Dibatalkan."
            )

        existing = db.execute("""
            SELECT component_id
            FROM component_parts
            WHERE part_id = ?
        """, (part_id,)).fetchone()

        if existing:
            raise RuntimeError(
                f"Part {part_number} sudah terhubung ke component "
                f"{existing[0]}. Dibatalkan."
            )

    for part_id, _, _ in targets:
        db.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type)
            VALUES (?, ?, 'listed_in_component')
        """, (component_id, part_id))

    db.commit()

    print("\nBERHASIL")
    print("Relasi baru:", len(targets))

except Exception:
    db.rollback()
    raise

finally:
    db.close()

# Verifikasi hasil
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row

print("\n=== VERIFIKASI COMPONENT 569 ===")
for row in db.execute("""
    SELECT p.id, p.part_number, p.part_name,
           p.catalog_ref, p.quantity_raw, cp.relation_type
    FROM component_parts cp
    JOIN parts p ON p.id = cp.part_id
    WHERE cp.component_id = ?
    ORDER BY p.catalog_ref, p.id
""", (component_id,)):
    print(dict(row))

print("\nTotal relasi:", db.execute("""
    SELECT COUNT(*)
    FROM component_parts
    WHERE component_id = ?
""", (component_id,)).fetchone()[0])

db.close()
