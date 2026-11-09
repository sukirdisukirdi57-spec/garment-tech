
import json

p = "tmp/ddl8000csm-audit/draf-data-juki.json"

isi = {
    "E82": {
        "problem": "Arus motor pitch terlalu tinggi",
        "symptoms": "Panel menampilkan E82",
        "possible_cause": "Motor pitch terbebani atau sistem penggeraknya mengalami gangguan",
        "solution": "Matikan mesin. Periksa hambatan yang terlihat pada mekanisme; jika kode tetap muncul, hubungi teknisi.",
        "safety_notes": "Pemeriksaan motor, encoder, dan konektor internal harus dilakukan teknisi.",
    },
    "E84": {
        "problem": "Gangguan sinyal fase Z motor pitch",
        "symptoms": "Panel menampilkan E84",
        "possible_cause": "Mekanisme macet atau encoder, kabel, maupun konektornya bermasalah",
        "solution": "Matikan mesin dan periksa apakah ada hambatan yang terlihat. Jika kode tetap muncul, hubungi teknisi.",
        "safety_notes": "Jangan membuka kontrol atau menyetel encoder sendiri.",
    },
    "E85": {
        "problem": "Sinyal encoder motor pitch tidak normal",
        "symptoms": "Panel menampilkan E85",
        "possible_cause": "Encoder, kabel, atau konektor motor pitch mengalami gangguan",
        "solution": "Matikan mesin. Jika kode tetap muncul, minta teknisi memeriksa sistem encoder.",
        "safety_notes": "Pemeriksaan konektor internal dan encoder harus dilakukan teknisi.",
    },
    "E86": {
        "problem": "Gangguan pada motor pitch",
        "symptoms": "Panel menampilkan E86",
        "possible_cause": "Motor pitch atau sistem pengendalinya mengalami gangguan",
        "solution": "Matikan mesin dan hubungi teknisi jika kode tetap muncul.",
        "safety_notes": "Jangan membuka kotak kontrol atau menguji motor dalam keadaan bertegangan.",
    },
    "E87": {
        "problem": "Motor pitch terkunci",
        "symptoms": "Panel menampilkan E87",
        "possible_cause": "Mekanisme pitch macet atau motor tidak dapat bergerak normal",
        "solution": "Matikan mesin dan periksa hambatan yang terlihat tanpa memaksa mekanisme. Jika tetap macet, hubungi teknisi.",
        "safety_notes": "Putuskan sumber listrik sebelum pemeriksaan dan jauhkan tangan dari bagian bergerak.",
    },
    "E92": {
        "problem": "Arus motor pemotong benang atau penekan sepatu terlalu tinggi",
        "symptoms": "Panel menampilkan E92",
        "possible_cause": "Mekanisme terbebani atau motor maupun sistem penggeraknya bermasalah",
        "solution": "Matikan mesin. Periksa hambatan yang terlihat tanpa membongkar komponen. Hubungi teknisi jika kode tetap muncul.",
        "safety_notes": "Jangan membongkar motor, konektor, atau kotak kontrol sendiri.",
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
