
import json

p = "tmp/ddl8000csm-audit/draf-data-juki.json"

isi = {
    "E46": {
        "problem": "Kegagalan reset watchdog sistem",
        "symptoms": "Panel menampilkan E46",
        "possible_cause": "Sistem kontrol mengalami gangguan atau reset tidak berhasil",
        "solution": "Matikan mesin, tunggu sebentar, lalu nyalakan kembali. Jika kode muncul lagi, hubungi teknisi.",
        "safety_notes": "Jangan membuka kotak kontrol atau mengubah komponen internal sendiri.",
    },
    "E60": {
        "problem": "Gangguan pada resistor regeneratif",
        "symptoms": "Panel menampilkan E60",
        "possible_cause": "Resistor regeneratif atau rangkaian penggeraknya bermasalah",
        "solution": "Matikan mesin dan hubungi teknisi untuk pemeriksaan.",
        "safety_notes": "Komponen daya dapat menyimpan tegangan berbahaya. Jangan membuka kotak kontrol.",
    },
    "E70": {
        "problem": "Kesalahan sistem",
        "symptoms": "Panel menampilkan E70",
        "possible_cause": "Sistem kontrol mengalami gangguan",
        "solution": "Matikan mesin, tunggu sebentar, lalu nyalakan kembali. Jika kode berulang, hubungi teknisi.",
        "safety_notes": "Jangan mengubah parameter atau membongkar sistem kontrol tanpa petunjuk teknisi.",
    },
    "E71": {
        "problem": "Kesalahan CRC atau pemeriksaan data sistem",
        "symptoms": "Panel menampilkan E71",
        "possible_cause": "Data sistem atau pemeriksaan integritas data mengalami kegagalan",
        "solution": "Catat kode yang tampil dan hubungi teknisi atau layanan resmi JUKI untuk petunjuk pemulihan.",
        "safety_notes": "Jangan menjalankan pemulihan setelan pabrik tanpa persetujuan karena data atau setelan tersimpan dapat terhapus atau berubah.",
    },
    "E72": {
        "problem": "Kegagalan fase pada catu daya tiga fase",
        "symptoms": "Panel menampilkan E72",
        "possible_cause": "Salah satu fase sumber listrik tiga fase tidak tersedia atau bermasalah",
        "solution": "Matikan mesin dan minta teknisi listrik memeriksa sumber daya serta sambungan sesuai spesifikasi mesin.",
        "safety_notes": "Jangan membuka panel listrik atau memperbaiki kabel tiga fase sendiri.",
    },
    "E80": {
        "problem": "Gangguan komunikasi antara chip utama dan chip penggerak",
        "symptoms": "Panel menampilkan E80",
        "possible_cause": "Sistem kontrol atau kotak kontrol mengalami gangguan",
        "solution": "Matikan mesin dan hubungi teknisi atau layanan resmi JUKI untuk pemeriksaan.",
        "safety_notes": "Pemeriksaan dan penggantian kotak kontrol harus dilakukan teknisi yang kompeten.",
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
