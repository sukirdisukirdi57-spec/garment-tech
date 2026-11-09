import sqlite3
from pathlib import Path
from datetime import date

DB = Path("database/garment.db")
OUT = Path("audit-kelengkapan/matriks_koreksi_teknis_ddl9000cs_revisi2.md")

# Temuan bersifat usulan audit, bukan pengesahan teknis.
notes = {
    "E000": ("Rendah", "Manual menyatakan bukan error.", "Pertahankan sebagai status/inisialisasi, bukan kerusakan; jelaskan bahwa tidak diperlukan perbaikan khusus."),
    "E007": ("Prioritas tinggi", "Deskripsi motor overload dan penyebab penggantian kepala mesin perlu dicocokkan.", "Verifikasi teks lengkap manual sebelum mengubah penyebab atau solusi."),
    "E009": ("Prioritas tinggi", "Deskripsi solenoid aktif terlalu lama perlu diselaraskan dengan langkah pemeriksaan pulley dan motor.", "Bandingkan langsung dengan baris E009 di manual. Selaraskan tabel awal dan Revisi 1."),
    "E011": ("Sedang", "Kode media tidak terpasang; solusi masih umum.", "Verifikasi tindakan spesifik pada manual."),
    "E012": ("Sedang", "Kesalahan membaca data; solusi masih umum.", "Verifikasi tindakan spesifik pada manual."),
    "E013": ("Sedang", "Kesalahan menulis data; solusi masih umum.", "Verifikasi tindakan spesifik pada manual."),
    "E014": ("Sedang", "Media write-protect; solusi perlu menyebut pemeriksaan status perlindungan tulis bila didukung manual.", "Cocokkan instruksi persis dengan manual."),
    "E015": ("Sedang", "Kesalahan format media; solusi masih umum.", "Verifikasi format dan tindakan yang ditentukan manual; jangan menyarankan pemformatan yang menghapus data tanpa peringatan."),
    "E016": ("Sedang", "Kapasitas media tidak cukup; solusi masih umum.", "Verifikasi tindakan spesifik pada manual."),
    "E032": ("Sedang", "File tidak kompatibel, tetapi solusi hanya menyebut pemeriksaan media.", "Periksa apakah manual menyarankan file yang kompatibel atau tindakan lain."),
    "E071": ("Prioritas tinggi", "Penyebab mencakup konektor dan rangkaian deteksi arus, tetapi solusi hanya memeriksa konektor.", "Selaraskan penyebab dengan instruksi resmi; pemeriksaan rangkaian hanya oleh teknisi."),
    "E072": ("Prioritas tinggi", "Tidak ada item pemeriksaan spesifik pada baris manual yang dirujuk.", "Jangan menambahkan langkah spekulatif; arahkan ke diagnosis teknisi."),
    "E081": ("Sedang", "Motor feed terkunci; solusi menyebut pemeriksaan kelancaran motor.", "Pertahankan sebagai draf dan pastikan nomenklatur motor sesuai manual."),
    "E204": ("Rendah", "USB masih terpasang saat mesin dinyalakan.", "Pertahankan tindakan melepas USB jika cocok dengan manual."),
    "E220": ("Sedang", "Peringatan grease berbasis jumlah jahitan.", "Bedakan dari E221; titik grease dan reset harus mengikuti manual."),
    "E221": ("Sedang", "Error grease yang dapat menghambat operasi.", "Bedakan dari E220; verifikasi prosedur reset dan jenis grease."),
    "E302": ("Prioritas tinggi", "Berkaitan dengan sakelar keselamatan saat kepala mesin miring.", "Pertahankan larangan operasi saat interlock aktif; jangan menganjurkan bypass sakelar."),
    "E303": ("Prioritas tinggi", "Istilah sensor meniskus dan solusi terkait pengaturan kepala/konektor encoder perlu diperiksa.", "Cocokkan penyebab dan prosedur dengan baris manual asli."),
    "E704": ("Prioritas tinggi", "Penulisan ulang versi sistem berisiko jika versi tidak sesuai.", "Tandai sebagai prosedur servis resmi, bukan langkah pengguna umum."),
    "E730": ("Sedang", "Gangguan encoder; CN39 dan kabel disebut.", "Verifikasi nomor konektor pada varian dan diagram kontrol yang tepat."),
    "E731": ("Sedang", "Gangguan sensor lubang motor; prosedur mirip E730.", "Pastikan manual memang memberikan prosedur yang sama."),
    "E733": ("Sedang", "Arah putaran motor terbalik pada kondisi tertentu.", "Verifikasi kondisi kecepatan dan pemeriksaan kabel terhadap manual."),
    "E811": ("Prioritas tinggi", "Tegangan berlebih dan kemungkinan konfigurasi suplai tidak sesuai.", "Pemeriksaan dan konfigurasi tegangan hanya oleh teknisi kompeten dengan prosedur resmi."),
    "E813": ("Prioritas tinggi", "Tegangan rendah dan kemungkinan konfigurasi suplai tidak sesuai.", "Verifikasi spesifikasi unit; jangan menyuruh pengguna mengubah konfigurasi tegangan."),
    "E815": ("Sedang", "Resistor regeneratif tidak terhubung; konektor CN11 disebut.", "Pertahankan sebagai draf; isolasi daya dan verifikasi diagram konektor."),
    "E903": ("Prioritas tinggi", "Gangguan catu 85 V; motor dan sekring F2 disebut sebagai pemeriksaan.", "Verifikasi langkah ini pada manual; pemeriksaan kelistrikan hanya oleh teknisi."),
    "E904": ("Prioritas tinggi", "Gangguan catu 24 V; tidak ada langkah spesifik dalam baris yang dirujuk.", "Jangan mengarang diagnosis; arahkan ke teknisi kompeten."),
    "E910": ("Sedang", "Pencarian titik asal motor presser; memory switch No. 23 disebut.", "Verifikasi nomor pengaturan dan kecocokan varian sebelum dipublikasikan."),
    "E912": ("Sedang", "Deteksi kecepatan motor poros utama.", "Verifikasi pemeriksaan encoder dan kabel pada manual."),
    "E915": ("Sedang", "Komunikasi panel; CN38 dan CN200 disebut.", "Verifikasi nomor konektor sesuai diagram unit."),
    "E922": ("Prioritas tinggi", "Kegagalan kontrol poros utama; tidak ada langkah pemeriksaan spesifik pada baris yang dirujuk.", "Pertahankan rujukan ke teknisi; jangan menebak komponen."),
    "E924": ("Prioritas tinggi", "Gangguan driver motor; perlu dipastikan apakah penyebab merupakan diagnosis pasti atau kemungkinan.", "Cocokkan terjemahan dan instruksi manual; penggantian hanya setelah diagnosis."),
    "E946": ("Sedang", "Kegagalan penulisan EEPROM kepala mesin.", "Verifikasi prosedur pemeriksaan koneksi INT PCB pada manual."),
    "E955": ("Sedang", "Error sensor arus; arus motor yang terukur disebut lebih tinggi dari perkiraan.", "Jangan menyatakan sensor pasti rusak; verifikasi langkah pemeriksaan kabel daya."),
    "E961": ("Sedang", "Deviasi motor pitch; solusi memeriksa kelancaran motor.", "Pertahankan sebagai draf; pemeriksaan mekanis setelah daya diisolasi."),
    "E962": ("Sedang", "Deviasi motor presser; solusi memeriksa kelancaran motor.", "Pertahankan sebagai draf; pastikan istilah motor konsisten."),
    "E971": ("Prioritas tinggi", "Proteksi arus berlebih IPM; tidak ada langkah spesifik pada baris yang dirujuk.", "Jangan menyalin solusi E972 secara otomatis; perlu diagnosis teknisi."),
    "E972": ("Prioritas tinggi", "Kode feed horizontal, tetapi solusi menyebut motor pitch.", "Periksa kemungkinan ketidaksesuaian nama motor dengan manual sebelum koreksi."),
    "E973": ("Prioritas tinggi", "Proteksi arus berlebih IPM; tidak ada langkah spesifik pada baris yang dirujuk.", "Jangan mengarang langkah atau menyalin solusi E974."),
    "E974": ("Prioritas tinggi", "Feed vertikal; perlu dipastikan apakah istilah motor pada solusi sesuai manual.", "Verifikasi nama motor dan tindakan pemeriksaan."),
    "E975": ("Prioritas tinggi", "Proteksi arus berlebih IPM motor presser; tidak ada langkah spesifik pada baris yang dirujuk.", "Jangan menyalin solusi E976 secara otomatis."),
    "E976": ("Prioritas tinggi", "Motor presser horizontal overload.", "Verifikasi istilah horizontal dan hubungan dengan kode presser lainnya."),
    "E985": ("Sedang", "Kegagalan kembali ke titik asal motor pitch atau feed.", "Pastikan motor yang tercakup dan prosedur penyetelan titik asal sesuai manual."),
}

expected = {
    "E000", "E007", "E009", "E011", "E012", "E013", "E014",
    "E015", "E016", "E032", "E071", "E072", "E081", "E204",
    "E220", "E221", "E302", "E303", "E704", "E730", "E731",
    "E733", "E811", "E813", "E815", "E903", "E904", "E910",
    "E912", "E915", "E922", "E924", "E946", "E955", "E961",
    "E962", "E971", "E972", "E973", "E974", "E975", "E976",
    "E985"
}

uri = DB.resolve().as_uri() + "?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row
con.execute("PRAGMA query_only=ON")

rows = con.execute("""
    SELECT id, code, problem, symptoms, possible_cause,
           solution, safety_notes, source
    FROM troubleshooting
    WHERE machine_id = 17
    ORDER BY id
""").fetchall()

integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
fk = con.execute("PRAGMA foreign_key_check").fetchall()
con.close()

codes = [r["code"] for r in rows]
if len(rows) != 43 or len(set(codes)) != 43 or set(codes) != expected:
    raise SystemExit(
        f"GAGAL validasi: baris={len(rows)}, unik={len(set(codes))}, "
        f"kode hilang={sorted(expected-set(codes))}, "
        f"kode tambahan={sorted(set(codes)-expected)}"
    )
if integrity != "ok" or fk:
    raise SystemExit(f"GAGAL integritas: {integrity}; FK error={len(fk)}")
if OUT.exists():
    raise SystemExit(f"GAGAL: file tujuan sudah ada, tidak ditimpa: {OUT}")

def clean(value):
    return str(value or "(kosong)").replace("|", "\\|").replace("\n", " ").strip()

lines = [
    "# Matriks Koreksi Teknis DDL-9000CS — Revisi 2",
    "",
    f"Tanggal pembuatan: {date.today().isoformat()}",
    "",
    "## Tujuan dan batasan",
    "",
    "Dokumen ini merupakan konsolidasi audit data troubleshooting untuk mesin dengan machine_id=17.",
    "Database dibuka dalam mode baca-saja. Dokumen ini tidak mengubah database maupun dokumen revisi sebelumnya.",
    "Peninjauan isi data bukan sertifikasi teknis. Setiap pernyataan yang belum dibandingkan langsung dengan manual lengkap tetap berstatus perlu verifikasi.",
    "",
    "Rujukan manual yang tercatat di data:",
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/ddl9000cs/menu/ddl9000cs/pdf/instruction_eg.pdf",
    "",
    "## Ringkasan",
    "",
    f"- Entri diperiksa: {len(rows)}",
    f"- Kode unik: {len(set(codes))}",
    f"- Entri dengan temuan prioritas tinggi: {sum(1 for r in rows if notes.get(r['code'], ('', '', ''))[0] == 'Prioritas tinggi')}",
    "- Status keseluruhan: draf; verifikasi manual dan kecocokan varian masih diperlukan.",
    "- Kolom gejala perlu ditinjau karena sebagian besar berisi teks generik, bukan gejala spesifik.",
    "",
    "## Matriks 43 kode",
    "",
    "| ID | Kode | Prioritas | Data saat ini: problem | Temuan audit | Usulan koreksi/tindak lanjut |",
    "|---:|---|---|---|---|---|",
]

for r in rows:
    priority, finding, action = notes[r["code"]]
    lines.append(
        f"| {r['id']} | {clean(r['code'])} | {priority} | "
        f"{clean(r['problem'])} | {finding} | {action} |"
    )

lines += [
    "",
    "## Data lengkap saat ini",
    "",
    "Bagian berikut mempertahankan isi aktual dari ekspor baca-saja untuk memudahkan pemeriksaan dan perbandingan.",
    ""
]

for r in rows:
    priority, finding, action = notes[r["code"]]
    lines += [
        f"### ID {r['id']} — {r['code']}",
        "",
        f"- **Prioritas:** {priority}",
        f"- **Problem:** {clean(r['problem'])}",
        f"- **Symptoms:** {clean(r['symptoms'])}",
        f"- **Possible cause:** {clean(r['possible_cause'])}",
        f"- **Solution saat ini:** {clean(r['solution'])}",
        f"- **Safety notes:** {clean(r['safety_notes'])}",
        f"- **Source saat ini:** {clean(r['source'])}",
        f"- **Temuan:** {finding}",
        f"- **Usulan:** {action}",
        "- **Status bukti:** perlu dicocokkan dengan teks manual lengkap dan varian mesin; belum disetujui untuk diterapkan ke database.",
        ""
    ]

lines += [
    "## Temuan lintas-entri",
    "",
    "1. Kolom symptoms berulang dengan kalimat generik. Ganti hanya dengan gejala yang benar-benar didukung manual atau beri label jelas bahwa gejala operasional belum terdokumentasi.",
    "2. Jangan menyalin solusi antarkode yang tampak berpasangan tanpa memeriksa manual, khususnya E971/E972, E973/E974, dan E975/E976.",
    "3. Nomor konektor, sekring, memory switch, konfigurasi tegangan, dan istilah motor harus sesuai dengan varian mesin dan diagram kontrol yang digunakan.",
    "4. Jangan membuat langkah perbaikan untuk kode yang manualnya tidak memberikan langkah spesifik. Arahkan ke teknisi kompeten.",
    "5. Instruksi terkait tegangan, PCB, motor, encoder, dan rangkaian internal harus membatasi pekerjaan tersebut kepada teknisi kompeten dengan prosedur isolasi energi yang tepat.",
    "6. Samakan penilaian E009 antara tabel awal dan bagian revisi sebelumnya agar tidak ada rekomendasi yang saling bertentangan.",
    "",
    "## Pemeriksaan yang belum selesai",
    "",
    "- Verifikasi satu per satu seluruh 43 kode terhadap tabel error dan bagian troubleshooting manual lengkap.",
    "- Konfirmasi varian DDL-9000C yang sebenarnya terpasang, panel kontrol, dan kotak kontrol.",
    "- Verifikasi setiap nomor halaman, konektor, nilai tegangan, serta nomor pengaturan sebelum publikasi.",
    "- Tinjau ulang gejala, penyebab, solusi, dan keselamatan bersama teknisi kompeten.",
    "- Jangan menghapus penanda draf sebelum bukti dan persetujuan teknis terdokumentasi.",
    "",
    "## Validasi pembuatan dokumen",
    "",
    f"- Baris database terbaca: {len(rows)}",
    f"- Kode unik: {len(set(codes))}",
    f"- PRAGMA integrity_check: {integrity}",
    f"- Foreign-key error: {len(fk)}",
    "- Database diubah oleh skrip: TIDAK",
    ""
]

OUT.write_text("\n".join(lines), encoding="utf-8")
print("BERHASIL:", OUT)
print("Baris:", len(rows))
print("Kode unik:", len(set(codes)))
print("Prioritas tinggi:", sum(1 for r in rows if notes.get(r["code"], ("", "", ""))[0] == "Prioritas tinggi"))
print("Integritas:", integrity)
print("Foreign-key error:", len(fk))
print("Database diubah: TIDAK")
print("Dokumen baru:", OUT.stat().st_size, "byte")
