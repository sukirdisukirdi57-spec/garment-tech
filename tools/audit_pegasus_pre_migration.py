import sqlite3
from pathlib import Path

DB = Path("database/garment.db").resolve()
REPORT = Path("audit_pegasus_pre_migration.txt")
MODELS = ("E256", "EX5400", "TML326")
PROBLEMS = (
    "Benang sering putus",
    "Jahitan loncat",
    "Jahitan tidak rapi atau tidak stabil",
    "Kain mengerut",
    "Kain tidak terumpan dengan stabil",
)

SYMPTOMS = {
    "Benang sering putus":
        "Putusnya benang terjadi berulang saat mesin dijalankan.",
    "Jahitan loncat":
        "Sebagian jahitan tidak terbentuk dengan sempurna.",
    "Jahitan tidak rapi atau tidak stabil":
        "Kerapatan dan bentuk jahitan berubah-ubah selama proses menjahit.",
    "Kain mengerut":
        "Permukaan kain berkerut atau tertarik setelah proses menjahit.",
    "Kain tidak terumpan dengan stabil":
        "Kain bergerak tidak stabil atau laju pengumpanan tidak konsisten.",
}

def line(out, value=""):
    out.append(str(value))

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
out = []
errors = []
warnings = []

try:
    line(out, f"Database: {DB}")
    line(out, "Mode: AUDIT PRA-MIGRASI — READ ONLY")
    line(out, f"Integritas awal: {con.execute('PRAGMA integrity_check').fetchone()[0]}")

    columns = {
        r["name"] for r in con.execute("PRAGMA table_info(troubleshooting)")
    }
    required = {
        "id", "machine_id", "problem", "symptoms",
        "possible_cause", "solution", "safety_notes", "source"
    }

    if not required.issubset(columns):
        errors.append("Kolom wajib tidak lengkap: " +
                      ", ".join(sorted(required - columns)))

    machines = con.execute(
        "SELECT id, model FROM machines WHERE model IN (?, ?, ?)",
        MODELS,
    ).fetchall()
    machine_ids = {r["model"]: r["id"] for r in machines}

    if set(machine_ids) != set(MODELS):
        errors.append(f"Model target tidak lengkap: {machine_ids}")

    total = 0
    for model in MODELS:
        if model not in machine_ids:
            continue

        rows = con.execute(
            """
            SELECT id, problem, symptoms, possible_cause,
                   solution, safety_notes, source
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
            """,
            (machine_ids[model],),
        ).fetchall()

        selected = [r for r in rows if r["problem"] in PROBLEMS]
        line(out)
        line(out, f"=== {model}: {len(selected)} baris target ===")

        if len(selected) != 5:
            errors.append(f"{model}: jumlah target bukan 5")

        for r in selected:
            total += 1
            line(out)
            line(out, f"ID {r['id']} | {r['problem']}")

            for field in (
                "symptoms", "possible_cause", "solution",
                "safety_notes", "source"
            ):
                value = r[field]
                line(out, f"LAMA {field}: {value!r}")
                if value is None or not str(value).strip():
                    warnings.append(f"ID {r['id']}: {field} kosong")

            # Usulan konservatif: hanya gejala diganti ke kalimat gejala.
            # Penyebab dan solusi lama dipertahankan agar informasi tidak hilang.
            proposed = {
                "symptoms": SYMPTOMS[r["problem"]],
                "possible_cause": r["symptoms"],
                "solution": r["possible_cause"],
                "safety_notes": r["safety_notes"],
                "source": r["source"],
            }

            line(out, "-- USULAN --")
            for field, value in proposed.items():
                line(out, f"BARU {field}: {value!r}")

            # Tampilkan instruksi lama yang tidak otomatis dipertahankan
            # pada pemetaan konservatif, agar ditinjau manual.
            old_solution = (r["solution"] or "").strip()
            old_safety = (r["safety_notes"] or "").strip()
            if old_solution and old_solution != old_safety:
                line(out, "TINJAUAN: solution lama berbeda dari safety_notes;")
                line(out, "          instruksi tersebut perlu ditinjau sebelum migrasi.")
                warnings.append(
                    f"ID {r['id']}: instruksi solution lama perlu ditinjau"
                )

    if total != 15:
        errors.append(f"Total target {total}, seharusnya 15")

    line(out)
    line(out, "=" * 70)
    line(out, f"TOTAL BARIS: {total}")
    line(out, f"JUMLAH ERROR: {len(errors)}")
    line(out, f"JUMLAH PERINGATAN: {len(warnings)}")
    for item in errors:
        line(out, "ERROR: " + item)
    for item in warnings:
        line(out, "PERINGATAN: " + item)

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    line(out, f"Integritas akhir: {integrity}")
    line(out, "Database tidak diubah.")

finally:
    con.close()

REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[:12]))
print(f"\nLaporan lengkap: {REPORT.resolve()}")
print("Database tetap tidak diubah.")
