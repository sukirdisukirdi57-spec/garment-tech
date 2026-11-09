import csv
import sqlite3
from pathlib import Path

db = Path("database/garment.db")
out = Path("audit-kelengkapan/laporan_audit_isi_ddl8700.csv")
ids = (1, 2, 3, 4, 247, 248, 249, 250)

audit = {
    1: (
        "BELUM TERVERIFIKASI",
        "Diagnosis mekanis masih berupa dugaan; manual yang diperiksa "
        "belum mengonfirmasi kondisi motor berputar tetapi jarum tidak bergerak.",
        "Instruksi pemeriksaan mekanisme terlalu umum untuk dijadikan "
        "prosedur perbaikan mandiri.",
        "Sudah menyebut mematikan dan memutus listrik; tambahkan "
        "peringatan agar pemeriksaan mekanis lanjutan dilakukan teknisi.",
        "Minta teknisi memeriksa hubungan penggerak dan mekanisme jarum; "
        "cari referensi servis yang secara khusus membahas gejala ini."
    ),
    2: (
        "DIDUKUNG SEBAGIAN",
        "Pemasangan benang dan tegangan relevan; jarum rusak atau "
        "permukaan tajam masih perlu pemeriksaan langsung.",
        "Pemeriksaan jalur benang dan penyetelan tegangan bertahap masuk akal; "
        "jangan menyimpulkan satu penyebab tanpa pengujian.",
        "Pastikan listrik diputus sebelum memeriksa jarum, jalur benang, "
        "hook, atau komponen mekanis.",
        "Periksa satu per satu jarum, jalur benang, tegangan, dan kemungkinan "
        "permukaan yang merusak benang; catat hasil pengujian."
    ),
    3: (
        "DIDUKUNG SEBAGIAN",
        "Pemasangan bobbin dan tegangan didukung manual; kerusakan bobbin, "
        "bobbin case, atau permukaan hook belum terbukti.",
        "Pemeriksaan arah, jalur, dan kondisi bobbin relevan; "
        "hindari perubahan tegangan besar tanpa pengujian.",
        "Putuskan listrik sebelum membuka area bobbin atau hook.",
        "Periksa bobbin dan bobbin case, jalur benang, serta kemungkinan "
        "kerusakan; verifikasi penyebab sebelum mengganti komponen."
    ),
    4: (
        "RELEVAN, PENYETELAN PERLU VERIFIKASI",
        "Manual membahas pemasangan jarum dan hubungan jarum–hook; "
        "jarak terlalu besar dapat menyebabkan jahitan loncat.",
        "Pemeriksaan jarum dan pemasangannya layak dilakukan; "
        "penyetelan jarak jarum–hook memerlukan prosedur model yang tepat.",
        "Putuskan listrik sebelum memeriksa atau mengganti jarum; "
        "serahkan penyetelan mekanis kepada teknisi kompeten.",
        "Periksa tipe dan pemasangan jarum dahulu. Jika masalah berlanjut, "
        "verifikasi jarak jarum–hook sesuai manual."
    ),
    247: (
        "RELEVAN, FAKTOR LAIN PERLU VERIFIKASI",
        "Manual mendukung penyetelan tegangan benang atas dan bawah; "
        "kesesuaian bahan atau jalur benang tetap perlu diperiksa.",
        "Penyetelan bertahap dan uji pada bahan yang sama sesuai; "
        "hindari mengubah beberapa setelan sekaligus.",
        "Putuskan listrik sebelum pemeriksaan mekanis; jauhkan tangan "
        "dari bagian bergerak saat pengujian.",
        "Periksa pemasangan benang dan bobbin, lalu ubah tegangan sedikit "
        "demi sedikit sambil mencatat hasil jahitan."
    ),
    248: (
        "DIDUKUNG SEBAGIAN",
        "Pemasangan jarum dan hubungan jarum–hook relevan; timing feed "
        "bukan penyebab yang otomatis terbukti untuk setiap jarum patah.",
        "Periksa tipe, kondisi, pemasangan, dan kemungkinan jarum membentur "
        "komponen sebelum menjalankan mesin kembali.",
        "Putuskan listrik sebelum mengganti jarum atau memeriksa area jarum.",
        "Periksa tanda benturan dan kesesuaian jarum. Jangan menyetel timing "
        "atau cam tanpa prosedur manual dan teknisi kompeten."
    ),
    249: (
        "RELEVAN, SEBAGIAN PENYEBAB PERLU VERIFIKASI",
        "Manual membahas panjang jahitan, tekanan sepatu, feed dog, "
        "dan timing; kotor atau aus perlu pemeriksaan fisik.",
        "Pemeriksaan feed dog dan tekanan sepatu relevan; "
        "hindari penyetelan mekanisme tanpa mengikuti manual.",
        "Putuskan listrik sebelum membersihkan atau memeriksa mekanisme feed.",
        "Periksa kebersihan dan kondisi feed dog, tekanan sepatu, serta "
        "pengaturan panjang jahitan; uji pada bahan yang sama."
    ),
    250: (
        "DIDUKUNG SEBAGIAN",
        "Manual mendukung pemeriksaan pelumasan dan suplai oli, "
        "tetapi tidak membuktikan penyebab semua suara atau getaran.",
        "Hentikan mesin bila suara atau getaran berat belum diketahui "
        "penyebabnya; jangan terus mengoperasikan mesin untuk menguji.",
        "Putuskan listrik sebelum membuka penutup atau memeriksa komponen. "
        "Pemeriksaan internal dilakukan teknisi kompeten.",
        "Periksa pelumasan sesuai manual. Minta teknisi memeriksa sumber "
        "suara atau getaran sebelum mesin dipakai kembali."
    ),
}

if not db.is_file():
    raise SystemExit(f"Database tidak ditemukan: {db}")

if out.exists():
    raise SystemExit(
        f"BERHENTI: {out} sudah ada. "
        "Jangan menimpa laporan lama; gunakan nama file baru."
    )

uri = f"file:{db.resolve()}?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SystemExit(f"BERHENTI: integrity_check = {integrity}")

    placeholders = ",".join("?" for _ in ids)
    rows = con.execute(f"""
        SELECT id, machine_id, problem, symptoms, possible_cause,
               solution, safety_notes, source
        FROM troubleshooting
        WHERE id IN ({placeholders})
        ORDER BY id
    """, ids).fetchall()

    if len(rows) != len(ids):
        raise SystemExit(
            f"BERHENTI: ditemukan {len(rows)} dari {len(ids)} entri."
        )

    report = []
    for r in rows:
        if r["machine_id"] != 3:
            raise SystemExit(f"BERHENTI: ID {r['id']} bukan machine_id 3.")

        status, diagnosis, solusi, keselamatan, tindak_lanjut = audit[r["id"]]
        report.append({
            "id": r["id"],
            "machine_id": r["machine_id"],
            "problem": r["problem"],
            "symptoms": r["symptoms"],
            "possible_cause": r["possible_cause"],
            "solution": r["solution"],
            "safety_notes": r["safety_notes"],
            "source": r["source"],
            "status_audit": status,
            "penilaian_diagnosis": diagnosis,
            "penilaian_solusi": solusi,
            "penilaian_keselamatan": keselamatan,
            "tindak_lanjut": tindak_lanjut,
            "integrity_check": integrity,
        })
finally:
    con.close()

fields = list(report[0].keys())
with out.open("x", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(report)

print("BERHASIL: laporan audit isi dibuat.")
print(f"File: {out}")
print(f"Jumlah entri: {len(report)}")
print("Database dibuka hanya-baca; tidak ada data yang diubah.")
print("Catatan: penilaian ini adalah hasil audit awal, bukan diagnosis teknisi.")
