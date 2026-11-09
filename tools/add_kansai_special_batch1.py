import sqlite3

DB = "database/garment.db"

DATA = {
    184: "DFB1404PSF",
    185: "DFB1411PSF",
}

PROBLEMS = [
    (
        "Benang sering putus",
        "Benang putus saat mesin berjalan atau selama proses jahit.",
        "Jalur benang tidak benar, tegangan benang tidak sesuai, jarum bermasalah, atau terdapat hambatan pada thread path.",
        "Periksa jalur benang, tegangan, kondisi jarum, dan pastikan tidak ada bagian yang menghambat jalannya benang.",
        "Matikan mesin sebelum threading, mengganti jarum, atau memeriksa jalur benang.",
    ),
    (
        "Jahitan loncat / tidak terbentuk",
        "Sebagian jahitan tidak terbentuk atau terdapat jahitan yang terlewat.",
        "Jarum bengkok atau salah pasang, threading tidak benar, atau interaksi jarum dan looper tidak bekerja dengan baik.",
        "Periksa pemasangan dan kondisi jarum serta seluruh jalur benang. Periksa area jarum dan looper jika masalah tetap terjadi.",
        "Matikan mesin sebelum memeriksa jarum atau area looper.",
    ),
    (
        "Jahitan tidak rapi / tidak konsisten",
        "Hasil jahitan tidak seragam, jahitan terlalu longgar, terlalu ketat, atau kualitas berubah selama proses.",
        "Tegangan benang tidak seimbang, feeding material tidak stabil, atau kondisi jarum dan looper tidak optimal.",
        "Periksa tension, jalur benang, feeding material, kondisi jarum, dan area looper. Lakukan uji jahit setelah penyetelan.",
        "Pastikan mesin berhenti sebelum melakukan penyetelan pada area jahit.",
    ),
    (
        "Jarum patah",
        "Jarum patah saat proses menjahit atau setelah mengenai bagian mesin.",
        "Jarum bengkok atau salah pasang, material tidak sesuai, atau terdapat gangguan pada area jarum dan looper.",
        "Ganti jarum yang sesuai, periksa pemasangannya, dan periksa area jarum serta looper sebelum mesin dijalankan kembali.",
        "Matikan mesin dan putuskan sumber listrik sebelum mengganti jarum atau melakukan pemeriksaan.",
    ),
    (
        "Benang looper putus / jahitan tidak mengunci",
        "Benang looper putus atau hasil jahitan tidak membentuk kuncian dengan baik.",
        "Threading looper tidak benar, tegangan tidak sesuai, atau kondisi looper dan jalur benang perlu diperiksa.",
        "Periksa jalur threading looper, tension, kondisi looper, dan pastikan tidak ada hambatan pada jalur benang.",
        "Matikan mesin sebelum threading atau memeriksa area looper.",
    ),
]


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Safety check: kedua model harus belum memiliki troubleshooting.
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
        source = f"KANSAI SPECIAL {model} Instruction Manual"

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

    print("\nHASIL KANSAI SPECIAL BATCH 1:")
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
