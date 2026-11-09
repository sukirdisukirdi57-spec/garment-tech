import argparse
import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
CSV = Path("tmp/bas311hn/h_staging_audited_v1.csv")
BACKUP_DIR = Path("backups")

MACHINE_ID = 227
DOCUMENT_ID = 582
PAGE = 37
CATEGORY = "H - Bobbin winder mechanism"
SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/-/media/ap2/ism/"
    "pdf/parts-book-download/bas311hn_326h_pb.pdf?rev=-1"
)


def load_rows():
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 33, f"Harus 33 baris, ditemukan {len(rows)}"
    assert len({r["catalog_ref"] for r in rows}) == 33, \
        "Ada catalog_ref duplikat"
    assert [int(r["catalog_ref"]) for r in rows] == list(range(1, 34)), \
        "Referensi harus berurutan 1–33"

    for r in rows:
        assert r["status"] == "VERIFIED", \
            f"Status belum VERIFIED pada ref {r['catalog_ref']}"
        assert r["diagram_page"] == str(PAGE), \
            f"Halaman salah pada ref {r['catalog_ref']}"
        assert r["part_number"].strip() and r["part_name"].strip(), \
            f"Kode/nama kosong pada ref {r['catalog_ref']}"
        assert r["quantity_raw"].strip().isdigit(), \
            f"Qty tidak valid pada ref {r['catalog_ref']}"

    return rows


def validate_database(conn):
    machine = conn.execute(
        "SELECT id, model FROM machines WHERE id = ?", (MACHINE_ID,)
    ).fetchone()
    assert machine, f"Mesin ID {MACHINE_ID} tidak ditemukan"
    assert "BAS-311HN-03S" in str(machine["model"]).upper(), \
        f"Model mesin tidak cocok: {machine['model']}"

    doc = conn.execute(
        "SELECT id, source_url FROM documents WHERE id = ?", (DOCUMENT_ID,)
    ).fetchone()
    assert doc, f"Dokumen ID {DOCUMENT_ID} tidak ditemukan"
    assert doc["source_url"] == SOURCE_URL, \
        "URL dokumen berbeda dari URL katalog yang diharapkan"

    existing = conn.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id = ? AND diagram_page = ?
    """, (MACHINE_ID, PAGE)).fetchone()[0]
    assert existing == 0, \
        f"Halaman {PAGE} sudah memiliki {existing} parts"

    category = conn.execute("""
        SELECT id FROM components
        WHERE machine_id = ? AND component_name = ?
    """, (MACHINE_ID, CATEGORY)).fetchone()
    assert not category, f"Kategori sudah ada: {CATEGORY}"

    return machine["model"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Simpan perubahan ke database; tanpa flag ini hanya dry-run"
    )
    args = parser.parse_args()

    assert DB.exists(), f"Database tidak ditemukan: {DB}"
    assert CSV.exists(), f"Staging tidak ditemukan: {CSV}"

    rows = load_rows()
    print("VALIDASI STAGING: LULUS")
    print("Jumlah baris:", len(rows))
    print("Status:", "33 VERIFIED")
    print("Halaman:", PAGE)
    print("Kategori:", CATEGORY)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        model = validate_database(conn)
        print("Model:", model)
        print("VALIDASI DATABASE: LULUS")
        print("Parts lama pada halaman 37: 0")
        print("Kategori H duplikat: TIDAK")

        if not args.apply:
            print("\nDRY-RUN BERHASIL — database tidak diubah.")
            print("Rencana: 1 kategori, 33 parts, 33 relasi.")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / (
            "garment-before-bas311hn-page37-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        shutil.copy2(DB, backup)
        print("Cadangan:", backup)

        try:
            conn.execute("BEGIN")
            cur = conn.execute("""
                INSERT INTO components (machine_id, component_name, notes)
                VALUES (?, ?, ?)
            """, (
                MACHINE_ID,
                CATEGORY,
                "Bagian H - Bobbin winder mechanism, katalog resmi "
                "Brother BAS-311HN/326H, halaman cetak 37."
            ))
            component_id = cur.lastrowid

            for r in rows:
                cur = conn.execute("""
                    INSERT INTO parts (
                        machine_id, source_document_id, part_number,
                        part_name, quantity, catalog_ref, diagram_page,
                        note, source_url, notes, quantity_raw
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID,
                    DOCUMENT_ID,
                    r["part_number"].strip(),
                    r["part_name"].strip(),
                    int(r["quantity_raw"]),
                    int(r["catalog_ref"]),
                    PAGE,
                    r.get("audit_note", ""),
                    SOURCE_URL,
                    r.get("audit_note", ""),
                    r["quantity_raw"].strip(),
                ))
                part_id = cur.lastrowid

                conn.execute("""
                    INSERT INTO component_parts (component_id, part_id)
                    VALUES (?, ?)
                """, (component_id, part_id))

            conn.commit()
            print("IMPOR BERHASIL")
            print("Component ID:", component_id)
            print("Parts:", len(rows))
            print("Relasi:", len(rows))
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
