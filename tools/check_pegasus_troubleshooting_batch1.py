import sqlite3

DB = "database/garment.db"

targets = {
    "M932": [
        ("Benang jarum sering putus", "Benang terlalu tegang, jarum rusak/tidak sesuai, atau jalur benang bermasalah.", "Periksa ukuran dan kondisi jarum, jalur benang, serta sesuaikan tegangan benang.", "Matikan mesin sebelum melakukan penyetelan atau penggantian jarum."),
        ("Jahitan loncat", "Jarum tidak sesuai, pemasangan jarum kurang tepat, atau timing jarum dan looper tidak sesuai.", "Periksa pemasangan dan kondisi jarum serta lakukan pemeriksaan hubungan jarum-looper.", "Matikan mesin sebelum pemeriksaan mekanisme."),
        ("Jahitan tidak terbentuk atau kurang rapi", "Tegangan benang tidak seimbang atau threading tidak sesuai.", "Periksa kembali jalur threading dan setel tegangan benang secara bertahap.", "Lakukan penyetelan saat mesin berhenti."),
        ("Benang looper sering putus", "Threading looper tidak tepat, tegangan terlalu tinggi, atau bagian jalur benang kasar.", "Periksa threading looper, tegangan, dan kondisi jalur benang.", "Matikan mesin sebelum membuka area looper."),
        ("Kain mengerut atau feeding tidak stabil", "Tekanan sepatu, differential feed, atau kondisi feed dog tidak sesuai.", "Periksa pengaturan feeding dan tekanan sepatu sesuai jenis kain.", "Jauhkan tangan dari area jarum dan feed mechanism saat mesin beroperasi."),
    ],
    "M952": [
        ("Benang jarum sering putus", "Benang terlalu tegang, jarum rusak/tidak sesuai, atau jalur benang bermasalah.", "Periksa ukuran dan kondisi jarum, jalur benang, serta sesuaikan tegangan benang.", "Matikan mesin sebelum melakukan penyetelan atau penggantian jarum."),
        ("Jahitan loncat", "Jarum tidak sesuai, pemasangan jarum kurang tepat, atau timing jarum dan looper tidak sesuai.", "Periksa pemasangan dan kondisi jarum serta lakukan pemeriksaan hubungan jarum-looper.", "Matikan mesin sebelum pemeriksaan mekanisme."),
        ("Jahitan tidak terbentuk atau kurang rapi", "Tegangan benang tidak seimbang atau threading tidak sesuai.", "Periksa kembali jalur threading dan setel tegangan benang secara bertahap.", "Lakukan penyetelan saat mesin berhenti."),
        ("Benang looper sering putus", "Threading looper tidak tepat, tegangan terlalu tinggi, atau bagian jalur benang kasar.", "Periksa threading looper, tegangan, dan kondisi jalur benang.", "Matikan mesin sebelum membuka area looper."),
        ("Kain mengerut atau feeding tidak stabil", "Tekanan sepatu, differential feed, atau kondisi feed dog tidak sesuai.", "Periksa pengaturan feeding dan tekanan sepatu sesuai jenis kain.", "Jauhkan tangan dari area jarum dan feed mechanism saat mesin beroperasi."),
    ],
    "M922": [
        ("Benang jarum sering putus", "Benang terlalu tegang, jarum rusak/tidak sesuai, atau jalur benang bermasalah.", "Periksa ukuran dan kondisi jarum, jalur benang, serta sesuaikan tegangan benang.", "Matikan mesin sebelum melakukan penyetelan atau penggantian jarum."),
        ("Jahitan loncat", "Jarum tidak sesuai, pemasangan jarum kurang tepat, atau hubungan jarum dengan looper tidak tepat.", "Periksa pemasangan dan kondisi jarum serta pemeriksaan mekanisme jarum-looper.", "Matikan mesin sebelum pemeriksaan mekanisme."),
        ("Jahitan mudah terurai", "Tegangan benang tidak seimbang atau pembentukan chain stitch tidak stabil.", "Periksa threading dan tegangan benang serta kondisi mekanisme pembentukan jahitan.", "Lakukan pemeriksaan saat mesin berhenti."),
        ("Benang looper atau chain thread putus", "Threading tidak tepat, tegangan terlalu tinggi, atau jalur benang bermasalah.", "Periksa jalur threading, tegangan, dan kondisi jalur benang.", "Matikan mesin sebelum membuka area looper."),
        ("Kain tidak terumpan dengan stabil", "Pengaturan feeding atau tekanan sepatu tidak sesuai dengan material.", "Periksa feed mechanism dan sesuaikan tekanan sepatu dengan jenis kain.", "Jauhkan tangan dari area feeding saat mesin beroperasi."),
    ],
}

con = sqlite3.connect(DB)
cur = con.cursor()

print("=== PEGASUS TROUBLESHOOTING BATCH 1 ===")
print("MODE : SAFETY CHECK ONLY")
print("DATABASE: TIDAK DIUBAH")
print()

errors = []

for model, rows in targets.items():
    machine = cur.execute("""
        SELECT id
        FROM machines
        WHERE brand_id = 10 AND model = ?
    """, (model,)).fetchone()

    if not machine:
        errors.append(f"Mesin {model} tidak ditemukan")
        continue

    machine_id = machine[0]
    existing = cur.execute("""
        SELECT problem
        FROM troubleshooting
        WHERE machine_id = ?
    """, (machine_id,)).fetchall()

    existing_problems = {x[0] for x in existing}

    print(f"{machine_id} | {model} | Rencana: {len(rows)}")

    for problem, cause, solution, safety in rows:
        if problem in existing_problems:
            errors.append(f"{model}: duplikat problem: {problem}")

print()
print(f"TOTAL RENCANA : {sum(len(v) for v in targets.values())}")

if errors:
    print("STATUS: TIDAK AMAN")
    for e in errors:
        print("ERROR:", e)
else:
    print("STATUS: AMAN")
    print("Semua mesin dan data tervalidasi.")
    print("DATABASE TIDAK DIUBAH.")

con.close()
