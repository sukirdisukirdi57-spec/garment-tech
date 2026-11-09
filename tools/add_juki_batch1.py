import sqlite3

DB = "database/garment.db"

DATA = {
    28: "MF-7500-C11",
    29: "MF-7500-E11",
    30: "MF-7900-U11",
}

PROBLEMS = [
    (
        "Jarum patah saat proses jahit",
        "Jarum patah ketika mesin sedang menjahit.",
        "Jarum bengkok, salah pasang, tidak sesuai dengan material, atau terdapat gangguan pada area jarum.",
        "Matikan mesin, periksa penyebab gangguan, kemudian ganti jarum dengan tipe dan ukuran yang sesuai.",
        "Matikan mesin dan putuskan sumber listrik sebelum mengganti jarum atau memeriksa area jarum.",
    ),
    (
        "Jahitan mudah terurai / penguncian benang tidak sempurna",
        "Jahitan mudah terurai atau hasil penguncian benang tidak sempurna.",
        "Threading tidak benar, tension tidak sesuai, atau jalur benang dan area looper perlu diperiksa.",
        "Periksa threading, tension, jalur benang, serta kondisi looper dan lakukan uji jahit.",
        "Matikan mesin sebelum threading atau memeriksa area looper dan jalur benang.",
    ),
]


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Safety check: setiap mesin harus tepat 6 troubleshooting.
    for machine_id, model in DATA.items():
        cur.execute(
            "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
            (machine_id,),
        )
        jumlah = cur.fetchone()[0]

        if jumlah != 6:
            print(
                f"STOP: {model} memiliki {jumlah} troubleshooting, "
                "bukan 6."
            )
            print("Tidak ada data yang dimasukkan.")
            conn.close()
            return

    # Insert 2 troubleshooting per mesin.
    for machine_id, model in DATA.items():
        source = f"Prosedur troubleshooting umum JUKI {model}"

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

    print("\nHASIL JUKI BATCH 1:")
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
