import csv
import sqlite3
from pathlib import Path

base = Path("audit-kelengkapan")
db = Path("database/garment.db")
draft_file = base / "draf_source_ddl8700.csv"
preview_file = base / "pratinjau_perubahan_source_ddl8700.csv"
output = base / "laporan_audit_final_ddl8700.csv"

expected_ids = {1, 2, 3, 4, 247, 248, 249, 250}

notes = {
    1: (
        "Bagian manual yang diperiksa belum mengonfirmasi diagnosis khusus ini.",
        "Perlu pemeriksaan teknisi dan referensi teknis yang secara khusus membahas "
        "motor berputar tetapi jarum tidak bergerak."
    ),
    2: (
        "Manual mendukung pemeriksaan pemasangan benang, tegangan, dan take-up spring; "
        "tidak semua penyebab benang putus terkonfirmasi.",
        "Periksa referensi khusus tentang jarum, gesekan benang, dan permukaan komponen."
    ),
    3: (
        "Manual mendukung pemasangan bobbin dan tegangan benang; penyebab spesifik "
        "benang bawah putus belum terbukti seluruhnya.",
        "Cari referensi khusus tentang kerusakan bobbin, bobbin case, dan permukaan hook."
    ),
    4: (
        "Referensi §18 relevan dan mengaitkan jarak hook–jarum yang terlalu besar "
        "dengan jahitan loncat.",
        "Pastikan tipe mesin dan prosedur penyetelan sesuai manual; serahkan penyetelan "
        "mekanis kepada teknisi kompeten."
    ),
    247: (
        "§15 mendukung penyetelan tegangan benang atas dan bawah; faktor material "
        "belum tentu dibuktikan oleh bagian ini.",
        "Uji perubahan tegangan bertahap pada bahan yang sama."
    ),
    248: (
        "§8 dan §18 relevan untuk jarum serta hubungan jarum–hook. §21 membahas feed "
        "timing dan memperingatkan penyetelan cam berlebihan dapat menyebabkan jarum patah.",
        "Periksa jarum dan kemungkinan benturan; verifikasi penyebab sebelum menyetel timing."
    ),
    249: (
        "§10, §11, dan §§19–21 relevan untuk panjang jahitan, tekanan sepatu, feed dog, "
        "dan timing; kotor atau aus belum dibuktikan secara khusus oleh referensi ini.",
        "Periksa kebersihan dan kondisi feed dog; penyetelan mekanis mengikuti manual."
    ),
    250: (
        "§6–7 relevan untuk pelumasan dan suplai oli, tetapi tidak menjelaskan semua "
        "penyebab suara atau getaran abnormal.",
        "Periksa pelumasan sesuai manual; hentikan mesin jika getaran atau suara berat "
        "belum diketahui penyebabnya."
    ),
}

if output.exists():
    raise SystemExit(
        f"BERHENTI: {output} sudah ada. "
        "Pilih nama output baru agar file lama tidak tertimpa."
    )

for path in (db, draft_file, preview_file):
    if not path.is_file():
        raise SystemExit(f"File tidak ditemukan: {path}")

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

draft_rows = read_csv(draft_file)
preview_rows = read_csv(preview_file)

drafts = {int(r["troubleshooting_id"]): r for r in draft_rows}
previews = {int(r["id"]): r for r in preview_rows}

if len(draft_rows) != 8 or set(drafts) != expected_ids:
    raise SystemExit("BERHENTI: isi CSV draf tidak cocok dengan 8 ID yang diaudit.")

if len(preview_rows) != 8 or set(previews) != expected_ids:
    raise SystemExit("BERHENTI: isi pratinjau tidak cocok dengan 8 ID yang diaudit.")

uri = f"file:{db.resolve()}?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SystemExit(f"BERHENTI: integrity_check menghasilkan {integrity!r}.")

    rows = con.execute("""
        SELECT id, machine_id, problem, source
        FROM troubleshooting
        WHERE id IN (1, 2, 3, 4, 247, 248, 249, 250)
        ORDER BY id
    """).fetchall()

    if len(rows) != 8:
        raise SystemExit("BERHENTI: jumlah entri database tidak sama dengan 8.")

    report = []
    for row in rows:
        tid = row["id"]
        if row["machine_id"] != 3:
            raise SystemExit(f"BERHENTI: machine_id ID {tid} bukan 3.")

        draft = drafts[tid]
        preview = previews[tid]

        if draft["source_draf"] != preview["source_baru_draf"]:
            raise SystemExit(f"BERHENTI: draf dan pratinjau berbeda pada ID {tid}.")

        if row["source"] != draft["source_draf"]:
            raise SystemExit(
                f"BERHENTI: source database tidak cocok dengan draf pada ID {tid}."
            )

        gap, action = notes[tid]
        report.append({
            "id": tid,
            "machine_id": row["machine_id"],
            "problem": row["problem"],
            "status_verifikasi": draft["status_verifikasi"],
            "source_tersimpan": row["source"],
            "catatan_bukti": gap,
            "tindak_lanjut": action,
            "status_pencocokan_database": "COCOK",
            "integrity_check": integrity,
        })

finally:
    con.close()

fields = [
    "id", "machine_id", "problem", "status_verifikasi",
    "source_tersimpan", "catatan_bukti", "tindak_lanjut",
    "status_pencocokan_database", "integrity_check"
]

with output.open("x", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(report)

print("BERHASIL: laporan audit dibuat.")
print(f"File: {output}")
print(f"Jumlah entri: {len(report)}")
print("Pencocokan sumber: semua cocok dengan draf yang disetujui.")
print("Database dibuka hanya-baca; tidak ada data database yang diubah.")
