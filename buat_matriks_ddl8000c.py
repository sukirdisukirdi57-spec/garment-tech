import sqlite3
from pathlib import Path
from datetime import date

DB = Path("database/garment.db")
OUT = Path("audit-kelengkapan/matriks_revisi_teknis_ddl8000c.md")

# Temuan dirangkum dari manual resmi JUKI DDL-8000C,
# bagian 5-4, halaman cetak 52–57 yang telah diperiksa.
# Semua usulan masih draf, bukan instruksi servis final.

data = {
"E01": ("Tegangan input terlalu tinggi; manual menyebut >300 VAC (130 VAC).",
        "Hentikan penggunaan bila tegangan suplai di luar spesifikasi. Minta teknisi kompeten memeriksa suplai dan konfigurasi listrik sebelum mesin digunakan kembali.",
        "Cantumkan angka batas hanya setelah tegangan nominal dan varian kontrol terkonfirmasi.",
        "Jangan membuka panel atau mengukur rangkaian bertegangan tanpa kompetensi dan alat yang sesuai.", 52),
"E02": ("Tegangan input terlalu rendah; manual menyebut <150 VAC (80 VAC).",
        "Hentikan penggunaan bila tegangan suplai di luar spesifikasi. Minta teknisi kompeten memeriksa suplai dan konfigurasi listrik sebelum mesin digunakan kembali.",
        "Pastikan angka pada manual berlaku untuk varian dan konfigurasi daya mesin ini.", 
        "Pemeriksaan listrik hanya oleh teknisi kompeten; jangan menyentuh bagian bertegangan.", 52),
"E03": ("Gangguan komunikasi CPU/panel.",
        "Matikan daya. Periksa konektor dan kabel panel apakah longgar atau rusak. Setelah sambungan dipastikan baik, nyalakan kembali. Jika kode berulang, hubungi servis untuk pemeriksaan panel/kontrol.",
        "Manual mengarahkan pemeriksaan konektor/kabel lalu pemeriksaan kontrol bila gangguan menetap.",
        "Matikan mesin dan putuskan suplai sebelum pemeriksaan konektor.", 52),
"E05": ("Sinyal pedal tidak normal.",
        "Matikan daya. Periksa konektor dan kabel pedal. Jika kode tetap muncul, minta teknisi memeriksa sensor pedal dan kotak kontrol.",
        "Perjelas pemeriksaan kabel sebelum menyimpulkan kerusakan komponen.",
        "Jangan memeriksa konektor saat daya menyala.", 52),
"E07": ("Rotor motor poros utama terkunci.",
        "Matikan daya. Periksa apakah roda mesin dapat diputar secara manual dengan wajar. Jika macet, periksa kemungkinan hambatan mekanis tanpa memaksa. Teknisi memeriksa konektor daya motor dan posisi berhenti jarum.",
        "Tambahkan pemeriksaan hambatan mekanis dan posisi jarum sesuai manual.",
        "Jangan memaksa roda atau menjalankan mesin saat mekanisme macet.", 52),
"E09": ("Sinyal penentuan posisi atas encoder motor poros utama tidak normal.",
        "Matikan daya. Minta teknisi memeriksa konektor encoder, pengaturan koreksi posisi awal motor, serta cakram encoder dari kotoran atau oli. Jika belum pulih, hubungi servis.",
        "Manual mengelompokkan E09 dan E11 dengan uraian serta prosedur yang sama.",
        "Pemeriksaan encoder dilakukan saat daya mati; penggantian komponen oleh teknisi.", 53),
"E10": ("Arus berlebih pada solenoid.",
        "Matikan daya. Pemeriksaan rangkaian solenoid dan penelusuran penyebab harus dilakukan teknisi mengikuti prosedur manual. Jika gangguan berlanjut, periksa solenoid terkait dan kotak kontrol melalui servis.",
        "Gunakan istilah 'solenoid'. Diagnosis manual membedakan kemungkinan solenoid penjepit benang dan pelepas tegangan benang.",
        "Jangan melepas konektor atau menguji aktuator pada rangkaian bertegangan sebagai tindakan operator.", 53),
"E11": ("Sinyal penentuan posisi atas encoder motor poros utama tidak normal.",
        "Matikan daya. Minta teknisi memeriksa konektor encoder, pengaturan koreksi posisi awal motor, serta cakram encoder dari kotoran atau oli. Jika belum pulih, hubungi servis.",
        "Uraian E11 sama dengan E09 dalam daftar manual yang diperiksa; pertahankan kedua kode.",
        "Pemeriksaan encoder dilakukan saat daya mati; penggantian komponen oleh teknisi.", 53),
"E14": ("Sinyal encoder motor poros utama tidak normal.",
        "Matikan daya. Teknisi memeriksa konektor encoder, pemasangan cakram dan sekrup pengunci, posisi cakram terhadap elemen encoder, serta kontaminasi oli.",
        "Lengkapi pemeriksaan cakram encoder, posisi pemasangan, dan sekrup pengunci.",
        "Jangan menyetel encoder saat mesin berdaya; servis diperlukan bila gangguan menetap.", 53),
"E15": ("Arus motor poros utama berlebih.",
        "Matikan daya. Minta teknisi memeriksa koneksi kabel daya motor, kontak yang buruk, dan kemungkinan kabel terjepit. Jika tidak ditemukan penyebab, hubungi servis.",
        "Sebutkan kemungkinan koneksi buruk atau kabel terjepit sesuai manual.",
        "Jangan membuka kotak kontrol atau memeriksa kabel bertegangan.", 53),
"E17": ("Sensor mendeteksi kepala mesin miring.",
        "Matikan daya. Pastikan kepala mesin berada pada posisi operasi normal. Teknisi memeriksa penyetelan sensor kemiringan bila kode tetap muncul.",
        "Bedakan posisi kepala yang tidak normal dari kemungkinan masalah sensor.",
        "Amankan kepala mesin sebelum pemeriksaan; jangan bekerja di bawah kepala yang tidak terkunci.", 53),
"E20": ("Motor poros utama gagal mulai.",
        "Matikan daya. Teknisi memeriksa konektor daya motor, konektor encoder, dan pengaturan koreksi posisi awal motor. Jika gagal pulih, hubungi servis.",
        "Masukkan pemeriksaan kedua konektor dan koreksi posisi awal.",
        "Pemeriksaan konektor hanya saat daya mati.", 54),
"E32": ("Berkas tidak kompatibel.",
        "Gunakan berkas yang kompatibel dengan mesin dan sistem kontrol. Periksa format dan versi berkas sebelum memuatnya kembali.",
        "Manual mengidentifikasi ketidakcocokan berkas; prosedur rinci tidak dicantumkan pada bagian yang diperiksa.",
        "Simpan salinan berkas asli sebelum mengganti atau memuat data.", 54),
"E46": ("Kesalahan reset watchdog timer.",
        "Matikan lalu nyalakan kembali mesin satu kali. Jika kode muncul lagi, hentikan penggunaan dan hubungi teknisi servis.",
        "Manual menyarankan siklus daya; gangguan berulang perlu ditangani servis.",
        "Pastikan mesin berhenti aman sebelum mematikan dan menyalakan kembali.", 54),
"E60": ("Gangguan pada resistor regeneratif.",
        "Matikan daya. Minta teknisi memeriksa koneksi dan kondisi resistor regeneratif. Ganti resistor jika rusak; jika gangguan tetap ada, periksa kotak kontrol melalui servis.",
        "Lengkapi pemeriksaan dengan tindakan penggantian resistor bila diperlukan.",
        "Tunggu hingga mesin aman dan daya terputus sebelum pemeriksaan; komponen listrik ditangani teknisi.", 54),
"E70": ("Kesalahan sistem.",
        "Matikan lalu nyalakan kembali mesin. Jika kode berulang, catat kondisi kemunculannya dan hubungi servis.",
        "Manual menyarankan memulai ulang daya; jangan menebak penyebab spesifik tanpa diagnosis.",
        "Pastikan mesin berhenti aman sebelum siklus daya.", 54),
"E71": ("Kesalahan CRC; data tersimpan rusak.",
        "Jangan langsung menginisialisasi data. Minta teknisi memeriksa instruksi parameter U272 pada manual dan mengamankan pengaturan yang diperlukan sebelum melakukan inisialisasi.",
        "Manual mengarahkan ke U272 untuk inisialisasi data tersimpan; dampak terhadap pengaturan harus dipastikan dahulu.",
        "Inisialisasi dapat memengaruhi data/pengaturan. Cadangkan atau catat pengaturan yang diperlukan dan ikuti manual varian yang tepat.", 54),
"E72": ("Kehilangan fase pada suplai tiga fase.",
        "Hentikan penggunaan. Teknisi kompeten harus memastikan jenis suplai dan tegangan sesuai spesifikasi mesin, lalu memeriksa koneksi serta suplai tiga fase.",
        "Manual menyebut suplai AC tiga fase 220 V; konfirmasi spesifikasi instalasi dan varian sebelum menggunakan angka tersebut.",
        "Jangan melepas steker atau membuka sambungan listrik tanpa prosedur isolasi daya yang aman.", 54),
"E80": ("Komunikasi antara chip utama dan chip penggerak tidak normal.",
        "Matikan daya. Jika kode tetap muncul setelah pemeriksaan dasar sesuai manual, hubungi servis untuk diagnosis kotak kontrol.",
        "Manual mengarahkan pemeriksaan/penggantian kotak kontrol oleh servis.",
        "Jangan membuka atau memperbaiki papan elektronik sendiri.", 54),
"E82": ("Arus motor pitch berlebih.",
        "Matikan daya. Periksa apakah mekanisme motor pitch terhambat. Jika tidak ada hambatan yang jelas, teknisi memeriksa konektor daya dan encoder motor.",
        "Tambahkan pemeriksaan hambatan mekanis sebelum dugaan kerusakan komponen.",
        "Jangan memaksa mekanisme bergerak; pemeriksaan konektor saat daya mati.", 54),
"E84": ("Gangguan fase Z motor pitch.",
        "Matikan daya. Teknisi memeriksa hambatan mekanis, konektor encoder, pemasangan dan pemusatan cakram encoder, sekrup pengunci, serta kemungkinan oli pada cakram.",
        "Perjelas pemeriksaan cakram encoder dan kontaminasi oli.",
        "Pemeriksaan dan penyetelan dilakukan saat daya mati oleh teknisi.", 55),
"E85": ("Sinyal encoder motor pitch tidak normal.",
        "Matikan daya. Teknisi memeriksa konektor encoder, pemasangan dan pemusatan cakram, sekrup pengunci, serta kontaminasi oli.",
        "Lengkapi pemeriksaan encoder; hindari menyimpulkan motor rusak sebelum pemeriksaan dasar.",
        "Pemeriksaan dan penyetelan dilakukan saat daya mati oleh teknisi.", 55),
"E86": ("Kegagalan operasi motor pitch.",
        "Matikan daya. Teknisi memeriksa konektor encoder, pemasangan dan pemusatan cakram, sekrup pengunci, serta kemungkinan oli pada cakram. Jika masalah menetap, hubungi servis.",
        "Manual memberi prosedur pemeriksaan yang serupa dengan pemeriksaan encoder motor pitch; kode tetap dibedakan.",
        "Pemeriksaan dan penyetelan dilakukan saat daya mati oleh teknisi.", 55),
"E87": ("Motor pitch terkunci.",
        "Matikan daya. Teknisi memeriksa hambatan mekanis, kemudian konektor daya motor dan konektor encoder. Jika kode menetap, hubungi servis.",
        "Pastikan kemungkinan penguncian mekanis diperiksa terlebih dahulu.",
        "Jangan memaksa motor atau mekanisme yang terkunci.", 56),
"E92": ("Arus berlebih pada motor pemotong benang/penekan benang.",
        "Matikan daya. Teknisi memeriksa hambatan mekanis dan konektor daya serta encoder motor. Jika gangguan berulang, hubungi servis.",
        "Perjelas nama aktuator dan urutan pemeriksaan dasar.",
        "Jangan menggerakkan mekanisme pemotong secara paksa.", 56),
"E94": ("Gangguan fase Z motor pemotong benang/penekan benang.",
        "Matikan daya. Teknisi memeriksa gerakan mekanisme, hambatan mekanis, konektor encoder, dan kontaminasi oli pada cakram encoder.",
        "Tambahkan pemeriksaan gerakan mekanis dan kontaminasi encoder.",
        "Jangan menyentuh mekanisme pemotong sebelum mesin aman dan daya terputus.", 56),
"E95": ("Sinyal encoder motor pemotong benang/penekan benang tidak normal.",
        "Matikan daya. Teknisi memeriksa konektor encoder. Jika gangguan tetap ada, lakukan diagnosis komponen melalui servis.",
        "Pertahankan pemeriksaan konektor sebagai langkah awal.",
        "Pemeriksaan konektor hanya saat daya mati.", 56),
"E96": ("Motor pemotong benang/penekan benang gagal mulai.",
        "Matikan daya. Teknisi memeriksa konektor daya dan encoder motor. Jika masalah tidak teratasi, hubungi servis.",
        "Cantumkan kedua konektor sesuai manual.",
        "Jangan menguji motor dengan mekanisme terbuka atau saat tidak aman.", 56),
"E97": ("Motor pemotong benang/penekan benang terkunci.",
        "Matikan daya. Teknisi memeriksa hambatan mekanis dan konektor daya serta encoder motor. Jika gangguan berlanjut, hubungi servis.",
        "Urutan pemeriksaan dimulai dari kemungkinan hambatan mekanis.",
        "Jangan memaksa mekanisme pemotong yang terkunci.", 57),
"E100": ("Beban motor poros utama berlebih.",
        "Matikan daya. Teknisi memeriksa apakah beban mekanis terlalu tinggi dan memeriksa pengaturan koreksi posisi awal motor. Jika kode menetap, hubungi servis.",
        "Tambahkan pemeriksaan beban mekanis dan koreksi posisi awal.",
        "Jangan menjalankan mesin jika mekanisme terasa berat atau macet.", 57),
"E110": ("Gangguan penerimaan data panel saat daya dinyalakan.",
        "Matikan daya. Teknisi memeriksa konektor panel. Jika gangguan tetap muncul, hubungi servis untuk pemeriksaan panel dan kotak kontrol.",
        "Sebutkan konektor panel serta kemungkinan pemeriksaan panel/kontrol jika masalah menetap.",
        "Matikan daya sebelum memeriksa konektor.", 57),
"PEDAL": ("Inisialisasi awal belum selesai.",
         "Pastikan area sekitar mesin aman, lalu tekan pedal ke arah belakang untuk menyelesaikan inisialisasi awal.",
         "Manual menyebut pedal digerakkan ke belakang untuk inisialisasi.",
         "Pastikan tidak ada orang atau benda di area jarum dan mekanisme sebelum mengoperasikan pedal.", 57),
"P_OFF": ("Indikasi daya mati.",
          "Matikan sakelar dan tunggu hingga layar padam sepenuhnya sebelum menyalakan kembali.",
          "Pertahankan prosedur menunggu layar padam sebelum daya dinyalakan kembali.",
          "Jangan memutus dan menyambung daya berulang kali dengan tergesa-gesa.", 57),
}

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
rows = conn.execute("""
    SELECT id, code, problem, symptoms, possible_cause,
           solution, safety_notes, source
    FROM troubleshooting
    WHERE machine_id = 16
    ORDER BY id
""").fetchall()
integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
conn.close()

codes = [r["code"] for r in rows]
if len(rows) != 33 or len(set(codes)) != 33:
    raise SystemExit(f"GAGAL: diharapkan 33 baris/kode unik, ditemukan {len(rows)} baris.")
if set(codes) != set(data):
    missing = sorted(set(data) - set(codes))
    extra = sorted(set(codes) - set(data))
    raise SystemExit(f"GAGAL: kode tidak cocok. Hilang={missing}, tambahan={extra}")
if integrity != "ok":
    raise SystemExit(f"GAGAL: integritas database {integrity}")

def esc(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()

lines = [
    "# Matriks Revisi Teknis — JUKI DDL-8000C",
    "",
    f"Tanggal pembuatan: {date.today().isoformat()}",
    "",
    "## Status dan batasan",
    "",
    "- Dokumen kerja; **belum merupakan persetujuan teknis final**.",
    "- Database dibuka dalam mode baca-saja. Skrip ini tidak mengubah database.",
    "- Rujukan: manual resmi JUKI DDL-8000C, bagian 5-4, daftar kode kesalahan, halaman cetak 52–57.",
    "- Pastikan kecocokan varian, panel/kotak kontrol, dan konfigurasi listrik sebelum mengesahkan instruksi.",
    "- Semua entri tetap `DRAF_PERLU_VERIFIKASI_TEKNIS` sampai diperiksa teknisi yang kompeten.",
    "",
    f"## Validasi awal",
    "",
    f"- Jumlah entri mesin ID 16: {len(rows)}",
    f"- Jumlah kode unik: {len(set(codes))}",
    f"- Integritas SQLite: `{integrity}`",
    "- Perubahan database: tidak ada (mode baca-saja).",
    "",
    "## Matriks per kode",
    "",
    "| ID | Kode | Masalah di database | Temuan manual | Usulan revisi solusi | Alasan revisi | Keselamatan | Halaman |",
    "|---:|---|---|---|---|---|---|---:|",
]
for r in rows:
    finding, proposal, reason, safety, page = data[r["code"]]
    lines.append(
        f"| {r['id']} | {esc(r['code'])} | {esc(r['problem'])} | "
        f"{esc(finding)} | {esc(proposal)} | {esc(reason)} | {esc(safety)} | {page} |"
    )

lines += [
    "",
    "## Pemeriksaan wajib sebelum status draf diubah",
    "",
    "1. Cocokkan model/varian mesin dan versi manual dengan pelat mesin serta sistem kontrol.",
    "2. Verifikasi angka tegangan E01/E02 dan konfigurasi suplai E72 terhadap spesifikasi instalasi aktual.",
    "3. Verifikasi makna parameter U272 dan konsekuensi inisialisasi sebelum instruksi E71 disahkan.",
    "4. Minta teknisi kompeten memeriksa istilah, langkah diagnosis, dan batas pekerjaan operator.",
    "5. Setelah verifikasi, revisi isi database hanya melalui proses perubahan yang disetujui dan dengan backup tervalidasi.",
    "",
    "## Sumber resmi",
    "",
    "Manual JUKI DDL-8000C:",
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/ddl8000c/menu/8000c/pdf/instruction_jp.pdf",
    "",
    "Halaman produk resmi:",
    "https://www.juki.co.jp/industrial_e/products_e/apparel_e/1needle_lock_e/detail.php?cd=DDL-8000C_E",
    "",
    "Catatan: usulan bahasa Indonesia di atas merupakan ringkasan kerja dari bagian manual yang telah diperiksa, bukan pengganti manual lengkap atau prosedur servis resmi.",
]

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("BERHASIL:", OUT)
print("Entri matriks:", len(rows))
print("Kode unik:", len(set(codes)))
print("Integritas DB:", integrity)
print("Database tidak diubah.")
