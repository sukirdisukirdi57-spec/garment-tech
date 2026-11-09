import sqlite3
from pathlib import Path

DB = Path("database/garment.db").resolve()
TARGET_MODELS = {"E256", "EX5400", "TML326"}
FIELDS = ("symptoms", "possible_cause", "solution", "safety_notes")

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"Integritas database bermasalah: {integrity}")

    rows = con.execute("""
        SELECT m.model, t.id, t.machine_id, t.problem,
               t.symptoms, t.possible_cause, t.solution, t.safety_notes
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        JOIN brands b ON b.id = m.brand_id
        WHERE UPPER(b.name) = 'PEGASUS'
        ORDER BY m.model, t.id
    """).fetchall()

    # Template pembanding: catatan E22L yang telah diaudit bersih.
    templates = {}
    for r in rows:
        if r["model"] == "E22L":
            if r["problem"] in templates:
                raise RuntimeError(
                    f"Problem E22L ganda: {r['problem']}"
                )
            templates[r["problem"]] = r

    targets = [
        r for r in rows if r["model"] in TARGET_MODELS
    ]

    if len(targets) != 15:
        raise RuntimeError(
            f"Target seharusnya 15 catatan, ditemukan {len(targets)}. "
            "Simulasi dihentikan."
        )

    print("=" * 78)
    print("SIMULASI PERBAIKAN TROUBLESHOOTING PEGASUS")
    print("MODE: READ-ONLY — DATABASE TIDAK DIUBAH")
    print(f"Integrity check: {integrity}")
    print(f"Jumlah target: {len(targets)}")
    print("=" * 78)

    for r in targets:
        template = templates.get(r["problem"])
        if template is None:
            print(
                f"\nLEWATI ID {r['id']} ({r['model']}): "
                f"template E22L untuk '{r['problem']}' tidak ditemukan."
            )
            continue

        # Usulan tiga kolom mengikuti pola E22L untuk problem yang sama.
        proposed = {
            "symptoms": template["symptoms"],
            "possible_cause": template["possible_cause"],
            "solution": template["solution"],
        }

        # Pertahankan seluruh instruksi keselamatan lama yang relevan.
        safety_parts = []
        for value in (
            template["safety_notes"],
            r["solution"],
            r["safety_notes"],
        ):
            value = (value or "").strip()
            if value and value not in safety_parts:
                safety_parts.append(value)

        proposed["safety_notes"] = " ".join(safety_parts)

        print(f"\n{'-' * 78}")
        print(f"MODEL: {r['model']} | ID: {r['id']}")
        print(f"MASALAH: {r['problem']}")

        for field in FIELDS:
            old = (r[field] or "").strip()
            new = proposed[field]
            print(f"\n[{field}]")
            print(f"LAMA : {old}")
            print(f"USUL : {new}")
            print(f"STATUS: {'TIDAK BERUBAH' if old == new else 'PERLU TINJAUAN'}")

    print("\n" + "=" * 78)
    print("SIMULASI SELESAI")
    print("Tidak ada perubahan database yang dilakukan.")
    print("Periksa usulan sebelum menyetujui penerapan.")
    print("Integrity check:", con.execute("PRAGMA integrity_check").fetchone()[0])

finally:
    con.close()
