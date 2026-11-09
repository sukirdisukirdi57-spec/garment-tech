import argparse
import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database" / "garment.db"
CSV_FILE = ROOT / "audit_yamato_vm180_specs.csv"
ANOMALY = {"VM1804PR-382-003"}

def fmt_decimal(value):
    value = (value or "").strip()
    if not value or value.upper() == "N/A":
        return ""
    return value.replace(".", ",").replace(" - ", "–")

def fmt_speed(value):
    value = (value or "").strip()
    if not value:
        return ""
    # 4,500 dari sumber resmi berarti empat ribu lima ratus.
    return value.replace(",", ".") + " sti/min"

def make_specs(row):
    model = row["model"].strip()
    url = row["official_url"].strip()
    description = row.get("description", "").strip()
    needles = row["needles"].strip()
    threads = row["threads"].strip()
    remarks = row.get("remarks", "").strip()

    notes = f"Sumber resmi: {url}"
    specs = [
        ("Jenis mesin", "Double chain stitch machine"),
        ("Jumlah jarum", f"{needles} jarum"),
        ("Jumlah benang", f"{threads} benang"),
    ]

    distance = row["needle_distance_mm"].strip()
    if distance and distance.upper() != "N/A":
        specs.append(("Jarak antar jarum", f"{fmt_decimal(distance)} mm"))
    elif "NG" in model.upper():
        specs.append(("Gauge parts", "Tidak tersedia (NG)"))

    specs.extend([
        ("Panjang jahitan", f"{fmt_decimal(row['stitch_length_mm'])} mm"),
        ("Angkat sepatu penekan", f"{fmt_decimal(row['presser_foot_lift_mm'])} mm"),
        ("Langkah jarum", f"{fmt_decimal(row['needle_stroke_mm'])} mm"),
        ("Kecepatan maksimum", fmt_speed(row["machine_speed_sti_min"])),
    ])

    if remarks and remarks != "-":
        specs.append(("Konfigurasi tambahan", remarks))

    if any(not value.strip() for _, value in specs):
        raise ValueError(f"Nilai spesifikasi kosong untuk {model}")

    return [
        (name, value, notes, description or None)
        for name, value in specs
    ]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Terapkan impor ke database setelah validasi dan backup"
    )
    args = parser.parse_args()

    if not DB.is_file() or not CSV_FILE.is_file():
        raise SystemExit("Database atau CSV audit tidak ditemukan.")

    with CSV_FILE.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    plans = []
    skipped = []

    # Semua validasi awal dilakukan dengan koneksi read-only.
    ro = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    ro.row_factory = sqlite3.Row

    integrity = ro.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        ro.close()
        raise SystemExit(f"Integritas database gagal: {integrity}")

    for row in rows:
        model = row["model"].strip()
        machine_id = int(row["machine_id"])

        if model in ANOMALY or row.get("review_flag", "").strip().upper().startswith("ANOMALI SUMBER:"):
            skipped.append((model, "anomali sumber; ditahan untuk pemeriksaan manual"))
            continue

        if row.get("match_status", "").strip() != "COCOK PERSIS":
            raise SystemExit(f"Status audit tidak valid: {model}")

        machine = ro.execute("""
            SELECT m.id, m.model, b.name AS brand
            FROM machines m
            JOIN brands b ON b.id = m.brand_id
            WHERE m.id = ?
        """, (machine_id,)).fetchone()

        if (
            not machine
            or machine["model"].strip().upper() != model.upper()
            or "YAMATO" not in machine["brand"].upper()
        ):
            raise SystemExit(f"Validasi mesin gagal: ID {machine_id}, {model}")

        existing = ro.execute(
            "SELECT COUNT(*) FROM specifications WHERE machine_id = ?",
            (machine_id,)
        ).fetchone()[0]

        if existing:
            raise SystemExit(
                f"Impor dihentikan: {model} sudah memiliki "
                f"{existing} spesifikasi. Periksa manual dahulu."
            )

        plans.append({
            "machine_id": machine_id,
            "model": model,
            "specs": make_specs(row),
        })

    ro.close()

    if len(plans) != 19 or len(skipped) != 1:
        raise SystemExit(
            f"Jumlah tidak sesuai: siap={len(plans)}, ditahan={len(skipped)}. "
            "Database tidak diubah."
        )

    print("MODE:", "APPLY" if args.apply else "SIMULASI — READ-ONLY")
    print("Integrity awal:", integrity)
    total = 0
    for plan in plans:
        total += len(plan["specs"])
        print(
            f"[SIAP] ID {plan['machine_id']} | {plan['model']} "
            f"| {len(plan['specs'])} atribut"
        )

    print("\n===== DITAHAN =====")
    for model, reason in skipped:
        print(f"{model}: {reason}")

    print("\nModel siap:", len(plans))
    print("Jumlah atribut yang direncanakan:", total)

    if not args.apply:
        print("Database diubah: TIDAK")
        print("Untuk menerapkan setelah meninjau hasil, jalankan dengan --apply.")
        return

    # Cegah menimpa backup yang sudah ada.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.with_name(f"garment.db.backup-before-vm180-{stamp}")
    if backup.exists():
        raise SystemExit(f"Backup sudah ada; dibatalkan: {backup}")

    # Validasi dan backup dilakukan sebelum transaksi penulisan.
    shutil.copy2(DB, backup)
    print("\nBackup:", backup)

    con = sqlite3.connect(DB)
    try:
        con.execute("BEGIN IMMEDIATE")

        # Ulangi pemeriksaan tepat sebelum menulis.
        for plan in plans:
            current = con.execute("""
                SELECT m.model, b.name
                FROM machines m
                JOIN brands b ON b.id = m.brand_id
                WHERE m.id = ?
            """, (plan["machine_id"],)).fetchone()

            if (
                not current
                or current[0].strip().upper() != plan["model"].upper()
                or "YAMATO" not in current[1].upper()
            ):
                raise RuntimeError(f"Validasi ulang gagal: {plan['model']}")

            count = con.execute(
                "SELECT COUNT(*) FROM specifications WHERE machine_id = ?",
                (plan["machine_id"],)
            ).fetchone()[0]
            if count:
                raise RuntimeError(
                    f"Spesifikasi muncul sebelum impor: {plan['model']}"
                )

        for plan in plans:
            for name, value, notes, description in plan["specs"]:
                con.execute("""
                    INSERT INTO specifications
                    (machine_id, specification, value, notes, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    plan["machine_id"], name, value, notes, description
                ))

        check = con.execute("PRAGMA integrity_check").fetchone()[0]
        if check != "ok":
            raise RuntimeError(f"Integritas setelah impor gagal: {check}")

        for plan in plans:
            count = con.execute(
                "SELECT COUNT(*) FROM specifications WHERE machine_id = ?",
                (plan["machine_id"],)
            ).fetchone()[0]
            if count != len(plan["specs"]):
                raise RuntimeError(
                    f"Jumlah hasil tidak sesuai untuk {plan['model']}: {count}"
                )

        con.commit()
        print("Integritas setelah impor:", check)
        print("Model berhasil diimpor:", len(plans))
        print("Atribut berhasil ditambahkan:", total)
        print("Database diubah: YA")
        print("Backup tersimpan:", backup)

    except Exception:
        con.rollback()
        print("TRANSAKSI DIBATALKAN — perubahan di-rollback.")
        print("Backup tetap tersedia:", backup)
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
