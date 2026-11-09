import sqlite3

DB = "database/garment.db"

DATA = {
    182: "VM1804P-382-003",
    183: "VM1804PR-382-003",
}

PROBLEMS = [
    (
        "Benang sering putus",
        "Benang putus saat proses jahit.",
        "Threading tidak benar, tension terlalu tinggi, jarum bermasalah, atau terdapat gesekan pada jalur benang.",
        "Periksa threading, tension, kondisi jarum, dan thread path.",
        "Matikan mesin sebelum threading, mengganti jarum, atau memeriksa jalur benang.",
    ),
    (
        "Jahitan loncat / tidak terbentuk",
        "Sebagian jahitan terlewat atau chainstitch tidak terbentuk.",
        "Jarum bengkok atau salah pasang, threading tidak tepat, atau area pembentukan stitch perlu diperiksa.",
        "Periksa jarum, threading, serta area jarum dan looper.",
        "Matikan mesin sebelum memeriksa jarum atau area pembentukan jahitan.",
    ),
    (
        "Jahitan tidak rapi",
        "Jahitan tidak seragam atau hasil seam tidak stabil.",
        "Tension tidak seimbang, feeding material tidak stabil, atau kondisi jarum dan looper kurang optimal.",
        "Periksa tension, feeding, kondisi jarum dan looper, kemudian lakukan uji jahit.",
        "Pastikan mesin berhenti sebelum melakukan penyetelan pada area jahit.",
    ),
    (
        "Jarum patah",
        "Jarum patah saat proses menjahit.",
        "Jarum salah pasang atau tidak sesuai material, atau terdapat gangguan pada area jarum.",
        "Ganti jarum yang sesuai dan periksa pemasangan serta area jarum sebelum mesin dijalankan.",
        "Matikan mesin dan putuskan sumber listrik sebelum mengganti jarum atau melakukan pemeriksaan.",
    ),
    (
        "Jahitan mudah terurai / tidak mengunci",
        "Loop chainstitch tidak terbentuk dengan baik atau jahitan mudah terurai.",
        "Threading tidak benar, tension tidak sesuai, atau kondisi looper dan jalur benang perlu diperiksa.",
        "Periksa threading, tension, kondisi looper, dan jalur benang.",
        "Matikan mesin sebelum threading atau memeriksa area looper.",
    ),
]


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Safety check: kedua model harus masih 0 troubleshooting.
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

    print("\nHASIL YAMATO BATCH 12:")
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
