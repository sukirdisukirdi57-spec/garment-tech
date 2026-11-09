import csv
import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
CSV_FILE = Path(
    "tools/he800c_audit/staging/"
    "he800c_troubleshooting_revision_candidates.csv"
)
MACHINE_ID = 102
EXPECTED_IDS = {672, 674, 675}

if not DB.is_file() or not CSV_FILE.is_file():
    raise SystemExit("GAGAL: database atau CSV kandidat tidak ditemukan.")

with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
    candidates = list(csv.DictReader(f))

try:
    ids = [int(r["existing_id"]) for r in candidates]
except (KeyError, ValueError) as e:
    raise SystemExit(f"GAGAL: struktur CSV tidak sesuai: {e}")

if len(ids) != 3 or set(ids) != EXPECTED_IDS:
    raise SystemExit(
        f"GAGAL: kandidat harus tepat ID {sorted(EXPECTED_IDS)}; "
        f"ditemukan {ids}"
    )

con = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SystemExit(f"GAGAL: integritas database: {integrity}")

    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=?",
        (MACHINE_ID,)
    ).fetchone()

    if machine is None or machine["model"] != "HE-800C":
        raise SystemExit("GAGAL: identitas mesin tidak sesuai.")

    print("=== SIMULASI READ-ONLY: HE-800C ===")
    print("Database:", DB)
    print("Mesin:", dict(machine))
    print("Integritas:", integrity)
    print("Tidak ada perubahan database.")

    for r in sorted(candidates, key=lambda x: int(x["existing_id"])):
        row_id = int(r["existing_id"])

        if int(r["machine_id"]) != MACHINE_ID:
            raise SystemExit(f"GAGAL: machine_id salah untuk ID {row_id}.")

        old = con.execute("""
            SELECT id, machine_id, problem, symptoms, possible_cause,
                   solution, safety_notes, source
            FROM troubleshooting
            WHERE id=? AND machine_id=?
        """, (row_id, MACHINE_ID)).fetchone()

        if old is None:
            raise SystemExit(f"GAGAL: ID {row_id} tidak ditemukan.")

        if r["status"].strip() != "KANDIDAT BELUM DISETUJUI":
            raise SystemExit(
                f"GAGAL: status ID {row_id} berubah: {r['status']}"
            )

        new_solution = (
            "Tindakan operator:\n" + r["operator_actions"].strip()
            + "\n\nTindakan teknisi berkualifikasi:\n"
            + r["technician_actions"].strip()
        )

        proposed = {
            "problem": r["proposed_title"].strip(),
            "symptoms": r["symptoms"].strip(),
            "possible_cause": r["possible_causes"].strip(),
            "solution": new_solution,
            "safety_notes": (
                "Matikan sakelar dan cabut kabel daya sebelum pemeriksaan. "
                "Pekerjaan atau penyetelan bertanda * pada manual hanya "
                "untuk teknisi berkualifikasi."
            ),
            "source": r["source"].strip(),
        }

        print("\n" + "=" * 72)
        print(
            f"ID {row_id} | {old['problem']} -> {proposed['problem']}"
        )
        print(
            f"Bagian manual: {r['manual_section']} | "
            f"Halaman: {r['manual_pages']}"
        )
        print("Status:", r["status"])

        for key, value in proposed.items():
            print(f"\n[{key}]")
            print("LAMA :", old[key])
            print("USUL :", value)

    print("\n" + "=" * 72)
    print("SIMULASI SELESAI — belum ada data yang diubah.")
    print("ID 671, 673, dan 676 tidak disentuh.")
finally:
    con.close()
