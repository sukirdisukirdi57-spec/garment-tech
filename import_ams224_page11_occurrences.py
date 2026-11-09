import sqlite3
import subprocess
import re
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
PDF = "assets/documents/juki/ams224en/ams224en4530r-parts.pdf"

MACHINE_ID = 46
DOCUMENT_ID = 162
PDF_PAGE = 11
TARGETS = set(range(41, 61))

def extract_rows():
    raw = subprocess.check_output(
        ["pdftotext", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE),
         "-layout", PDF, "-"],
        stderr=subprocess.DEVNULL,
        text=True
    )

    pattern = re.compile(
        r"^\s*(\d+)\s+(\S+)\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    parsed = {}

    for line in raw.splitlines():
        m = pattern.match(line)
        if not m:
            continue

        ref = int(m.group(1))
        if ref in TARGETS:
            if ref in parsed:
                raise RuntimeError(f"REF duplikat di PDF: {ref}")

            parsed[ref] = {
                "catalog_ref": str(ref),
                "marker": "",
                "part_number": m.group(2),
                "part_name": m.group(3).strip(),
                "quantity_raw": m.group(4),
                "catalog_line_original": line.rstrip()
            }

    if set(parsed) != TARGETS:
        raise RuntimeError(
            f"REF PDF tidak lengkap: {sorted(TARGETS - set(parsed))}"
        )

    return parsed

# 1. Baca dan validasi sumber sebelum backup/import
parsed = extract_rows()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    document = con.execute("""
        SELECT source_url FROM documents
        WHERE id=? AND machine_id=?
    """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

    if not document:
        raise RuntimeError("Dokumen sumber tidak ditemukan.")

    source_url = document["source_url"]

    for ref, item in parsed.items():
        rows = con.execute("""
            SELECT id, part_number, part_name, quantity_raw
            FROM parts
            WHERE machine_id=?
              AND source_document_id=?
              AND catalog_ref=?
        """, (MACHINE_ID, DOCUMENT_ID, ref)).fetchall()

        matches = [
            r for r in rows
            if r["part_number"] == item["part_number"]
            and r["part_name"] == item["part_name"]
            and r["quantity_raw"] == item["quantity_raw"]
        ]

        if len(matches) != 1:
            raise RuntimeError(
                f"Validasi parts gagal pada REF {ref}: "
                f"{len(matches)} kecocokan"
            )

    existing = con.execute("""
        SELECT COUNT(*) FROM catalog_occurrences
        WHERE machine_id=? AND pdf_page=?
    """, (MACHINE_ID, PDF_PAGE)).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"PDF page {PDF_PAGE} sudah memiliki {existing} occurrence. "
            "Import dihentikan."
        )

    # 2. Backup database yang konsisten
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.parent / f"garment-before-ams224-page11-{stamp}.db"

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()

    print("BACKUP:", backup)

    # 3. Insert dalam satu transaksi
    con.execute("BEGIN IMMEDIATE")

    for ref in sorted(parsed):
        item = parsed[ref]

        con.execute("""
            INSERT INTO catalog_occurrences (
                machine_id,
                source_document_id,
                pdf_page,
                catalog_ref,
                marker,
                part_number,
                part_name,
                quantity_raw,
                catalog_line_original,
                source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID,
            DOCUMENT_ID,
            PDF_PAGE,
            item["catalog_ref"],
            item["marker"],
            item["part_number"],
            item["part_name"],
            item["quantity_raw"],
            item["catalog_line_original"],
            source_url
        ))

    # 4. Verifikasi hasil sebelum commit
    saved = con.execute("""
        SELECT catalog_ref, marker, part_number, part_name,
               quantity_raw, catalog_line_original, source_url
        FROM catalog_occurrences
        WHERE machine_id=? AND source_document_id=? AND pdf_page=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, DOCUMENT_ID, PDF_PAGE)).fetchall()

    if len(saved) != 20:
        raise RuntimeError(f"Jumlah hasil tidak sesuai: {len(saved)}")

    for row in saved:
        ref = int(row["catalog_ref"])
        expected = parsed[ref]

        for field, value in expected.items():
            if row[field] != value:
                raise RuntimeError(
                    f"Verifikasi gagal REF {ref}, kolom {field}"
                )

        if row["source_url"] != source_url:
            raise RuntimeError(f"Source URL salah pada REF {ref}")

    con.commit()

    print("\n=== IMPORT BERHASIL ===")
    print("Machine ID      :", MACHINE_ID)
    print("Document ID     :", DOCUMENT_ID)
    print("PDF page        :", PDF_PAGE)
    print("Occurrence masuk:", len(saved))
    print("REF             :", saved[0]["catalog_ref"],
          "sampai", saved[-1]["catalog_ref"])
    print("Backup          :", backup)

except Exception:
    if con.in_transaction:
        con.rollback()
    raise

finally:
    con.close()
