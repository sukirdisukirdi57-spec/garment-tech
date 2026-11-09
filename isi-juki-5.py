
import json

p = "tmp/ddl8000csm-audit/draf-data-juki.json"

isi = {
    "E94": {
        "problem": "Gangguan sinyal fase Z motor pemotong benang atau penekan sepatu",
        "symptoms": "Panel menampilkan E94",
        "possible_cause": "Mekanisme macet atau encoder maupun sambungannya bermasalah",
        "solution": "Matikan mesin dan periksa hambatan yang terlihat. Jika kode tetap muncul, hubungi teknisi.",
        "safety_notes": "Pemeriksaan encoder dan konektor internal harus dilakukan teknisi.",
    },
    "E95": {
        "problem": "Sinyal encoder motor pemotong benang atau penekan sepatu tidak normal",
        "symptoms": "Panel menampilkan E95",
        "possible_cause": "Encoder, kabel, atau konektor motor mengalami gangguan",
        "solution": "Matikan mesin. Jika kode tetap muncul, minta teknisi memeriksa sistem encoder.",
        "safety_notes": "Jangan membuka kotak kontrol atau memeriksa rangkaian bertegangan sendiri.",
    },
    "E96": {
        "problem": "Motor pemotong benang atau penekan sepatu gagal mulai",
        "symptoms": "Panel menampilkan E96 dan motor terkait tidak mulai bergerak",
        "possible_cause": "Motor, mekanisme, atau sistem pengendalinya mengalami gangguan",
        "solution": "Matikan mesin. Jika kode tetap muncul, hubungi teknisi untuk pemeriksaan.",
        "safety_notes": "Jangan membongkar motor atau konektor internal sendiri.",
    },
    "E97": {
        "problem": "Motor pemotong benang atau penekan sepatu terkunci",
        "symptoms": "Panel menampilkan E97",
        "possible_cause": "Mekanisme macet atau motor tidak dapat bergerak normal",
        "solution": "Matikan mesin dan periksa hambatan yang terlihat tanpa memaksa mekanisme. Hubungi teknisi jika tetap macet.",
        "safety_notes": "Putuskan sumber listrik sebelum pemeriksaan dan jauhkan tangan dari bagian bergerak.",
    },
    "E100": {
        "problem": "Motor poros utama mengalami beban berlebih",
        "symptoms": "Panel menampilkan E100",
        "possible_cause": "Beban mekanis berlebihan atau gangguan pada motor dan sistem penggeraknya",
        "solution": "Matikan mesin. Periksa hambatan yang terlihat tanpa memaksa mekanisme. Jika kode berulang, hubungi teknisi.",
        "safety_notes": "Jangan membuka kotak kontrol atau menyentuh rangkaian listrik internal.",
    },
    "E110": {
        "problem": "Gangguan penerimaan data pada panel operasi saat mesin dinyalakan",
        "symptoms": "Panel menampilkan E110",
        "possible_cause": "Komunikasi data panel atau sistem kontrol mengalami gangguan",
        "solution": "Matikan mesin, tunggu sebentar, lalu nyalakan kembali. Jika kode muncul lagi, hubungi teknisi.",
        "safety_notes": "Pemeriksaan kabel internal dan sistem kontrol harus dilakukan teknisi.",
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
