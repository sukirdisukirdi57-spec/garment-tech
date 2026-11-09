
import json

p = "tmp/ddl8000csm-audit/draf-data-juki.json"

isi = {
    "E01": {
        "problem": "Tegangan listrik terlalu tinggi",
        "symptoms": "Panel menampilkan E01",
        "possible_cause": "Tegangan sumber listrik tidak sesuai spesifikasi",
        "solution": "Matikan mesin dan minta teknisi memeriksa sumber listrik.",
        "safety_notes": "Jangan membuka kotak kontrol atau mengukur rangkaian listrik sendiri.",
    },
    "E02": {
        "problem": "Tegangan listrik terlalu rendah",
        "symptoms": "Panel menampilkan E02",
        "possible_cause": "Tegangan sumber listrik di bawah rentang yang diperlukan",
        "solution": "Matikan mesin dan minta teknisi memeriksa sumber listrik.",
        "safety_notes": "Jangan membuka kotak kontrol atau memperbaiki rangkaian listrik sendiri.",
    },
    "E03": {
        "problem": "Gangguan komunikasi CPU dan panel",
        "symptoms": "Panel menampilkan E03",
        "possible_cause": "Kabel komunikasi atau sistem kontrol bermasalah",
        "solution": "Matikan mesin. Periksa kabel luar yang terlihat; jika masalah berlanjut, hubungi teknisi.",
        "safety_notes": "Pemeriksaan konektor internal harus dilakukan teknisi.",
    },
    "E05": {
        "problem": "Sinyal pedal tidak normal",
        "symptoms": "Panel menampilkan E05 atau respons pedal tidak normal",
        "possible_cause": "Kabel, sambungan, atau sensor pedal bermasalah",
        "solution": "Matikan mesin dan periksa kabel luar pedal. Hubungi teknisi jika tetap bermasalah.",
        "safety_notes": "Jangan membuka rangkaian pedal saat mesin terhubung ke listrik.",
    },
    "E07": {
        "problem": "Motor poros utama terkunci",
        "symptoms": "Panel menampilkan E07 dan mesin tidak berjalan normal",
        "possible_cause": "Mekanisme macet atau motor mengalami gangguan",
        "solution": "Matikan mesin. Periksa hambatan yang terlihat; jangan memaksa pulley berputar.",
        "safety_notes": "Putuskan sumber listrik sebelum pemeriksaan. Hubungi teknisi jika tetap macet.",
    },
    "E09": {
        "problem": "Sinyal posisi atas encoder motor poros utama tidak normal",
        "symptoms": "Panel menampilkan E09",
        "possible_cause": "Encoder, kabel, konektor, atau penyetelan posisi bermasalah",
        "solution": "Matikan mesin. Jika kode tetap muncul, minta teknisi memeriksa encoder.",
        "safety_notes": "Pemeriksaan encoder dan bagian dalam kontrol harus dilakukan teknisi.",
    },
    "E10": {
        "problem": "Arus elektromagnet terlalu tinggi",
        "symptoms": "Panel menampilkan E10",
        "possible_cause": "Elektromagnet atau rangkaian pengendalinya bermasalah",
        "solution": "Matikan mesin dan minta teknisi memeriksa elektromagnet serta rangkaiannya.",
        "safety_notes": "Jangan melepas konektor internal atau menguji rangkaian bertegangan.",
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

print("Draf 7 kode berhasil diperbarui.")
