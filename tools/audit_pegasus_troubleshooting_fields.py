import sqlite3
from pathlib import Path

DB = Path("database/garment.db").resolve()
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

rows = cur.execute("""
SELECT t.id, m.model, t.problem, t.symptoms,
       t.possible_cause, t.solution, t.safety_notes, t.source
FROM troubleshooting t
JOIN machines m ON m.id=t.machine_id
JOIN brands b ON b.id=m.brand_id
WHERE UPPER(b.name)='PEGASUS'
ORDER BY m.model, t.id
""").fetchall()

print("Total record:", len(rows))

def has_any(value, words):
    value = (value or "").lower()
    return any(w in value for w in words)

safety_words = (
    "matikan mesin", "mesin berhenti", "cabut listrik",
    "putuskan sumber listrik", "sebelum memeriksa"
)
action_words = (
    "periksa", "bersihkan", "sesuaikan", "lakukan",
    "ganti ", "pastikan", "setel", "atur "
)
symptom_words = (
    "terjadi", "terlihat", "muncul", "tidak terbentuk",
    "berulang", "berubah", "tidak stabil", "putusnya",
    "mengalami", "berkerut"
)

flags = []
for r in rows:
    symptoms = r["symptoms"] or ""
    cause = r["possible_cause"] or ""
    solution = r["solution"] or ""
    safety = r["safety_notes"] or ""

    reasons = []
    if has_any(symptoms, action_words):
        reasons.append("symptoms berisi kata tindakan")
    if has_any(cause, ("periksa ", "bersihkan ", "lakukan ", "ganti ")):
        reasons.append("possible_cause berisi instruksi tindakan")
    if has_any(solution, safety_words):
        reasons.append("solution tampak berisi instruksi keselamatan")
    if not (r["source"] or "").strip():
        reasons.append("source kosong")
    if not symptoms.strip() or not cause.strip() or not solution.strip():
        reasons.append("ada kolom utama kosong")

    # Ini hanya penyaringan awal, bukan penetapan otomatis bahwa data salah.
    if reasons:
        flags.append((r, reasons))

print("Record yang perlu ditinjau:", len(flags))
for r, reasons in flags:
    print("\\n" + "=" * 64)
    print(f"ID={r['id']} | model={r['model']}")
    print("Indikasi:", "; ".join(reasons))
    for field in (
        "problem", "symptoms", "possible_cause",
        "solution", "safety_notes", "source"
    ):
        print(f"{field}: {r[field] or ''}")

print("\\nRingkasan sumber:")
sources = cur.execute("""
SELECT COALESCE(NULLIF(TRIM(t.source), ''), '[KOSONG]') AS src,
       COUNT(*) AS jumlah
FROM troubleshooting t
JOIN machines m ON m.id=t.machine_id
JOIN brands b ON b.id=m.brand_id
WHERE UPPER(b.name)='PEGASUS'
GROUP BY src
ORDER BY jumlah DESC
""").fetchall()
for r in sources:
    print(f"{r['jumlah']:>3} | {r['src']}")

print("\\nIntegritas:", cur.execute("PRAGMA integrity_check").fetchone()[0])
con.close()
print("SELESAI — DATABASE TIDAK DIUBAH")
