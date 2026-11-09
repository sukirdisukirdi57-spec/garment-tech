import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = json.loads((BASE / "migration.json").read_text(encoding="utf-8"))
DB = Path(__file__).resolve().parents[2] / "database" / "garment.db"

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

try:
    machine = conn.execute(
        "SELECT id, model FROM machines WHERE id = 52"
    ).fetchone()
    document = conn.execute(
        "SELECT id, machine_id, title FROM documents WHERE id = 219"
    ).fetchone()

    print("MODE: SIMULASI SAJA — DATABASE TIDAK DIUBAH")
    print("Database:", DB)
    print("Mesin:", dict(machine) if machine else "TIDAK DITEMUKAN")
    print("Dokumen:", dict(document) if document else "TIDAK DITEMUKAN")

    if not machine or machine["model"] != "S-6200A":
        raise SystemExit("GAGAL: identitas mesin tidak cocok.")
    if not document or document["machine_id"] != 52:
        raise SystemExit("GAGAL: dokumen sumber tidak cocok.")

    component = DATA["component"]
    existing = conn.execute(
        "SELECT id FROM components WHERE machine_id = 52 AND component_name = ?",
        (component["component_name"],),
    ).fetchone()
    print("Komponen sudah ada:", dict(existing) if existing else "Belum ada")

    relations = DATA["relations"]
    print("Baris katalog:", len(relations))
    print("ID part lokal unik:", len({r["id"] for r in relations}))
    print("Nomor part unik:", len({r["part_number"] for r in relations}))
    print("Relasi varian:", sum(
        str(r.get("relation_notes") or "").startswith("For ")
        for r in relations
    ))

    if len(relations) != 36:
        raise SystemExit("GAGAL: jumlah baris bukan 36.")
    if any(r["machine_id"] != 52 or r["source_document_id"] != 219
           for r in relations):
        raise SystemExit("GAGAL: referensi mesin/dokumen tidak konsisten.")
    if any(not r.get("part_number") or not r.get("part_name")
           for r in relations):
        raise SystemExit("GAGAL: nomor/nama part kosong.")

    print("HASIL: pemeriksaan dasar lolos.")
    print("Belum ada data yang ditambah atau diubah.")
finally:
    conn.close()
