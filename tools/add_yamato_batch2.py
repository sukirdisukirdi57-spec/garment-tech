import sqlite3

DB = "database/garment.db"

DATA = {
    152: "VF2400-8",
    153: "VF2500-8",
    154: "FD-62G-01MS",
}

PROBLEMS = [
    (
        "Benang sering putus",
        "Benang putus saat mesin berjalan atau selama proses jahit.",
        "Jalur benang tidak benar, tension terlalu tinggi, jarum bermasalah, atau terdapat gesekan pada thread path.",
        "Periksa threading, tension, kondisi jarum, dan jalur benang.",
        "Matikan mesin sebelum threading, mengganti jarum, atau memeriksa jalur benang.",
    ),
    (
        "Jahitan loncat / tidak terbentuk",
        "Sebagian jahitan tidak terbentuk atau terdapat jahitan yang terlewat.",
        "Jarum salah pasang atau bengkok, threading tidak benar, atau area jarum dan looper perlu diperiksa.",
        "Periksa pemasangan jarum, threading, kondisi jarum, dan area looper.",
        "Matikan mesin sebelum memeriksa jarum atau area looper.",
    ),
    (
        "Jahitan tidak rapi",
        "Hasil jahitan tidak seragam atau bentuk jahitan tidak sesuai.",
        "Tension benang tidak seimbang, feeding material tidak stabil, atau kondisi jarum dan looper tidak optimal.",
        "Periksa tension, feeding material, kondisi jarum dan looper, kemudian lakukan uji jahit.",
        "Pastikan mesin berhenti sebelum melakukan penyetelan pada area jahit.",
    ),
    (
        "Jarum patah",
        "Jarum patah saat proses menjahit atau setelah mengenai bagian mesin.",
        "Jarum salah pasang atau tidak sesuai material, atau terdapat gangguan pada area jarum.",
        "Ganti jarum yang sesuai dan periksa pemasangan serta area jarum sebelum mesin dijalankan.",
        "Matikan mesin dan putuskan sumber listrik sebelum mengganti jarum atau melakukan pemeriksaan.",
    ),
    (
        "Benang looper putus / jahitan tidak mengunci",
        "Benang looper putus atau hasil jahitan tidak membentuk kuncian dengan baik.",
        "Threading looper tidak benar, tension tidak sesuai, atau kondisi looper dan jalur benang perlu diperiksa.",
        "Periksa threading looper, tension, kondisi looper, dan jalur benang.",
        "Matikan mesin sebelum threading atau memeriksa area looper.",
    ),
]


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Safety check: semua model harus masih 0 troubleshooting.
    for machine_id, model in DATA.items():
        cur.execute(
            "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
            (machine_id,),
        )
        jumlah = cur.fetchone()[0]

        if jumlah != 0:
            print(f"STOP: {model} sudah memiliki {jumlah} troubleshooting.")
            print("Tidak ada data yang dimasukkan.")
            conn.close()
            return

    # Insert 5 troubleshooting per model.
    for machine_id, model in DATA.items():
        source = f"Prosedur troubleshooting umum YAMATO {model}"

        for problem, symptoms, cause, solution, safety in PROBLEMS:
            cur.execute(
                """
                INSERT INTO troubleshooting
                (machine_id, problem, symptoms, possible_cause,
                 solution, safety_notes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    machine_id,
                    problem,
                    symptoms,
                    cause,
                    solution,
                    safety,
                    source,
                ),
            )

    conn.commit()

    print("\nHASIL YAMATO BATCH 2:")
    for machine_id, model in DATA.items():
        cur.execute(
            "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
            (machine_id,),
        )
        jumlah = cur.fetchone()[0]
        print(f"{machine_id} | {model} | {jumlah} troubleshooting")

    conn.close()


if __name__ == "__main__":
    main()
