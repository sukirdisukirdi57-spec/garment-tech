#!/usr/bin/env python3
"""Ekstrak diagram MAICA UAM-03."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/UAM03_parts_book.pdf"
OUT = Path("static/images/mechanisms/maica/uam03")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 64

# section_ref -> diagram_page (PDF page 1-based)
SECTION_TO_PAGE = {
    1: 3,   # TELAO
    2: 6,   # IMPILATORE
    3: 8,   # SCARICATORE
    4: 9,   # FERMA TESSUTO
    5: 11,  # ASSE X-Y TAGLIO
    6: 13,  # CROCHET
    7: 15,  # ASSE X-Y CUCITO
    8: 17,  # TESTA A CUCIRE
    9: 19,  # TRAVE
    10: 21, # PARTI ELETTRICHE
    11: 23, # LASER
    12: 25, # TAGLIERINA
    13: 27, # CARTER
    14: 29, # QUADRO ELETTRICO
    15: 31, # DIME CUCITO POLSO
    16: 32, # DIME TAGLIO POLSO
    17: 33, # DIME CUCITURA COLLO
    18: 34, # DIME TAGLIO COLLO
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

conn = sqlite3.connect(DB)
cur = conn.cursor()

for sec_ref, page in SECTION_TO_PAGE.items():
    pdf_idx = page - 1  # 0-based
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] section {sec_ref} page {page}")
        continue
    pix = doc[pdf_idx].get_pixmap(matrix=mat)
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    path = f"images/mechanisms/maica/uam03/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=?""",
                (path, MID, sec_ref))
    print(f"[OK] section {sec_ref:>2} -> page {page:>2} -> {out.name}")

doc.close()
conn.commit()

cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path terisi: {cur.fetchone()[0]}/19")

# Verifikasi file
missing = 0
for page in SECTION_TO_PAGE.values():
    f = Path("static") / f"images/mechanisms/maica/uam03/pdf-page-{page}.jpg"
    if not f.exists():
        print(f"  MISSING: {f}")
        missing += 1
print("✅ Semua file ada" if missing == 0 else f"❌ {missing} file hilang")
conn.close()
