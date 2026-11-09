#!/usr/bin/env python3
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db").resolve()

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

EXPECTED_MODELS = {
    **{i: "E256" for i in range(1279, 1284)},
    **{i: "EX5400" for i in range(1284, 1289)},
    **{i: "TML326" for i in range(1289, 1294)},
}

FIELDS = ("symptoms", "possible_cause", "solution", "safety_notes")

def stop(message):
    raise RuntimeError(message)

def read_rows(con):
    return con.execute("""
        SELECT t.id, m.model, t.problem, t.symptoms,
               t.possible_cause, t.solution, t.safety_notes, t.source
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        WHERE t.id BETWEEN 1279 AND 1293
        ORDER BY t.id
    """).fetchall()

def validate(rows):
    if len(rows) != 15:
        stop(f"Jumlah baris harus 15, ditemukan {len(rows)}.")
    for r in rows:
        if EXPECTED_MODELS.get(r["id"]) != r["model"]:
            stop(f"ID {r['id']}: model tidak sesuai.")
        if r["problem"] not in SYMPTOMS:
            stop(f"ID {r['id']}: problem tidak dikenali.")
        if not r["source"] or not r["source"].strip():
            stop(f"ID {r['id']}: source kosong.")

def proposal(r):
    problem = r["problem"]
    values = {
        "symptoms": SYMPTOMS[problem],
        "possible_cause": r["symptoms"],
        "solution": r["possible_cause"],
        "safety_notes": r["safety_notes"],
    }

    if problem == "Jahitan loncat":
        values["safety_notes"] = (
            "Matikan mesin dan lepaskan sumber tenaga sebelum "
            "memeriksa jarum, looper, atau sinkronisasi mekanisme."
        )

    elif problem == "Jahitan tidak rapi atau tidak stabil":
        values["solution"] = (
            values["solution"].rstrip()
            + " Lakukan penyetelan secara bertahap."
        )
        extra = "Jangan menyentuh bagian bergerak saat mesin beroperasi."
        if extra.lower() not in values["safety_notes"].lower():
            values["safety_notes"] = (
                values["safety_notes"].rstrip() + " " + extra
            )

    for field, value in values.items():
        if not isinstance(value, str) or not value.strip():
            stop(f"ID {r['id']}: usulan {field} kosong.")
    return values

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Terapkan perubahan; tanpa opsi ini hanya simulasi."
    )
    args = parser.parse_args()

    if not DB.exists():
        stop(f"Database tidak ditemukan: {DB}")

    con = sqlite3.connect(
        str(DB) if args.apply else f"file:{DB}?mode=ro",
        uri=not args.apply,
        timeout=30,
    )
    con.row_factory = sqlite3.Row

    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            stop(f"Integritas awal gagal: {integrity}")

        rows = read_rows(con)
        validate(rows)

        # Simpan seluruh hasil yang diharapkan sebelum perubahan.
        expected = {
            r["id"]: {
                **proposal(r),
                "source": r["source"],
                "model": r["model"],
                "problem": r["problem"],
            }
            for r in rows
        }

        print("MODE:", "APPLY" if args.apply else "READ ONLY — SIMULASI")
        print("Database:", DB)
        print("Baris tervalidasi:", len(rows))
        print("Integritas awal:", integrity)

        for r in rows:
            p = expected[r["id"]]
            print(f"\nID {r['id']} | {r['model']} | {r['problem']}")
            for field in FIELDS:
                print(f"  {field}: {p[field]}")
            print("  source dipertahankan:", p["source"])

        if not args.apply:
            print("\nSIMULASI SELESAI — database tidak diubah.")
            return

        # Backup konsisten sebelum transaksi.
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = DB.parent / (
            f"garment.db.backup-before-pegasus-troubleshooting-{stamp}"
        )
        backup_con = sqlite3.connect(str(backup))
        try:
            con.backup(backup_con)
        finally:
            backup_con.close()

        if not backup.exists() or backup.stat().st_size == 0:
            stop("Backup tidak berhasil dibuat.")

        print("\nBackup:", backup)
        print("Ukuran backup:", backup.stat().st_size, "bytes")

        con.execute("BEGIN IMMEDIATE")
        current = read_rows(con)
        validate(current)
        if len(current) != len(expected):
            stop("Data berubah sebelum transaksi.")

        for r in current:
            p = expected[r["id"]]
            con.execute("""
                UPDATE troubleshooting
                SET symptoms = ?,
                    possible_cause = ?,
                    solution = ?,
                    safety_notes = ?
                WHERE id = ?
            """, tuple(p[f] for f in FIELDS) + (r["id"],))

        # Bandingkan SEMUA kolom hasil dengan usulan yang tersimpan.
        after = read_rows(con)
        if len(after) != 15:
            stop("Jumlah baris pascamigrasi tidak sesuai.")

        for r in after:
            p = expected[r["id"]]
            for field in FIELDS:
                if r[field] != p[field]:
                    stop(f"Verifikasi {field} gagal pada ID {r['id']}.")
            if r["source"] != p["source"]:
                stop(f"Source berubah pada ID {r['id']}.")
            if r["model"] != p["model"] or r["problem"] != p["problem"]:
                stop(f"Identitas record berubah pada ID {r['id']}.")

        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            stop(f"Integritas sebelum commit gagal: {integrity}")

        con.commit()

        # Pemeriksaan integritas akhir setelah commit.
        final_integrity = con.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        if final_integrity != "ok":
            stop(
                "Integritas setelah commit gagal. "
                f"Backup tersedia di {backup}"
            )

        print("\nMIGRASI BERHASIL")
        print("Baris diperbarui:", len(after))
        print("Semua kolom diverifikasi: OK")
        print("Source dipertahankan: OK")
        print("Integritas akhir:", final_integrity)
        print("Backup:", backup)

    except Exception as exc:
        if args.apply and con.in_transaction:
            con.rollback()
            print("ROLLBACK: transaksi dibatalkan.")
        raise
    finally:
        con.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nGAGAL:", exc)
        raise SystemExit(1)
