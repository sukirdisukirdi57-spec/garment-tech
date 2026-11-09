import sqlite3
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
SOURCE = Path("tmp/ams221en-check")
DEST = Path("static/component_images")

# Component ID, Part ID, Part Number, Catalog Ref, PDF Page
TARGETS = [
    (406, 8641, "B1411-552-0A0", 58, 15),
    (408, 8758, "401-02213", 20, 19),
    (429, 9513, "400-00056", 19, 43),
    (431, 9537, "401-62838", 43, 43),
    (432, 9631, "400-42352", 4, 46),
]

# PDF page -> source image and destination image
IMAGES = {
    15: ("page-15-15.jpg", "ams221en_page15.jpg"),
    19: ("page-19-19.jpg", "ams221en_page19.jpg"),
    43: ("page-43-43.jpg", "ams221en_page43.jpg"),
    46: ("page-46-46.jpg", "ams221en_page46.jpg"),
}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

if not DB.is_file():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

# Pastikan seluruh gambar sumber tersedia.
for page, (src_name, dest_name) in IMAGES.items():
    src = SOURCE / src_name
    if not src.is_file():
        raise SystemExit(f"Gambar sumber tidak ditemukan: {src}")

DEST.mkdir(parents=True, exist_ok=True)

# Jangan menimpa gambar tujuan yang berbeda.
for page, (src_name, dest_name) in IMAGES.items():
    src = SOURCE / src_name
    dst = DEST / dest_name
    if dst.exists() and sha256(src) != sha256(dst):
        raise SystemExit(
            f"File tujuan sudah ada dan berbeda: {dst}\n"
            "Periksa file tersebut sebelum melanjutkan."
        )

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.execute("PRAGMA foreign_keys = ON")

try:
    # Validasi struktur tabel.
    required = {
        "components": {"id", "machine_id", "part_number",
                       "catalog_ref", "diagram_page", "image_path"},
        "parts": {"id", "machine_id", "part_number",
                  "catalog_ref", "diagram_page"},
        "catalog_occurrences": {"machine_id", "source_document_id",
                                "catalog_ref", "part_number", "pdf_page"},
        "component_parts": {"component_id", "part_id",
                            "relation_type", "notes"},
    }

    for table, expected in required.items():
        columns = {
            r["name"] for r in con.execute(
                f"PRAGMA table_info({table})"
            )
        }
        missing = expected - columns
        if missing:
            raise RuntimeError(
                f"Kolom tabel {table} tidak lengkap: {sorted(missing)}"
            )

    # Validasi kelima pasangan komponen, part, dan occurrence.
    for cid, pid, pn, ref, page in TARGETS:
        c = con.execute("""
            SELECT * FROM components
            WHERE id=? AND machine_id=45
        """, (cid,)).fetchone()

        p = con.execute("""
            SELECT * FROM parts
            WHERE id=? AND machine_id=45
        """, (pid,)).fetchone()

        if not c or not p:
            raise RuntimeError(f"Komponen/part tidak ditemukan: {cid}/{pid}")

        if c["part_number"] != pn or p["part_number"] != pn:
            raise RuntimeError(f"Part number tidak cocok: component {cid}")

        if int(c["catalog_ref"]) != ref or int(p["catalog_ref"]) != ref:
            raise RuntimeError(f"Catalog ref tidak cocok: component {cid}")

        occurrence = con.execute("""
            SELECT COUNT(*) AS n
            FROM catalog_occurrences
            WHERE machine_id=45
              AND source_document_id=159
              AND catalog_ref=?
              AND part_number=?
              AND pdf_page=?
        """, (ref, pn, page)).fetchone()["n"]

        if occurrence != 1:
            raise RuntimeError(
                f"Occurrence harus tepat satu: {pn}, REF {ref}, "
                f"page {page}; ditemukan {occurrence}"
            )

        existing = con.execute("""
            SELECT part_id
            FROM component_parts
            WHERE component_id=? AND relation_type='main-part'
        """, (cid,)).fetchall()

        if existing and any(r["part_id"] != pid for r in existing):
            raise RuntimeError(
                f"Komponen {cid} sudah memiliki main-part berbeda."
            )

    # Backup konsisten menggunakan SQLite backup API.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = Path(f"database/garment-before-ams221en-diagrams-{stamp}.db")

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()

    print(f"BACKUP: {backup}")

    copied = []
    for page, (src_name, dest_name) in IMAGES.items():
        src = SOURCE / src_name
        dst = DEST / dest_name

        if not dst.exists():
            shutil.copy2(src, dst)
            copied.append(dst)

        if not dst.is_file() or sha256(src) != sha256(dst):
            raise RuntimeError(f"Verifikasi gambar gagal: {dst}")

    # Perubahan database dalam satu transaksi.
    with con:
        for cid, pid, pn, ref, page in TARGETS:
            image_name = IMAGES[page][1]
            image_path = f"component_images/{image_name}"

            con.execute("""
                UPDATE components
                SET diagram_page=?, image_path=?
                WHERE id=? AND machine_id=45
            """, (page, image_path, cid))

            con.execute("""
                UPDATE parts
                SET diagram_page=?
                WHERE id=? AND machine_id=45
            """, (page, pid))

            relation = con.execute("""
                SELECT id FROM component_parts
                WHERE component_id=? AND part_id=?
                  AND relation_type='main-part'
            """, (cid, pid)).fetchone()

            if not relation:
                con.execute("""
                    INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, 'main-part', ?)
                """, (
                    cid, pid,
                    f"Verified from JUKI AMS-221EN Parts List, "
                    f"REF {ref}, PDF page {page}"
                ))

    # Validasi hasil.
    print("\n=== VALIDASI AKHIR ===")
    for cid, pid, pn, ref, page in TARGETS:
        r = con.execute("""
            SELECT c.id, c.component_name, c.part_number,
                   c.catalog_ref, c.diagram_page, c.image_path,
                   p.id AS part_id, p.diagram_page AS part_page,
                   cp.relation_type
            FROM components c
            JOIN parts p ON p.id=?
            JOIN component_parts cp
              ON cp.component_id=c.id AND cp.part_id=p.id
            WHERE c.id=? AND c.machine_id=45
              AND cp.relation_type='main-part'
        """, (pid, cid)).fetchone()

        if not r:
            raise RuntimeError(f"Validasi relasi gagal: component {cid}")

        if r["diagram_page"] != page or r["part_page"] != page:
            raise RuntimeError(f"Validasi halaman gagal: component {cid}")

        print(dict(r))

    print("\n=== GAMBAR ===")
    for page, (_, dest_name) in IMAGES.items():
        print(f"PDF page {page}: {DEST / dest_name}")

    print("\nPEMASANGAN BERHASIL: 5 komponen, 4 gambar.")
    print("Relasi sub-part tidak diubah.")

except Exception:
    # Hapus hanya gambar baru yang dibuat oleh skrip ini.
    for path in locals().get("copied", []):
        if path.exists():
            path.unlink()
    raise
finally:
    con.close()
