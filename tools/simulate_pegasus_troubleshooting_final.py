import sqlite3
from pathlib import Path

DB = Path("database/garment.db").resolve()
TARGET_MODELS = ("E256", "EX5400", "TML326")
PROBLEMS = (
    "Benang sering putus",
    "Jahitan loncat",
    "Jahitan tidak rapi atau tidak stabil",
    "Kain mengerut",
    "Kain tidak terumpan dengan stabil",
)

# Catatan berikut mempertahankan instruksi keselamatan yang relevan
# tanpa menambahkan kalimat yang hanya mengulang instruksi lama.
SAFETY_BY_PROBLEM = {
    "Benang sering putus":
        "Matikan mesin sebelum memeriksa jalur benang, jarum, looper, atau melakukan penyetelan.",

    "Jahitan loncat":
        "Matikan mesin dan lepaskan sumber tenaga sebelum memeriksa jarum, looper, atau sinkronisasi mekanisme.",

    "Jahitan tidak rapi atau tidak stabil":
        "Matikan mesin sebelum membersihkan area pembentukan jahitan atau melakukan penyetelan. Jangan menyentuh bagian bergerak saat mesin beroperasi.",

    "Kain mengerut":
        "Matikan mesin sebelum melakukan penyetelan pada tegangan benang, tekanan sepatu, atau mekanisme feed.",

    "Kain tidak terumpan dengan stabil":
        "Matikan mesin sebelum membersihkan atau memeriksa feed dog, sepatu, dan mekanisme pengumpanan.",
}

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

try:
    print("DATABASE:", DB)
    print("MODE: SIMULASI FINAL — READ ONLY")
    print("Integritas awal:", con.execute("PRAGMA integrity_check").fetchone()[0])

    # Periksa struktur tabel sebelum membuat proposal.
    cols = {
        row["name"]
        for row in con.execute("PRAGMA table_info(troubleshooting)")
    }
    required = {
        "id", "machine_id", "problem", "symptoms",
        "possible_cause", "solution", "safety_notes"
    }
    if not required.issubset(cols):
        raise RuntimeError(
            "Kolom troubleshooting tidak sesuai: "
            + ", ".join(sorted(required - cols))
        )

    machines = {
        row["model"]: row["id"]
        for row in con.execute(
            """
            SELECT model, id
            FROM machines
            WHERE model IN (?, ?, ?)
            """,
            TARGET_MODELS,
        )
    }

    if set(machines) != set(TARGET_MODELS):
        raise RuntimeError(
            f"Model target tidak lengkap. Ditemukan: {machines}"
        )

    template_machine_id = con.execute(
        "SELECT id FROM machines WHERE model = 'E22L'"
    ).fetchone()

    if not template_machine_id:
        raise RuntimeError("Model E22L tidak ditemukan sebagai pembanding.")

    template_machine_id = template_machine_id["id"]
    proposals = []

    for model in TARGET_MODELS:
        machine_id = machines[model]

        rows = con.execute(
            """
            SELECT id, problem, symptoms, possible_cause,
                   solution, safety_notes
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
            """,
            (machine_id,),
        ).fetchall()

        target_rows = [r for r in rows if r["problem"] in PROBLEMS]
        if len(target_rows) != 5:
            raise RuntimeError(
                f"{model}: seharusnya 5 masalah target, "
                f"tetapi ditemukan {len(target_rows)}."
            )

        for old in target_rows:
            template = con.execute(
                """
                SELECT symptoms, possible_cause, solution
                FROM troubleshooting
                WHERE machine_id = ? AND problem = ?
                ORDER BY id
                LIMIT 1
                """,
                (template_machine_id, old["problem"]),
            ).fetchone()

            if not template:
                raise RuntimeError(
                    f"Template E22L tidak ditemukan: {old['problem']}"
                )

            proposals.append({
                "model": model,
                "id": old["id"],
                "problem": old["problem"],
                "old_symptoms": old["symptoms"],
                "old_cause": old["possible_cause"],
                "old_solution": old["solution"],
                "old_safety": old["safety_notes"],
                "symptoms": template["symptoms"],
                "possible_cause": template["possible_cause"],
                "solution": template["solution"],
                "safety_notes": SAFETY_BY_PROBLEM[old["problem"]],
            })

    if len(proposals) != 15:
        raise RuntimeError(
            f"Jumlah proposal bukan 15: {len(proposals)}"
        )

    for p in proposals:
        print("\n" + "=" * 76)
        print(f"{p['model']} | ID {p['id']} | {p['problem']}")
        print("- SIMULASI KOLOM LAMA")
        print("symptoms      :", p["old_symptoms"])
        print("possible_cause:", p["old_cause"])
        print("solution      :", p["old_solution"])
        print("safety_notes  :", p["old_safety"])
        print("- USULAN KOLOM BARU")
        print("symptoms      :", p["symptoms"])
        print("possible_cause:", p["possible_cause"])
        print("solution      :", p["solution"])
        print("safety_notes  :", p["safety_notes"])

    print("\n" + "=" * 76)
    print("TOTAL PROPOSAL:", len(proposals))
    print("Database tidak diubah; koneksi menggunakan mode read-only.")
    print("Integritas akhir:", con.execute("PRAGMA integrity_check").fetchone()[0])

finally:
    con.close()
