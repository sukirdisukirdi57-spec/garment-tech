import sqlite3
from pathlib import Path
from datetime import date

DB = Path("database/garment.db")
OUT = Path("audit-kelengkapan/matriks_revisi_teknis_ddl9000cs.md")

expected = [
    "E000", "E007", "E009", "E011", "E012", "E013", "E014",
    "E015", "E016", "E032", "E071", "E072", "E081", "E204",
    "E220", "E221", "E302", "E303", "E704", "E730", "E731",
    "E733", "E811", "E813", "E815", "E903", "E904", "E910",
    "E912", "E915", "E922", "E924", "E946", "E955", "E961",
    "E962", "E971", "E972", "E973", "E974", "E975", "E976",
    "E985"
]

no_check_item = {
    "E072", "E904", "E922", "E924", "E971", "E973", "E975"
}

def audit_note(code):
    notes = {
        "E000": (
            "Manual menyatakan 'not an error'.",
            "Tinjau redaksi agar jelas bahwa kode ini bukan indikasi kerusakan.",
            "Jangan menyimpulkan ada komponen rusak hanya dari kode ini."
        ),
    }

    if code in no_check_item:
        return (
            "Daftar manual yang ditinjau tidak mencantumkan butir pemeriksaan.",
            "Jangan menambahkan langkah diagnosis atau perbaikan tanpa sumber teknis tambahan.",
            "Pertahankan sebagai draf dan minta konfirmasi teknisi atau dokumentasi resmi."
        )

    if code in notes:
        return notes[code]

    return (
        "Cocokkan uraian, penyebab, dan butir pemeriksaan dengan bagian 4-6 manual.",
        "Periksa apakah solusi di database mengikuti langkah manual dan tidak menambahkan asumsi.",
        "Pastikan tindakan operator dibedakan dari pekerjaan teknisi dan prosedur berisiko."
    )

def esc(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

machine = conn.execute("""
    SELECT id, model, function, description, notes
    FROM machines WHERE id = 17
""").fetchone()

rows = conn.execute("""
    SELECT id, code, problem, symptoms, possible_cause,
           solution, safety_notes, source
    FROM troubleshooting
    WHERE machine_id = 17
    ORDER BY id
""").fetchall()

integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
conn.close()

actual = [r["code"] for r in rows]

if not machine:
    raise SystemExit("GAGAL: mesin ID 17 tidak ditemukan.")
if len(rows) != 43:
    raise SystemExit(f"GAGAL: diharapkan 43 entri, ditemukan {len(rows)}.")
if len(set(actual)) != 43:
    raise SystemExit("GAGAL: ada kode kosong atau duplikat.")
if set(actual) != set(expected):
    print("Kode hilang:", sorted(set(expected) - set(actual)))
    print("Kode tambahan:", sorted(set(actual) - set(expected)))
    raise SystemExit("GAGAL: daftar kode tidak cocok.")
if integrity != "ok":
    raise SystemExit(f"GAGAL: integrity_check = {integrity}")
if fk_errors:
    raise SystemExit(f"GAGAL: foreign_key_check menemukan {len(fk_errors)} masalah.")

draft_count = sum(
    "DRAF_PERLU_VERIFIKASI_TEKNIS" in (r["source"] or "")
    or "DRAF_REVISI_PERLU_VERIFIKASI_TEKNIS" in (r["source"] or "")
    for r in rows
)

lines = [
    "# Matriks Revisi Teknis — JUKI DDL-9000CS",
    "",
    f"Tanggal dibuat: {date.today().isoformat()}",
    "",
    "## Status dan batasan",
    "",
    "- Dokumen kerja untuk audit teknis, bukan pengesahan akhir.",
    "- Database dibuka dalam mode baca-saja; skrip tidak mengubah database.",
    "- Acuan: JUKI DDL-9000C-S Instruction Manual, bagian 4-6, List of errors, halaman cetak 52–54.",
    "- Kecocokan manual DDL-9000C-S dengan varian mesin berlabel DDL-9000CS belum dianggap terkonfirmasi.",
    "- Jangan mengubah status draf sebelum pemeriksaan teknis dan kecocokan varian disetujui.",
    "",
    "## Validasi awal",
    "",
    f"- Mesin: {esc(machine['model'])} (ID 17)",
    f"- Entri ditemukan: {len(rows)}",
    f"- Kode unik: {len(set(actual))}",
    f"- Entri dengan penanda draf yang dikenali: {draft_count}",
    f"- Integritas SQLite: `{integrity}`",
    f"- Kesalahan foreign key: {len(fk_errors)}",
    "- Perubahan database: tidak ada.",
    "",
    "## Matriks tinjauan per kode",
    "",
    "| ID | Kode | Masalah saat ini | Gejala | Kemungkinan penyebab | Solusi saat ini | Catatan audit manual | Usulan tindak lanjut | Catatan keselamatan | Sumber saat ini |",
    "|---:|---|---|---|---|---|---|---|---|---|"
]

for r in rows:
    finding, action, safety_review = audit_note(r["code"])
    lines.append(
        f"| {r['id']} | {esc(r['code'])} | {esc(r['problem'])} | "
        f"{esc(r['symptoms'])} | {esc(r['possible_cause'])} | "
        f"{esc(r['solution'])} | {esc(finding)} | {esc(action)} | "
        f"{esc((r['safety_notes'] or '') + ' ' + safety_review)} | "
        f"{esc(r['source'])} |"
    )

lines += [
    "",
    "## Daftar perhatian khusus",
    "",
    "1. **E000:** manual menyebut 'not an error'; pastikan penjelasan di aplikasi tidak membuat operator menganggapnya kerusakan.",
    "2. **E072, E904, E922, E924, E971, E973, E975:** tidak ada butir pemeriksaan pada daftar manual yang ditinjau. Jangan mengarang langkah perbaikan.",
    "3. **Kecocokan varian:** verifikasi label mesin, panel, kotak kontrol, dan versi manual sebelum mengesahkan data.",
    "4. **Kode lainnya:** cocokkan teks solusi dan penyebab satu per satu dengan manual; catatan umum dalam matriks bukan bukti bahwa setiap solusi telah diverifikasi.",
    "5. **Keselamatan:** prosedur listrik, motor, sensor, dan penggantian komponen harus dibatasi pada personel kompeten sesuai manual.",
    "",
    "## Referensi resmi",
    "",
    "Manual JUKI DDL-9000C-S:",
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/ddl9000cs/menu/ddl9000cs/pdf/instruction_eg.pdf",
    "",
    "Catatan: matriks ini menyalin isi yang sekarang tersimpan di database dan menambahkan catatan audit. Usulan tindak lanjut bukan prosedur servis final."
]

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("BERHASIL:", OUT)
print("Entri:", len(rows))
print("Kode unik:", len(set(actual)))
print("Entri bertanda draf:", draft_count)
print("Integritas:", integrity)
print("Foreign key error:", len(fk_errors))
print("Database tidak diubah.")
