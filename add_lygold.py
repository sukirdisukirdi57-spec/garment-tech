import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db = Path("database/garment.db")

if not db.exists():
    raise SystemExit(f"Database tidak ditemukan: {db}")

backup = db.with_name(
    f"garment_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
)
shutil.copy2(db, backup)
print(f"Backup dibuat: {backup}")

conn = sqlite3.connect(db)
conn.execute("PRAGMA foreign_keys = ON")

try:
    conn.execute("BEGIN IMMEDIATE")

    existing = conn.execute(
        "SELECT id FROM machines WHERE UPPER(TRIM(model)) = ?",
        ("LGA105E-BUT",)
    ).fetchone()

    if existing:
        raise RuntimeError(
            f"Model LGA105E-BUT sudah ada, machine ID: {existing[0]}"
        )

    brand = conn.execute(
        "SELECT id FROM brands WHERE UPPER(TRIM(name)) = 'LYGOLD'"
    ).fetchone()

    if brand:
        brand_id = brand[0]
    else:
        cur = conn.execute(
            """INSERT INTO brands (name, country, notes)
               VALUES (?, ?, ?)""",
            ("LYGOLD", None, "Asal negara merek belum diverifikasi.")
        )
        brand_id = cur.lastrowid

    machine_type = conn.execute(
        "SELECT id FROM machine_types WHERE id = ? AND name = ?",
        (16, "Automatic Machine")
    ).fetchone()

    if not machine_type:
        raise RuntimeError(
            "Machine type ID 16 bukan Automatic Machine. "
            "Periksa tabel machine_types terlebih dahulu."
        )

    cur = conn.execute(
        """INSERT INTO machines
           (brand_id, machine_type_id, model, function, description, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            brand_id,
            16,
            "LGA105E-BUT",
            "Automatic Elastic Joining Machine",
            "Mesin otomatis untuk menyambung karet elastis.",
            "Nomor seri: 81210313001. Data berdasarkan label mesin; "
            "perlu verifikasi dengan dokumentasi teknis."
        )
    )
    machine_id = cur.lastrowid

    specs = [
        ("Tegangan AC", "220 V, 50 Hz"),
        ("Total daya", "1600 W"),
        ("Daya pembentuk", "850 W"),
        ("Tegangan DC", "24 V"),
        ("Suhu pemanasan", "90°C–170°C"),
        ("Nomor seri", "81210313001"),
    ]

    for name, value in specs:
        conn.execute(
            """INSERT INTO specifications
               (machine_id, specification, value, notes, description)
               VALUES (?, ?, ?, ?, ?)""",
            (
                machine_id,
                name,
                value,
                "Transkripsi label mesin; perlu verifikasi.",
                "Sumber: label LYGOLD LGA105E-BUT."
            )
        )

    conn.commit()

    print("\nBERHASIL!")
    print("Brand ID:", brand_id)
    print("Machine ID:", machine_id)
    print("Model: LGA105E-BUT")
    print("Jumlah spesifikasi:", len(specs))
    print("Backup:", backup)

except Exception as exc:
    conn.rollback()
    print("\nGAGAL:", exc)
    print("Perubahan database dibatalkan.")
finally:
    conn.close()
