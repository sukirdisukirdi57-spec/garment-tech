import sqlite3
from pathlib import Path

DB = Path("database/garment.db").resolve()
MODELS = ("E256", "EX5400", "TML326")

SYMPTOMS = {
    "Benang sering putus":
        "Putusnya benang terjadi berulang saat mesin dijalankan.",
    "Jahitan loncat":
        "Sebagian jahitan tidak terbentuk dengan sempurna.",
    "Jahitan tidak rapi atau tidak stabil":
        "Kerapatan dan bentuk jahitan berubah-ubah selama proses menjahit.",
    "Kain mengerut":
        "Permukaan kain berkerut atau tertarik setelah proses menjahit.",
    "Kain tidak terumpan dengan stabil":
        "Kain bergerak tidak stabil atau laju pengumpanan tidak konsisten.",
}

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

try:
    print("DATABASE:", DB)
    print("MODE: SIMULASI V2 — READ ONLY")
    print("Integritas awal:", con.execute("PRAGMA integrity_check").fetchone()[0])

    machines = con.execute(
        "SELECT id, model FROM machines WHERE model IN (?, ?, ?)",
        MODELS,
    ).fetchall()

    if {r["model"] for r in machines} != set(MODELS):
        raise RuntimeError("Model target tidak lengkap.")

    proposals = []

    for machine in machines:
        model = machine["model"]

        rows = con.execute(
            """
            SELECT id, problem, symptoms, possible_cause,
                   solution, safety_notes
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
            """,
            (machine["id"],),
        ).fetchall()

        selected = [r for r in rows if r["problem"] in SYMPTOMS]

        if len(selected) != 5:
            raise RuntimeError(
                f"{model}: ditemukan {len(selected)} dari 5 masalah target."
            )

        for r in selected:
            # Kolom penyebab dan solusi dipertahankan dari baris aslinya.
            cause = r["symptoms"]
            solution = r["possible_cause"]
            old_solution = (r["solution"] or "").strip()
            safety = (r["safety_notes"] or "").strip()

            if r["problem"] == "Jahitan loncat":
                safety = (
                    "Matikan mesin dan lepaskan sumber tenaga sebelum "
                    "memeriksa jarum, looper, atau sinkronisasi mekanisme."
                )

            elif r["problem"] == "Jahitan tidak rapi atau tidak stabil":
                extra = "Jangan menyentuh bagian bergerak saat mesin beroperasi."
                if extra.lower() not in safety.lower():
                    safety = f"{safety} {extra}".strip()

                # Pertahankan arahan penyetelan bertahap sebagai langkah kerja.
                extra_solution = "Lakukan penyetelan secara bertahap."
                if extra_solution.lower() not in solution.lower():
                    solution = f"{solution} {extra_solution}".strip()

            proposals.append({
                "model": model,
                "id": r["id"],
                "problem": r["problem"],
                "old": dict(r),
                "symptoms": SYMPTOMS[r["problem"]],
                "possible_cause": cause,
                "solution": solution,
                "safety_notes": safety,
                "old_solution": old_solution,
            })

    if len(proposals) != 15:
        raise RuntimeError(f"Total target bukan 15: {len(proposals)}")

    for p in sorted(proposals, key=lambda x: x["id"]):
        print("\n" + "=" * 72)
        print(f"{p['model']} | ID {p['id']} | {p['problem']}")
        print("GEJALA       :", p["symptoms"])
        print("PENYEBAB     :", p["possible_cause"])
        print("SOLUSI       :", p["solution"])
        print("KESELAMATAN  :", p["safety_notes"])
        print("CATATAN LAMA :", p["old_solution"])

    print("\n" + "=" * 72)
    print("TOTAL PROPOSAL:", len(proposals))
    print("Database tidak diubah.")
    print("Integritas akhir:", con.execute("PRAGMA integrity_check").fetchone()[0])

finally:
    con.close()
