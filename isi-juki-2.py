
import json

p = "tmp/ddl8000csm-audit/draf-data-juki.json"

isi = {
    "E11": {
        "problem": "Sinyal posisi atas encoder motor poros utama tidak normal",
        "symptoms": "Panel menampilkan E11",
        "possible_cause": "Encoder, kabel, konektor, atau penyetelan posisi motor bermasalah",
        "solution": "Matikan mesin. Jika kode tetap muncul, minta teknisi memeriksa encoder dan penyetelannya.",
        "safety_notes": "Pemeriksaan encoder dan bagian dalam kontrol harus dilakukan teknisi.",
    },
    "E14": {
        "problem": "Sinyal encoder motor poros utama tidak normal",
        "symptoms": "Panel menampilkan E14",
        "possible_cause": "Encoder, kabel, konektor, atau sistem penggerak bermasalah",
        "solution": "Matikan mesin. Jika kode tetap muncul, hubungi teknisi untuk pemeriksaan.",
        "safety_notes": "Jangan membuka kotak kontrol atau melakukan pemeriksaan listrik internal sendiri.",
    },
    "E15": {
        "problem": "Arus penggerak motor poros utama terlalu tinggi",
        "symptoms": "Panel menampilkan E15",
        "possible_cause": "Motor terbebani atau terdapat gangguan pada kabel maupun sistem penggerak",
        "solution": "Matikan mesin dan periksa kabel luar yang terlihat. Jika kode tetap muncul, hubungi teknisi.",
        "safety_notes": "Jangan membuka kotak kontrol atau menyentuh kabel listrik internal.",
    },
    "E17": {
        "problem": "Sensor kemiringan kepala mesin mendeteksi posisi tidak normal",
        "symptoms": "Panel menampilkan E17",
        "possible_cause": "Kepala mesin miring atau sensor kemiringan mengalami gangguan",
        "solution": "Periksa apakah kepala mesin berada pada posisi normal. Jika kode tetap muncul, hubungi teknisi.",
        "safety_notes": "Matikan mesin sebelum pemeriksaan. Jangan mengangkat atau menurunkan kepala mesin tanpa penyangga yang benar.",
    },
    "E20": {
        "problem": "Motor poros utama gagal mulai",
        "symptoms": "Panel menampilkan E20 dan motor tidak mulai beroperasi",
        "possible_cause": "Gangguan koneksi, penyetelan posisi, atau sistem penggerak motor",
        "solution": "Matikan mesin. Jika kode tetap muncul setelah dinyalakan kembali, hubungi teknisi.",
        "safety_notes": "Pemeriksaan konektor internal dan penyetelan motor harus dilakukan teknisi.",
    },
    "E32": {
        "problem": "Berkas yang digunakan tidak kompatibel",
        "symptoms": "Panel menampilkan E32 saat menggunakan atau memuat berkas",
        "possible_cause": "Berkas tidak sesuai dengan format atau versi yang didukung mesin",
        "solution": "Periksa berkas dan gunakan berkas yang sesuai dengan petunjuk resmi untuk model mesin.",
        "safety_notes": "Jangan memulihkan atau mengubah data sistem tanpa memahami dampaknya.",
    },
}

with open(p, encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    if item["code"] in isi:
        item.update(isi[item["code"]])
        item["source"] = "Manual JUKI DDL-8000C Series; perlu verifikasi varian."
        item["model_compatibility"] = "Belum diverifikasi untuk setiap varian mesin"

with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Draf 6 kode berhasil diperbarui.")
