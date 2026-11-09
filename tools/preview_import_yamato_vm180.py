import csv
import sqlite3
from pathlib import Path

DB = Path("database/garment.db").resolve()
CSV_FILE = Path("audit_yamato_vm180_specs.csv")
SKIP_MODELS = {"VM1804PR-382-003"}

if not CSV_FILE.is_file():
    raise SystemExit(f"CSV tidak ditemukan: {CSV_FILE}")

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

print("MODE: SIMULASI — DATABASE READ-ONLY")
print("Integrity:", con.execute("PRAGMA integrity_check").fetchone()[0])

with CSV_FILE.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

planned = 0
skipped_anomaly = 0
skipped_existing = 0
skipped_invalid = 0

for row in rows:
    model = row["model"].strip()
    machine_id = int(row["machine_id"])

    machine = con.execute("""
        SELECT m.id, m.model, b.name AS brand
        FROM machines m
        JOIN brands b ON b.id = m.brand_id
        WHERE m.id = ?
    """, (machine_id,)).fetchone()

    if not machine or machine["model"].strip().upper() != model.upper():
        print(f"[LEWATI] ID/model tidak cocok: {machine_id} / {model}")
        skipped_invalid += 1
        continue

    if "YAMATO" not in machine["brand"].upper():
        print(f"[LEWATI] Merek bukan YAMATO: {model}")
        skipped_invalid += 1
        continue

    if row.get("match_status") != "COCOK PERSIS":
        print(f"[LEWATI] Model belum cocok: {model}")
        skipped_invalid += 1
        continue

    if model in SKIP_MODELS or row.get("review_flag", "").strip().upper().startswith("ANOMALI SUMBER:"):
        print(f"[TINJAU MANUAL] {model}")
        skipped_anomaly += 1
        continue

    existing = con.execute("""
        SELECT COUNT(*)
        FROM specifications
        WHERE machine_id = ?
    """, (machine_id,)).fetchone()[0]

    if existing:
        print(f"[LEWATI] {model}: sudah memiliki {existing} spesifikasi")
        skipped_existing += 1
        continue

    required = [
        "needles", "threads", "stitch_length_mm",
        "presser_foot_lift_mm", "needle_stroke_mm",
        "machine_speed_sti_min"
    ]
    missing = [k for k in required if not row.get(k, "").strip()]
    if missing:
        print(f"[LEWATI] {model}: data kosong {', '.join(missing)}")
        skipped_invalid += 1
        continue

    planned += 1
    print(f"[SIAP SIMULASI] ID {machine_id} | {model}")

print("\n===== RINGKASAN SIMULASI =====")
print("Baris CSV             :", len(rows))
print("Siap direncanakan     :", planned)
print("Anomali/manual        :", skipped_anomaly)
print("Sudah punya spesifikasi:", skipped_existing)
print("Tidak valid/kosong    :", skipped_invalid)
print("Database diubah       : TIDAK")

con.close()
