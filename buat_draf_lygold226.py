import csv
from pathlib import Path

out = Path("audit-kelengkapan/draf_lygold_lga105e_but.csv")

fields = [
    "machine_id", "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source", "code"
]

source = (
    "IIGM Pvt. Ltd. - LYGOLD LG A105E Automatic Elastic Joining Machine, "
    "Product Overview; usulan berbasis fungsi produk; "
    "DRAF_PERLU_VERIFIKASI_TEKNIS"
)

safety = (
    "Ikuti SOP keselamatan dan isolasi energi sebelum pemeriksaan bagian "
    "bergerak. Jangan membuka panel listrik atau menyervis sistem ultrasonik "
    "kecuali oleh teknisi yang berwenang. Verifikasi prosedur pada manual resmi."
)

rows = [
    {
        "machine_id": 226,
        "problem": "Hasil potong ultrasonik tidak rapi",
        "symptoms": "Tepi elastis tampak tidak rata atau hasil potong tidak konsisten.",
        "possible_cause": "Kemungkinan posisi material, kondisi area potong, atau setelan sistem potong; belum terverifikasi.",
        "solution": "Periksa posisi dan jalur material sesuai SOP. Jika masalah berlanjut, minta teknisi memeriksa sistem potong berdasarkan manual resmi.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
    {
        "machine_id": 226,
        "problem": "Penandaan pena tidak muncul atau meleset",
        "symptoms": "Tanda tidak terlihat atau posisinya tidak sesuai target.",
        "possible_cause": "Kemungkinan tinta, posisi pena, material, atau parameter penandaan; belum terverifikasi.",
        "solution": "Periksa tinta dan posisi pena serta parameter yang diizinkan operator. Catat hasil sebelum meminta penyesuaian teknis.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
    {
        "machine_id": 226,
        "problem": "Sensor atau kamera tidak mendeteksi logo",
        "symptoms": "Logo tidak terdeteksi atau posisi logo yang diproses tidak tepat.",
        "possible_cause": "Kemungkinan lensa kotor, pencahayaan, posisi logo, atau sistem sensor; belum terverifikasi.",
        "solution": "Periksa kebersihan lensa, pencahayaan, dan posisi material sesuai SOP. Jika tetap gagal, minta teknisi memeriksa sistem deteksi.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
    {
        "machine_id": 226,
        "problem": "Posisi sambungan elastis tidak tepat",
        "symptoms": "Sambungan berada di luar posisi yang diharapkan.",
        "possible_cause": "Kemungkinan penempatan material atau parameter proses; belum terverifikasi.",
        "solution": "Periksa pemasangan material dan parameter yang ditetapkan. Uji dengan prosedur produksi yang disetujui sebelum melanjutkan produksi.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
    {
        "machine_id": 226,
        "problem": "Panjang elastis tidak sesuai target",
        "symptoms": "Panjang hasil potong berbeda dari nilai yang ditentukan.",
        "possible_cause": "Kemungkinan jalur material, setelan panjang, atau sistem pengukuran; belum terverifikasi.",
        "solution": "Bandingkan setelan dengan hasil ukur aktual dan periksa jalur material. Kalibrasi atau servis hanya mengikuti prosedur resmi.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
    {
        "machine_id": 226,
        "problem": "Elastis tersangkut atau bentuknya tidak konsisten",
        "symptoms": "Aliran material terhambat atau bentuk elastis berubah-ubah.",
        "possible_cause": "Kemungkinan jalur masuk material atau perangkat pembentuk; belum terverifikasi.",
        "solution": "Hentikan proses sesuai SOP dan isolasi energi sebelum memeriksa jalur material. Jangan menarik material dari mekanisme yang masih bergerak.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
    {
        "machine_id": 226,
        "problem": "Hasil jahitan tidak konsisten",
        "symptoms": "Jahitan tampak berbeda antarproduk atau tidak sesuai standar kualitas.",
        "possible_cause": "Kemungkinan benang, jarum, pemasangan material, atau setelan jahitan; belum terverifikasi.",
        "solution": "Periksa benang, jarum, dan pemasangan material sesuai SOP. Penyetelan mekanisme jahit harus mengacu pada manual yang sesuai dengan unit.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
    {
        "machine_id": 226,
        "problem": "Layar sentuh atau kontrol tidak merespons",
        "symptoms": "Input operator tidak ditanggapi atau kontrol tampak tidak normal.",
        "possible_cause": "Kemungkinan antarmuka, catu daya, atau sistem kontrol; belum terverifikasi.",
        "solution": "Catat kondisi dan pesan yang tampil. Ikuti prosedur penghentian dan penyalaan ulang yang resmi; jangan membuka panel listrik.",
        "safety_notes": safety,
        "source": source,
        "code": "",
    },
]

with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

with out.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    checked = list(reader)

problems = [r["problem"].strip() for r in checked]
assert len(checked) == 8, "Jumlah baris tidak sesuai"
assert all(r["machine_id"] == "226" for r in checked), "ID mesin tidak sesuai"
assert all(r["problem"].strip() and r["source"].strip() for r in checked), "Kolom wajib kosong"
assert len(set(problems)) == len(problems), "Ada masalah duplikat"
assert all(not r["code"].strip() for r in checked), "Kode harus kosong sampai diverifikasi"
assert all("DRAF_PERLU_VERIFIKASI_TEKNIS" in r["source"] for r in checked)

print("DRAF BERHASIL DIBUAT")
print("File:", out)
print("Jumlah baris:", len(checked))
print("Masalah duplikat:", len(problems) - len(set(problems)))
print("Kode alarm:", "semua kosong (belum ada sumber resmi)")
print("Status:", "semua DRAF_PERLU_VERIFIKASI_TEKNIS")
print("Database: tidak diubah")
