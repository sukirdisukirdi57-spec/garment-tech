import csv
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
CSV_FILE = Path("tmp/bas311hn/c5_staging_review.csv")
SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/"
    "-/media/ap2/ism/pdf/parts-book-download/"
    "bas311hn_326h_pb.pdf?rev=-1"
)
MACHINE_ID = 227
DIAGRAM_PAGE = 13

if not DB.exists() or not CSV_FILE.exists():
    raise SystemExit("GAGAL: database atau CSV staging tidak ditemukan.")

with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 33:
    raise SystemExit(f"GAGAL: diharapkan 33 baris, ditemukan {len(rows)}.")

refs = [int(r["catalog_ref"]) for r in rows]
if len(set(refs)) != 33:
    raise SystemExit("GAGAL: catalog_ref tidak unik.")

for r in rows:
    if (
        not r["part_number"].strip()
        or not r["part_name"].strip()
        or int(r["diagram_page"]) != DIAGRAM_PAGE
    ):
        raise SystemExit(f"GAGAL: data tidak valid: {r}")

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

try:
    db.execute("BEGIN IMMEDIATE")

    machine = db.execute(
        "SELECT model FROM machines WHERE id = ?",
        (MACHINE_ID,)
    ).fetchone()
    if not machine or machine["model"] != "BAS-311HN-03S":
        raise RuntimeError("Identitas mesin ID 227 tidak sesuai.")

    pending = []
    already_present = 0

    for r in rows:
        ref = int(r["catalog_ref"])
        quantity_raw = r["quantity_raw"].strip()
        quantity = int(quantity_raw) if quantity_raw.isdigit() else None

        existing = db.execute("""
            SELECT id, part_number, part_name, quantity
            FROM parts
            WHERE machine_id = ?
              AND diagram_page = ?
              AND catalog_ref = ?
        """, (MACHINE_ID, DIAGRAM_PAGE, ref)).fetchall()

        if existing:
            if len(existing) != 1:
                raise RuntimeError(
                    f"Konflik: referensi katalog {ref} muncul lebih dari sekali."
                )
            e = existing[0]
            if (
                e["part_number"] != r["part_number"].strip()
                or e["part_name"] != r["part_name"].strip()
                or e["quantity"] != quantity
            ):
                raise RuntimeError(
                    f"Konflik data pada catalog_ref {ref}; impor dibatalkan."
                )
            already_present += 1
            continue

        pending.append({
            "catalog_ref": ref,
            "part_number": r["part_number"].strip(),
            "part_name": r["part_name"].strip(),
            "quantity": quantity,
            "quantity_raw": quantity_raw,
            "note": r.get("review_note", "").strip(),
        })

    # Pastikan semua konflik diperiksa sebelum membuat backup atau menulis.
    db.rollback()

    if pending:
        backup = DB.with_name(
            f"garment.db.before-c5-{datetime.now():%Y%m%d-%H%M%S}.bak"
        )
        source = sqlite3.connect(DB)
        destination = sqlite3.connect(backup)
        source.backup(destination)
        destination.close()
        source.close()
        print("Backup:", backup)

        db.execute("BEGIN IMMEDIATE")

        for p in pending:
            db.execute("""
                INSERT INTO parts (
                    machine_id, part_number, part_name, quantity,
                    catalog_ref, diagram_page, note, source_url,
                    notes, quantity_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                p["part_number"],
                p["part_name"],
                p["quantity"],
                p["catalog_ref"],
                DIAGRAM_PAGE,
                p["note"],
                SOURCE_URL,
                "C5 Feed mechanism; data katalog sementara. "
                "Kecocokan khusus submodel BAS-311HN-03S "
                "dan pemetaan kategori masih perlu diverifikasi.",
                p["quantity_raw"],
            ))

        db.commit()
    else:
        print("Semua referensi sudah ada dan cocok; tidak ada baris baru.")

    total = db.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id = ? AND diagram_page = ?
          AND catalog_ref IN (
              SELECT CAST(catalog_ref AS INTEGER)
              FROM (
                  SELECT catalog_ref FROM parts
                  WHERE machine_id = ? AND diagram_page = ?
              )
          )
    """, (MACHINE_ID, DIAGRAM_PAGE, MACHINE_ID, DIAGRAM_PAGE)).fetchone()[0]

    print("Model:", machine["model"])
    print("Baris staging:", len(rows))
    print("Sudah ada dan cocok:", already_present)
    print("Baris baru ditambahkan:", len(pending))
    print("Total part pada diagram halaman 13:", total)
    print("Relasi kategori 529 dibuat: tidak")
    print("Status: impor selesai; verifikasi submodel masih diperlukan.")

except Exception as exc:
    db.rollback()
    raise SystemExit(f"GAGAL — transaksi dibatalkan: {exc}")
finally:
    db.close()
