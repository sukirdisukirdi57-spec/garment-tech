import sqlite3
from pathlib import Path
from collections import Counter

db = Path("database/garment.db").resolve()
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

ACTION = (
    "periksa", "bersihkan", "sesuaikan", "lakukan",
    "ganti", "pasang", "atur", "setel", "lepaskan",
    "gunakan", "pastikan", "hindari"
)
SAFETY = (
    "matikan mesin", "mesin berhenti", "lepaskan sumber tenaga",
    "cabut listrik", "putuskan sumber listrik",
    "jangan menyentuh", "sebelum melakukan pemeriksaan",
    "sebelum memeriksa", "sebelum membersihkan"
)
SYMPTOM = (
    "terjadi", "terbentuk", "berulang", "berubah",
    "tidak stabil", "tidak konsisten", "berkerut",
    "tert tarik", "tidak terumpan", "putusnya",
    "permukaan kain", "kerapatan dan bentuk"
)

def has_any(value, words):
    value = (value or "").lower()
    return any(word in value for word in words)

try:
    rows = con.execute("""
        SELECT t.id, m.model, t.problem, t.symptoms,
               t.possible_cause, t.solution, t.safety_notes, t.source
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        JOIN brands b ON b.id = m.brand_id
        WHERE UPPER(b.name) = 'PEGASUS'
        ORDER BY m.model, t.id
    """).fetchall()

    print("AUDIT STRUKTUR TROUBLESHOOTING PEGASUS")
    print("MODE: READ-ONLY")
    print(f"Total catatan: {len(rows)}")
    print("=" * 88)

    flagged = []
    model_counts = Counter()

    for r in rows:
        reasons = []
        symptoms = r["symptoms"] or ""
        cause = r["possible_cause"] or ""
        solution = r["solution"] or ""
        safety = r["safety_notes"] or ""

        if not symptoms.strip():
            reasons.append("GEJALA KOSONG")
        if not cause.strip():
            reasons.append("PENYEBAB KOSONG")
        if not solution.strip():
            reasons.append("SOLUSI KOSONG")
        if not safety.strip():
            reasons.append("KEAMANAN KOSONG")

        # Gejala yang berisi kata tindakan bisa perlu ditinjau,
        # tetapi bukan bukti kesalahan dengan sendirinya.
        if has_any(symptoms, ACTION):
            reasons.append("GEJALA MENGANDUNG KATA TINDAKAN")

        if has_any(cause, ("periksa", "bersihkan", "lakukan", "ganti", "pasang")):
            reasons.append("PENYEBAB MENGANDUNG INSTRUKSI")

        if has_any(solution, SAFETY):
            reasons.append("SOLUSI MENGANDUNG INSTRUKSI KESELAMATAN")

        # Safety note yang sama dengan solusi patut diperiksa.
        if solution.strip() and safety.strip() and (
            solution.strip().casefold() == safety.strip().casefold()
        ):
            reasons.append("SOLUSI SAMA PERSIS DENGAN CATATAN KEAMANAN")

        if reasons:
            flagged.append((r, reasons))
            model_counts[r["model"]] += 1

    print(f"Catatan bertanda untuk ditinjau: {len(flagged)}")
    print(f"Model yang memiliki tanda: {len(model_counts)}")

    for model, count in sorted(model_counts.items()):
        print(f"  {model}: {count} catatan")

    print("\nDETAIL CATATAN YANG DITANDAI")
    print("=" * 88)

    for r, reasons in flagged:
        print(f"\nID={r['id']} | MODEL={r['model']} | MASALAH={r['problem']}")
        print("TANDA:", "; ".join(reasons))
        print("GEJALA :", r["symptoms"])
        print("PENYEBAB:", r["possible_cause"])
        print("SOLUSI :", r["solution"])
        print("KEAMANAN:", r["safety_notes"])

    print("\n" + "=" * 88)
    print("INTEGRITY CHECK:",
          con.execute("PRAGMA integrity_check").fetchone()[0])
    print("Database tidak diubah.")
    print("CATATAN: tanda otomatis adalah indikasi, bukan vonis kesalahan.")

finally:
    con.close()
