import csv
import sqlite3
import re
import sys
from pathlib import Path
from urllib.parse import quote

DB = Path("database/garment.db")
OUT = Path("tools/pegasus_priority_field_diff.csv")

MODELS = ["E22L", "E256", "EX5400", "TML326"]
FIELDS = [
    "symptoms", "possible_cause", "solution",
    "safety_notes", "source"
]

def norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

if not DB.exists():
    sys.exit(f"ERROR: Database tidak ditemukan: {DB}")

uri = "file:" + quote(str(DB.resolve())) + "?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row

try:
    tables = [
        r["name"] for r in con.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]

    schemas = {}
    for table in tables:
        schemas[table] = [
            r["name"] for r in con.execute(
                f'PRAGMA table_info("{table}")'
            )
        ]

    required = set(FIELDS) | {"id", "machine_id"}
    trouble_candidates = [
        t for t, cols in schemas.items()
        if required.issubset(set(cols))
    ]

    machine_candidates = [
        t for t, cols in schemas.items()
        if {"id", "model"}.issubset(set(cols))
    ]

    if len(trouble_candidates) != 1 or len(machine_candidates) != 1:
        print("ERROR: Struktur tabel belum dapat ditentukan otomatis.")
        print("Kandidat troubleshooting:", trouble_candidates)
        print("Kandidat mesin:", machine_candidates)
        print("Tabel dan kolom yang ditemukan:")
        for t, cols in schemas.items():
            print(f"- {t}: {', '.join(cols)}")
        sys.exit(2)

    tt = trouble_candidates[0]
    mt = machine_candidates[0]

    # Semua nama tabel/kolom diambil dari skema database lokal.
    sql = f'''
        SELECT t.id AS record_id, m.model AS model,
               t.symptoms, t.possible_cause, t.solution,
               t.safety_notes, t.source
        FROM "{tt}" t
        JOIN "{mt}" m ON m.id = t.machine_id
        WHERE UPPER(m.model) IN (?, ?, ?, ?)
        ORDER BY UPPER(m.model), t.id
    '''
    records = con.execute(sql, MODELS).fetchall()

    by_model = {m: [] for m in MODELS}
    for r in records:
        model = str(r["model"]).upper()
        if model in by_model:
            by_model[model].append(dict(r))

    baseline = {}
    for r in by_model["E22L"]:
        baseline.setdefault(norm(r["symptoms"]), []).append(r)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "model", "record_id", "problem",
        "baseline_model", "baseline_record_id",
        "field", "target_value", "baseline_value",
        "status", "review_note"
    ]

    count = 0
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for model in ["E256", "EX5400", "TML326"]:
            for target in by_model[model]:
                matches = baseline.get(norm(target["symptoms"]), [])
                base = matches[0] if len(matches) == 1 else None

                for field in FIELDS:
                    old = target.get(field) or ""
                    ref = (base.get(field) or "") if base else ""
                    same = norm(old) == norm(ref) if base else False

                    notes = []
                    if not base:
                        notes.append(
                            "Pembanding E22L tidak unik/tidak ditemukan; "
                            "jangan otomatis menyalin."
                        )
                    elif field == "solution":
                        if "penyetelan secara bertahap" in norm(old) and \
                           "penyetelan secara bertahap" not in norm(ref):
                            notes.append(
                                "Target memiliki langkah penyetelan bertahap "
                                "yang tidak ada pada pembanding."
                            )
                    elif field == "possible_cause":
                        if "jarum bengkok" in norm(old) and \
                           "jarum bengkok" not in norm(ref):
                            notes.append(
                                "Target menyebut jarum bengkok; "
                                "validasi teknis sebelum revisi."
                            )
                    elif field == "safety_notes" and not same:
                        notes.append(
                            "Perbedaan keselamatan; validasi dengan manual "
                            "model terkait."
                        )
                    elif field == "source" and not same:
                        notes.append(
                            "Validasi sumber resmi dan kecocokan model."
                        )

                    writer.writerow({
                        "model": model,
                        "record_id": target["record_id"],
                        "problem": target["symptoms"],
                        "baseline_model": "E22L" if base else "",
                        "baseline_record_id": base["record_id"] if base else "",
                        "field": field,
                        "target_value": old,
                        "baseline_value": ref,
                        "status": (
                            "SAMA" if same else
                            "BERBEDA" if base else "PERLU PEMBANDING"
                        ),
                        "review_note": " ".join(notes)
                    })
                    count += 1

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    print("=== LAPORAN PERBANDINGAN PEGASUS ===")
    print(f"Tabel troubleshooting : {tt}")
    print(f"Tabel mesin           : {mt}")
    print(f"Record ditemukan      : {len(records)}")
    print(f"Baris perbandingan    : {count}")
    print(f"CSV                   : {OUT}")
    print(f"Integritas database   : {integrity}")
    print("Mode database         : READ ONLY")
    print("Perubahan database    : TIDAK ADA")

    if integrity != "ok":
        sys.exit("PERINGATAN: pemeriksaan integritas tidak OK.")
finally:
    con.close()
