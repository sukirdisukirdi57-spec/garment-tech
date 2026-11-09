
import json

p = "tmp/ddl8000csm-audit/draf-data-juki.json"

isi = {
    "PEDAL": {
        "problem": "Proses inisialisasi pedal belum selesai",
        "symptoms": "Panel menampilkan PEDAL",
        "possible_cause": "Posisi awal pedal belum dikenali oleh sistem",
        "solution": "Ikuti petunjuk manual untuk menyelesaikan inisialisasi pedal. Pada manual seri ini, pedal ditekan pada bagian belakang untuk menjalankan proses awal.",
        "safety_notes": "Pastikan area sekitar pedal bebas hambatan dan mesin tidak bergerak tanpa disengaja.",
    },
    "P_OFF": {
        "problem": "Indikasi mesin dalam keadaan mati",
        "symptoms": "Panel menampilkan P_OFF",
        "possible_cause": "Catu daya mesin dimatikan atau sistem sedang menunjukkan kondisi daya mati",
        "solution": "Jika hendak menyalakan mesin, ikuti prosedur pengoperasian resmi. Pastikan area mesin aman sebelum menghidupkan daya.",
        "safety_notes": "Jangan memeriksa bagian listrik internal. Matikan daya sebelum membersihkan atau memeriksa bagian mekanis.",
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

print("Draf PEDAL dan P_OFF berhasil diperbarui.")
