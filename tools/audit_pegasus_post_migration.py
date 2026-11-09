import sqlite3
from pathlib import Path
from collections import Counter

DB = Path("database/garment.db").resolve()
URI = f"file:{DB}?mode=ro"

TARGET_MODELS = ("E256", "EX5400", "TML326")
EXPECTED_PROBLEMS = {
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

con = sqlite3.connect(URI, uri=True)
con.row_factory = sqlite3.Row

errors = []
warnings = []

try:
    print("=" * 72)
    print("AUDIT PEGASUS PASCAMIGRASI — READ ONLY")
    print("Database:", DB)

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    print("Integritas awal:", integrity)
    if integrity.lower() != "ok":
        errors.append("Integritas SQLite bukan ok.")

    total = con.execute("""
        SELECT COUNT(*)
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        JOIN brands b ON b.id = m.brand_id
        WHERE UPPER(b.name) = 'PEGASUS'
    """).fetchone()[0]
    print("Total record troubleshooting PEGASUS:", total)
    if total != 180:
        warnings.append(
            f"Total troubleshooting PEGASUS bukan 180: {total}"
        )

    columns = {
        r["name"]
        for r in con.execute("PRAGMA table_info(troubleshooting)")
    }
    required = {
        "id", "machine_id", "problem", "symptoms",
        "possible_cause", "solution", "safety_notes", "source"
    }
    missing = required - columns
    if missing:
        raise RuntimeError(
            "Kolom yang dibutuhkan tidak ditemukan: "
            + ", ".join(sorted(missing))
        )

    machine_columns = {
        r["name"] for r in con.execute("PRAGMA table_info(machines)")
    }
    model_col = next(
        (c for c in ("model", "model_name", "name")
         if c in machine_columns),
        None
    )
    if not model_col:
        raise RuntimeError(
            "Kolom model pada tabel machines tidak dikenali. "
            "Database tidak diubah."
        )

    sql = f"""
        SELECT t.id, t.machine_id, m."{model_col}" AS model,
               t.problem, t.symptoms, t.possible_cause,
               t.solution, t.safety_notes, t.source
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        WHERE m."{model_col}" IN (?, ?, ?)
        ORDER BY m."{model_col}", t.id
    """
    rows = con.execute(sql, TARGET_MODELS).fetchall()

    print("\n=== PEMERIKSAAN 15 RECORD TARGET ===")
    print("Record ditemukan:", len(rows))
    if len(rows) != 15:
        errors.append(f"Target seharusnya 15 record, ditemukan {len(rows)}.")

    counts = Counter(r["model"] for r in rows)
    for model in TARGET_MODELS:
        print(f"  {model}: {counts[model]} record")
        if counts[model] != 5:
            errors.append(f"{model}: jumlah record bukan 5.")

    seen = set()
    for r in rows:
        rid = r["id"]
        model = r["model"]
        problem = r["problem"]

        if problem in seen and False:
            pass
        seen.add((model, problem))

        expected_symptom = EXPECTED_PROBLEMS.get(problem)
        if expected_symptom is None:
            errors.append(f"ID {rid}: masalah tidak dikenal: {problem!r}")
        elif r["symptoms"] != expected_symptom:
            errors.append(
                f"ID {rid} ({model}): gejala tidak sesuai pola "
                f"untuk {problem!r}."
            )

        for field in (
            "symptoms", "possible_cause", "solution",
            "safety_notes", "source"
        ):
            value = r[field]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"ID {rid}: kolom {field} kosong.")

        if r["solution"] == r["safety_notes"]:
            warnings.append(
                f"ID {rid} ({model}): solusi identik dengan catatan keamanan."
            )

        if not r["source"] or not r["source"].strip():
            errors.append(f"ID {rid}: sumber tidak tersedia.")

        print(
            f"ID {rid} | {model} | {problem} | "
            f"gejala={'OK' if r['symptoms'] == expected_symptom else 'PERIKSA'}"
        )

    for model in TARGET_MODELS:
        model_rows = [r for r in rows if r["model"] == model]
        problems = Counter(r["problem"] for r in model_rows)
        for problem in EXPECTED_PROBLEMS:
            if problems[problem] != 1:
                errors.append(
                    f"{model}: masalah {problem!r} muncul "
                    f"{problems[problem]} kali, seharusnya 1."
                )

    print("\n=== RINGKASAN ===")
    print("Kesalahan:", len(errors))
    print("Peringatan:", len(warnings))

    for item in errors:
        print("ERROR:", item)
    for item in warnings:
        print("PERINGATAN:", item)

    final_integrity = con.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]
    print("\nIntegritas akhir:", final_integrity)
    if final_integrity.lower() != "ok":
        errors.append("Integritas akhir bukan ok.")

    if errors:
        print("HASIL: PERLU DITINJAU")
    elif warnings:
        print("HASIL: LOLOS PEMERIKSAAN DASAR, ADA PERINGATAN")
    else:
        print("HASIL: LOLOS PEMERIKSAAN DASAR")

    print("MODE: READ ONLY — DATABASE TIDAK DIUBAH")

finally:
    con.close()
