import sqlite3

DB = "database/garment.db"

data = {
    192: "WT169P",
    193: "W264P",
    194: "FS703P",
}

problems = [
    (
        "Benang sering putus",
        "Jalur benang kurang tepat, tegangan benang tidak sesuai, jarum rusak, atau komponen jalur benang kotor.",
        "Periksa kembali jalur benang, kondisi jarum, kebersihan area benang, dan sesuaikan tegangan secara bertahap.",
        "Matikan mesin sebelum melakukan pemeriksaan atau pembersihan.",
    ),
    (
        "Jahitan loncat",
        "Jarum tidak sesuai atau rusak, pemasangan jarum kurang tepat, atau pembentukan loop benang terganggu.",
        "Periksa ukuran dan pemasangan jarum, ganti jarum bila rusak, lalu periksa kembali jalur dan ketegangan benang.",
        "Matikan mesin sebelum mengganti jarum atau menyentuh area jarum.",
    ),
    (
        "Jahitan tidak rapi atau tidak stabil",
        "Tegangan benang tidak seimbang, jarum atau benang tidak sesuai, atau area pembentukan jahitan kotor.",
        "Periksa benang, jarum, tegangan benang, dan bersihkan area pembentukan jahitan.",
        "Lakukan pemeriksaan dengan mesin dalam kondisi berhenti.",
    ),
    (
        "Kain mengerut",
        "Tekanan sepatu, tegangan benang, atau kondisi feeding tidak sesuai dengan material.",
        "Periksa feeding, tekanan sepatu, dan tegangan benang. Lakukan penyesuaian bertahap sesuai material.",
        "Hindari melakukan penyetelan saat mesin sedang beroperasi.",
    ),
    (
        "Kain tidak terumpan dengan stabil",
        "Area feeding kotor, tekanan atau posisi komponen feeding tidak sesuai, atau material tidak sesuai dengan penyetelan mesin.",
        "Bersihkan area feeding dan periksa kondisi serta posisi komponen feeding. Sesuaikan penyetelan dengan material.",
        "Matikan mesin sebelum membersihkan atau memeriksa mekanisme feeding.",
    ),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    # Safety check
    for machine_id, model in data.items():
        row = cur.execute("""
            SELECT m.id, m.model, b.name
            FROM machines m
            JOIN brands b ON b.id = m.brand_id
            WHERE m.id = ?
        """, (machine_id,)).fetchone()

        if not row:
            raise RuntimeError(f"Machine ID {machine_id} tidak ditemukan")

        if row[2] != "PEGASUS":
            raise RuntimeError(
                f"Machine ID {machine_id} bukan PEGASUS: {row[2]}"
            )

        count = cur.execute("""
            SELECT COUNT(*)
            FROM troubleshooting
            WHERE machine_id = ?
        """, (machine_id,)).fetchone()[0]

        if count != 0:
            raise RuntimeError(
                f"{model} sudah memiliki {count} troubleshooting"
            )

    # Transaction
    total = 0

    for machine_id, model in data.items():
        for problem, cause, solution, safety in problems:
            cur.execute("""
                INSERT INTO troubleshooting
                (machine_id, problem, symptoms, possible_cause,
                 solution, safety_notes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                machine_id,
                problem,
                problem,
                cause,
                solution,
                safety,
                f"Prosedur troubleshooting umum PEGASUS {model}"
            ))
            total += 1

    conn.commit()

    print("INSERT BERHASIL :", total)
    print("COMMIT : OK")

    for machine_id, model in data.items():
        count = cur.execute("""
            SELECT COUNT(*)
            FROM troubleshooting
            WHERE machine_id = ?
        """, (machine_id,)).fetchone()[0]
        print(f"{model} | ID {machine_id} | Troubleshooting: {count}")

except Exception as e:
    conn.rollback()
    print("ROLLBACK : OK")
    print("ERROR :", e)

finally:
    conn.close()
