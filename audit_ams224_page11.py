import sqlite3
import subprocess
import re
import sys

DB = "database/garment.db"
PDF = "assets/documents/juki/ams224en/ams224en4530r-parts.pdf"

MACHINE_ID = 46
DOCUMENT_ID = 162
PDF_PAGE = 11

TARGETS = set(range(41, 61))

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    document = con.execute("""
        SELECT source_url
        FROM documents
        WHERE id=? AND machine_id=?
    """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

    if not document:
        raise RuntimeError("Dokumen sumber tidak ditemukan.")

    raw = subprocess.check_output([
        "pdftotext", "-f", str(PDF_PAGE),
        "-l", str(PDF_PAGE), "-layout", PDF, "-"
    ], stderr=subprocess.DEVNULL, text=True)

    parsed = {}

    pattern = re.compile(
        r"^\s*(\d+)\s+(\S+)\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    for line in raw.splitlines():
        match = pattern.match(line)
        if not match:
            continue

        ref = int(match.group(1))
        if ref not in TARGETS:
            continue

        parsed[ref] = {
            "part_number": match.group(2),
            "part_name": match.group(3).strip(),
            "quantity_raw": match.group(4),
            "original": line.rstrip(),
            "marker": ""
        }

    print("=== PEMERIKSAAN PDF PAGE 11 ===")
    print("Baris REF ditemukan:", len(parsed))

    if set(parsed) != TARGETS:
        missing = sorted(TARGETS - set(parsed))
        raise RuntimeError(f"REF belum lengkap: {missing}")

    print("\n=== VALIDASI TERHADAP PARTS ===")

    for ref in sorted(TARGETS):
        item = parsed[ref]

        rows = con.execute("""
            SELECT id, part_number, part_name, quantity_raw
            FROM parts
            WHERE machine_id=?
              AND source_document_id=?
              AND catalog_ref=?
        """, (MACHINE_ID, DOCUMENT_ID, str(ref))).fetchall()

        matches = [
            r for r in rows
            if r["part_number"] == item["part_number"]
            and r["part_name"] == item["part_name"]
            and r["quantity_raw"] == item["quantity_raw"]
        ]

        if len(matches) != 1:
            raise RuntimeError(
                f"REF {ref}: kecocokan parts harus tepat satu, "
                f"ditemukan {len(matches)}"
            )

        item["part_id"] = matches[0]["id"]
        print(
            f"OK REF {ref}: part_id={item['part_id']} "
            f"{item['part_number']} qty={item['quantity_raw']}"
        )

    existing = con.execute("""
        SELECT catalog_ref, part_number
        FROM catalog_occurrences
        WHERE machine_id=? AND pdf_page=?
    """, (MACHINE_ID, PDF_PAGE)).fetchall()

    if existing:
        raise RuntimeError(
            f"Halaman sudah memiliki {len(existing)} occurrence. "
            "Import dibatalkan agar tidak menimpa data."
        )

    print("\n=== RINGKASAN ===")
    print("Machine ID       :", MACHINE_ID)
    print("Source document  :", DOCUMENT_ID)
    print("PDF page         :", PDF_PAGE)
    print("Jumlah occurrence:", len(parsed))
    print("Marker           : kosong")
    print("Source URL       :", document["source_url"])
    print("\nPREFLIGHT BERHASIL. BELUM ADA DATA YANG DIUBAH.")

finally:
    con.close()
