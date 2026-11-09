import csv
import sqlite3
from pathlib import Path

db = Path("database/garment.db")
out = Path("audit-kelengkapan/draf_perbaikan_isi_ddl8700.csv")
ids = (1, 2, 3, 4, 247, 248, 249, 250)

proposals = {
    1: {
        "possible_cause": (
            "Penyebab belum terverifikasi. Kemungkinan terdapat masalah pada "
            "hubungan mekanis penggerak dan mekanisme jarum, tetapi kondisi "
            "aktual perlu diperiksa teknisi."
        ),
        "solution": (
            "Hentikan mesin dan putuskan sumber listrik. Jangan membongkar "
            "atau menyetel mekanisme penggerak tanpa prosedur servis yang sesuai. "
            "Minta teknisi kompeten memeriksa mengapa motor berputar tetapi "
            "jarum tidak bergerak. Uji kembali hanya setelah pemeriksaan aman."
        ),
        "safety_notes": (
            "Matikan mesin dan putuskan sumber listrik sebelum pemeriksaan. "
            "Jangan menyentuh bagian bergerak atau menjalankan mesin dengan "
            "penutup pelindung dilepas. Pemeriksaan mekanis lanjutan dilakukan "
            "teknisi kompeten."
        ),
    },
    2: {
        "possible_cause": (
            "Benang atas dapat putus akibat pemasangan benang yang tidak tepat, "
            "kondisi atau pemasangan jarum, tegangan benang yang terlalu tinggi, "
            "atau gesekan pada jalur benang. Penyebab pastinya perlu diperiksa."
        ),
        "solution": (
            "Putuskan listrik sebelum memeriksa jarum dan jalur benang. Periksa "
            "kondisi serta pemasangan jarum dan ikuti jalur pemasangan benang "
            "sesuai manual. Periksa area yang mungkin menggesek benang. Jika "
            "tegangan perlu disetel, ubah sedikit demi sedikit dan uji pada "
            "bahan yang sama dengan pelindung terpasang."
        ),
        "safety_notes": (
            "Putuskan sumber listrik sebelum mengganti jarum atau memeriksa "
            "jalur benang dan komponen mekanis. Jauhkan tangan dari bagian "
            "bergerak saat pengujian."
        ),
    },
    3: {
        "possible_cause": (
            "Benang bawah dapat putus karena pemasangan atau jalur benang "
            "bobbin yang tidak tepat, masalah pada bobbin atau bobbin case, "
            "tegangan yang tidak sesuai, atau gesekan pada area hook. "
            "Penyebab pastinya belum terkonfirmasi."
        ),
        "solution": (
            "Putuskan listrik sebelum membuka area bobbin atau hook. Periksa "
            "kondisi bobbin dan bobbin case, arah serta jalur benang sesuai "
            "manual, dan tanda kerusakan yang terlihat. Setel tegangan hanya "
            "secara bertahap sesuai prosedur. Jika ada kerusakan atau masalah "
            "berulang, minta teknisi memeriksanya."
        ),
        "safety_notes": (
            "Matikan mesin dan putuskan sumber listrik sebelum membuka area "
            "bobbin atau hook. Jangan menyentuh bagian bergerak atau melakukan "
            "penyetelan mekanis saat mesin beroperasi."
        ),
    },
    4: {
        "possible_cause": (
            "Jahitan loncat dapat berkaitan dengan kondisi atau pemasangan "
            "jarum dan hubungan jarum–hook. Penyebab lain perlu diperiksa "
            "berdasarkan gejala dan manual mesin."
        ),
        "solution": (
            "Putuskan listrik, lalu periksa kondisi, tipe, dan pemasangan jarum "
            "sesuai manual. Jika jahitan tetap loncat, minta teknisi kompeten "
            "memeriksa hubungan serta jarak jarum–hook menggunakan prosedur "
            "dan spesifikasi model yang tepat. Jangan mengubah penyetelan "
            "mekanis berdasarkan perkiraan."
        ),
        "safety_notes": (
            "Putuskan sumber listrik sebelum mengganti jarum atau memeriksa "
            "area jarum. Pemeriksaan dan penyetelan jarum–hook dilakukan "
            "teknisi kompeten sesuai manual."
        ),
    },
    247: {
        "possible_cause": (
            "Jahitan terlalu kencang atau longgar dapat berkaitan dengan "
            "tegangan benang atas atau bawah dan pemasangan benang. "
            "Kesesuaian benang, jarum, serta bahan juga perlu diperiksa "
            "sebelum menentukan penyebab."
        ),
        "solution": (
            "Periksa pemasangan benang atas dan bobbin sesuai manual. "
            "Ubah tegangan sedikit demi sedikit, satu perubahan pada satu "
            "waktu, lalu uji pada bahan yang sama. Jika hasil tidak membaik, "
            "periksa kembali pemasangan benang dan minta bantuan teknisi "
            "sebelum mengubah setelan mekanis lain."
        ),
        "safety_notes": (
            "Putuskan listrik sebelum memeriksa jarum, hook, atau komponen "
            "mekanis. Saat melakukan uji jahit, pasang kembali pelindung "
            "dan jauhkan tangan dari bagian bergerak."
        ),
    },
    248: {
        "possible_cause": (
            "Jarum patah dapat berkaitan dengan jarum yang bengkok atau rusak, "
            "tipe atau ukuran yang tidak sesuai, pemasangan yang keliru, "
            "atau benturan dengan komponen maupun bahan. Penyebab pastinya "
            "harus diperiksa sebelum mesin digunakan kembali."
        ),
        "solution": (
            "Hentikan mesin dan putuskan listrik. Periksa jarum dan pastikan "
            "tipe, ukuran, serta pemasangannya sesuai manual. Periksa tanda "
            "benturan pada jarum dan komponen di sekitarnya. Jika benturan "
            "berulang atau penyebabnya tidak jelas, jangan menjalankan mesin "
            "kembali sebelum diperiksa teknisi. Jangan menyetel timing atau "
            "cam tanpa prosedur servis yang tepat."
        ),
        "safety_notes": (
            "Putuskan sumber listrik sebelum mengganti jarum atau memeriksa "
            "area jarum. Jangan menguji mesin jika jarum berulang kali patah "
            "atau diduga membentur komponen."
        ),
    },
    249: {
        "possible_cause": (
            "Kain yang tidak maju dengan baik dapat berkaitan dengan "
            "pengaturan panjang jahitan, tekanan sepatu, kondisi atau "
            "kebersihan feed dog, dan timing pengumpan. Faktor penyebab "
            "perlu dipastikan melalui pemeriksaan."
        ),
        "solution": (
            "Putuskan listrik sebelum membersihkan atau memeriksa area feed "
            "dog. Periksa kebersihan dan kondisi yang terlihat, lalu pastikan "
            "panjang jahitan dan tekanan sepatu sesuai manual serta bahan. "
            "Uji pada bahan yang sama. Jika masalah berlanjut, minta teknisi "
            "memeriksa timing dan penyetelan mekanis."
        ),
        "safety_notes": (
            "Matikan mesin dan putuskan sumber listrik sebelum membersihkan "
            "atau memeriksa mekanisme pengumpan. Penyetelan timing atau "
            "komponen mekanis dilakukan teknisi sesuai manual."
        ),
    },
    250: {
        "possible_cause": (
            "Suara atau getaran abnormal dapat berkaitan dengan pelumasan "
            "atau masalah mekanis, tetapi penyebabnya tidak dapat dipastikan "
            "tanpa pemeriksaan."
        ),
        "solution": (
            "Hentikan mesin jika suara atau getaran berat, muncul mendadak, "
            "atau penyebabnya tidak diketahui. Putuskan listrik sebelum "
            "pemeriksaan. Periksa pelumasan hanya sesuai prosedur manual "
            "yang berlaku. Minta teknisi memeriksa sumber suara atau getaran "
            "sebelum mesin digunakan kembali jika masalah belum jelas."
        ),
        "safety_notes": (
            "Jangan terus mengoperasikan mesin dengan suara atau getaran "
            "berat yang belum diketahui penyebabnya. Putuskan sumber listrik "
            "sebelum membuka penutup atau memeriksa komponen internal. "
            "Pemeriksaan internal dilakukan teknisi kompeten."
        ),
    },
}

if not db.is_file():
    raise SystemExit(f"Database tidak ditemukan: {db}")
if out.exists():
    raise SystemExit(
        f"BERHENTI: {out} sudah ada. Gunakan nama file baru agar "
        "draf lama tidak tertimpa."
    )

con = sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SystemExit(f"BERHENTI: integrity_check = {integrity}")

    marks = ",".join("?" for _ in ids)
    rows = con.execute(f"""
        SELECT id, machine_id, problem, possible_cause, solution,
               safety_notes, source
        FROM troubleshooting
        WHERE id IN ({marks})
        ORDER BY id
    """, ids).fetchall()

    if len(rows) != len(ids):
        raise SystemExit(f"BERHENTI: hanya menemukan {len(rows)} dari 8 entri.")

    report = []
    for r in rows:
        if r["machine_id"] != 3:
            raise SystemExit(f"BERHENTI: machine_id salah untuk ID {r['id']}.")

        p = proposals[r["id"]]
        report.append({
            "id": r["id"],
            "machine_id": r["machine_id"],
            "problem": r["problem"],
            "possible_cause_lama": r["possible_cause"],
            "possible_cause_usulan": p["possible_cause"],
            "solution_lama": r["solution"],
            "solution_usulan": p["solution"],
            "safety_notes_lama": r["safety_notes"],
            "safety_notes_usulan": p["safety_notes"],
            "source_tidak_diubah": r["source"],
            "status": "DRAF UNTUK DITINJAU - BELUM DITERAPKAN",
        })
finally:
    con.close()

with out.open("x", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(report[0].keys()))
    writer.writeheader()
    writer.writerows(report)

print("BERHASIL: draf usulan perbaikan dibuat.")
print(f"File: {out}")
print(f"Jumlah entri: {len(report)}")
print("Database hanya dibaca; tidak ada perubahan database.")
print("Semua usulan masih perlu ditinjau sebelum disetujui.")
