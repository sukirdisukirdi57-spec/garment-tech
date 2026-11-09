import sqlite3
from pathlib import Path
from collections import defaultdict

DB = Path("database/garment.db").resolve()
URI = f"file:{DB}?mode=ro"

MODELS = (
    "W3522P", "W542P", "W562P", "W562PC",
    "W664P", "W674", "WT264P"
)

FIELDS = (
    "symptoms", "possible_cause", "solution", "safety_notes"
)

con = sqlite3.connect(URI, uri=True)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    print("AUDIT ISI TROUBLESHOOTING PEGASUS W-SERIES")
    print("MODE: READ ONLY")
    print("Database:", DB)
    print("Integritas awal:", integrity)

    if integrity.lower() != "ok":
        raise RuntimeError("Integritas SQLite tidak ok.")

    rows = con.execute("""
        SELECT t.id, m.model, t.problem,
               t.symptoms, t.possible_cause,
               t.solution, t.safety_notes, t.source
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        JOIN brands b ON b.id = m.brand_id
        WHERE UPPER(b.name) = 'PEGASUS'
          AND m.model IN (?, ?, ?, ?, ?, ?, ?)
        ORDER BY m.model, t.id
    """, MODELS).fetchall()

    print("Record W-series ditemukan:", len(rows))

    # Kumpulkan pola teks seluruh PEGASUS untuk perbandingan.
    all_rows = con.execute("""
        SELECT m.model, t.problem,
               t.symptoms, t.possible_cause,
               t.solution, t.safety_notes
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        JOIN brands b ON b.id = m.brand_id
        WHERE UPPER(b.name) = 'PEGASUS'
    """).fetchall()

    patterns = defaultdict(list)
    for r in all_rows:
        key = (
            r["problem"],
            *(r[f] or "" for f in FIELDS)
        )
        patterns[key].append(r["model"])

    for model in MODELS:
        subset = [r for r in rows if r["model"] == model]
        print(f"\n{'=' * 72}\nMODEL {model}: {len(subset)} record")

        for r in subset:
            key = (
                r["problem"],
                *(r[f] or "" for f in FIELDS)
            )
            matching_models = sorted(set(patterns[key]) - {model})

            print(f"\nID {r['id']} | {r['problem']}")
            print("GEJALA :", r["symptoms"])
            print("PENYEBAB:", r["possible_cause"])
            print("SOLUSI :", r["solution"])
            print("KEAMANAN:", r["safety_notes"])
            print("SUMBER :", r["source"])
            print(
                "POLA IDENTIK DI MODEL LAIN:",
                ", ".join(matching_models) if matching_models
                else "Tidak ditemukan"
            )

    print("\n" + "=" * 72)
    print("Integritas akhir:",
          con.execute("PRAGMA integrity_check").fetchone()[0])
    print("Database tidak diubah.")

finally:
    con.close()
