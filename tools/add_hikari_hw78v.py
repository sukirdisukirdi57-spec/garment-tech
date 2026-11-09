import sqlite3

DB = "database/garment.db"
MACHINE_ID = 148
MODEL = "HW78V"

PROBLEMS = [
    (
        "Benang sering putus",
        "Benang putus saat mesin berjalan.",
        "Jalur benang tidak benar, tegangan terlalu tinggi, atau jarum/looper bermasalah.",
        "Periksa jalur benang, kondisi jarum dan looper, lalu sesuaikan tegangan secara bertahap.",
        "Matikan mesin sebelum threading atau pemeriksaan.",
    ),
    (
        "Jahitan loncat / tidak terbentuk",
        "Sebagian jahitan tidak terbentuk atau jahitan terputus.",
        "Jarum bengkok/salah pasang atau interaksi jarum dan looper tidak sesuai.",
        "Periksa pemasangan dan kondisi jarum serta area looper. Penyetelan mekanisme dilakukan teknisi kompeten.",
        "Matikan mesin sebelum memeriksa jarum dan looper.",
    ),
    (
        "Jahitan interlock tidak rapi",
        "Jahitan terlihat tidak seimbang, longgar, atau tidak menutup tepi kain dengan baik.",
        "Tegangan benang, jalur benang, atau penyetelan mesin tidak sesuai bahan.",
        "Periksa seluruh jalur benang dan sesuaikan tegangan secara bertahap. Uji pada potongan bahan sebelum produksi.",
        "Matikan mesin sebelum melakukan penyetelan.",
    ),
    (
        "Jarum patah",
        "Jarum patah saat menjahit atau mengenai bagian mesin.",
        "Jarum rusak/salah pasang atau terdapat gangguan antara jarum dan looper.",
        "Ganti jarum yang sesuai dan periksa pemasangan serta area jarum-looper.",
        "Matikan mesin sebelum mengganti jarum atau memeriksa area jarum.",
    ),
    (
        "Benang looper putus / jahitan tidak mengunci",
        "Benang looper putus atau jahitan tidak membentuk kuncian dengan baik.",
        "Jalur atau tegangan benang looper tidak sesuai atau terdapat masalah pada looper.",
        "Periksa jalur dan tegangan benang looper serta kondisi looper. Penyetelan mekanisme dilakukan teknisi kompeten.",
        "Matikan mesin sebelum threading atau pemeriksaan looper.",
    ),
]


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
        (MACHINE_ID,),
    )
    jumlah = cur.fetchone()[0]

    if jumlah != 0:
        print(f"STOP: {MODEL} sudah memiliki {jumlah} troubleshooting.")
        print("Tidak ada data yang dimasukkan.")
        conn.close()
        return

    source = f"HIKARI {MODEL} Instruction Manual"

    for problem, symptoms, cause, solution, safety in PROBLEMS:
        cur.execute(
            """
            INSERT INTO troubleshooting
            (machine_id, problem, symptoms, possible_cause,
             solution, safety_notes, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                MACHINE_ID,
                problem,
                symptoms,
                cause,
                solution,
                safety,
                source,
            ),
        )

    conn.commit()

    cur.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
        (MACHINE_ID,),
    )
    print(f"HASIL HW78V: {cur.fetchone()[0]} troubleshooting")

    conn.close()


if __name__ == "__main__":
    main()
