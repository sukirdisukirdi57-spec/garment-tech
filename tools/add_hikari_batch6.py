import sqlite3

DB = "database/garment.db"

DATA = {
    145: "HX8V-16-03B/C",
    143: "HX8V-16-03C",
    131: "HX8V-16-04",
}

PROBLEMS = [
    ("Benang sering putus",
     "Benang putus saat menjahit.",
     "Jalur benang salah, tegangan terlalu tinggi, atau jarum/looper bermasalah.",
     "Periksa jalur benang, jarum, looper, dan sesuaikan tegangan.",
     "Matikan mesin sebelum pemeriksaan."),

    ("Jahitan loncat / tidak terbentuk",
     "Sebagian jahitan tidak terbentuk.",
     "Jarum salah/bengkok atau posisi looper tidak sesuai.",
     "Periksa jarum, jalur benang, dan looper. Penyetelan dilakukan teknisi kompeten.",
     "Matikan mesin sebelum memeriksa jarum/looper."),

    ("Jahitan overlock tidak rapi",
     "Jahitan longgar, ketat, atau tidak seimbang.",
     "Tegangan benang atau jalur benang tidak sesuai.",
     "Periksa jalur benang dan sesuaikan tegangan secara bertahap.",
     "Matikan mesin sebelum penyetelan."),

    ("Jarum patah",
     "Jarum patah saat menjahit.",
     "Jarum rusak/salah pasang atau terjadi gangguan dengan looper.",
     "Ganti jarum yang sesuai dan periksa area jarum-looper.",
     "Matikan mesin sebelum mengganti jarum."),

    ("Benang looper putus / jahitan tidak mengunci",
     "Benang looper putus atau jahitan tidak terkunci.",
     "Jalur/tegangan benang looper tidak sesuai atau looper bermasalah.",
     "Periksa jalur dan tegangan looper serta kondisi looper.",
     "Matikan mesin sebelum pemeriksaan looper."),
]

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    for machine_id, model in DATA.items():
        cur.execute(
            "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
            (machine_id,))
        jumlah = cur.fetchone()[0]

        if jumlah != 0:
            print(f"STOP: {model} sudah memiliki {jumlah} troubleshooting.")
            print("Tidak ada data yang dimasukkan.")
            conn.close()
            return

    for machine_id, model in DATA.items():
        source = f"HIKARI {model} Instruction Manual"

        for problem, symptoms, cause, solution, safety in PROBLEMS:
            cur.execute("""
                INSERT INTO troubleshooting
                (machine_id, problem, symptoms, possible_cause,
                 solution, safety_notes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (machine_id, problem, symptoms, cause,
                  solution, safety, source))

    conn.commit()

    print("\nHASIL BATCH 6:")
    for machine_id, model in DATA.items():
        cur.execute(
            "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
            (machine_id,))
        print(f"{machine_id} | {model} | {cur.fetchone()[0]} troubleshooting")

    conn.close()

if __name__ == "__main__":
    main()
