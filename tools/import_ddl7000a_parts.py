import re
import sqlite3

TXT = "/sdcard/Download/ddl7000a_partslist.txt"
DB = "database/garment.db"

MACHINE_ID = 4
SOURCE_DOCUMENT_ID = 14

# =========================
# BACA TXT HASIL PDF
# =========================

with open(TXT, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

# Cari awal Numerical Index
index_start = next(
    i for i, line in enumerate(lines)
    if line.strip() == "NUMERICAL INDEX OF PARTS"
)

# =========================
# BACA NUMERICAL INDEX
# PART NUMBER -> (PAGE, REF)
# =========================

index = {}

for line in lines[index_start + 4:]:
    if line.strip() == "NUMERICAL INDEX OF PARTS":
        continue

    matches = re.findall(
        r"([A-Z0-9][A-Z0-9._/-]*-[A-Z0-9._/-]+)\s+(\d+)\s+(\d+)",
        line
    )

    for part, page, ref in matches:
        index.setdefault(part, []).append(
            (int(page), int(ref))
        )

# =========================
# BACA BARIS DIAGRAM
# =========================

part_pattern = re.compile(
    r"^\s*(\d+)\s+"
    r"(?:(?:☆\s*)?(?:#\d+\s*)?)"
    r"([A-Z0-9][A-Z0-9._/-]*-[A-Z0-9._/-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+\)?)\s*$"
)

results = []

for line in lines[:index_start]:
    m = part_pattern.match(line)

    if not m:
        continue

    ref = int(m.group(1))
    part = m.group(2)
    name = m.group(3).strip()
    qty_raw = m.group(4)

    matches = [
        page
        for page, idx_ref in index.get(part, [])
        if idx_ref == ref
    ]

    if not matches:
        raise RuntimeError(
            f"PAGE tidak ditemukan: REF={ref}, PART={part}"
        )

    page = matches[0]

    qty = int(qty_raw.replace("(", "").replace(")", ""))

    results.append(
        {
            "ref": ref,
            "part_number": part,
            "part_name": name,
            "quantity": qty,
            "quantity_raw": qty_raw,
            "page": page,
        }
    )

print(f"Data hasil parsing: {len(results)} baris")

if len(results) != 507:
    raise RuntimeError(
        f"Jumlah data tidak sesuai. Ditemukan {len(results)}, "
        f"seharusnya 507."
    )

# =========================
# IMPORT KE SQLITE
# =========================

conn = sqlite3.connect(DB)

try:
    cur = conn.cursor()

    # Pastikan machine dan document memang ada
    cur.execute(
        "SELECT id, model FROM machines WHERE id = ?",
        (MACHINE_ID,)
    )
    machine = cur.fetchone()

    if not machine:
        raise RuntimeError(
            f"Machine ID {MACHINE_ID} tidak ditemukan."
        )

    cur.execute(
        "SELECT id, title FROM documents WHERE id = ?",
        (SOURCE_DOCUMENT_ID,)
    )
    document = cur.fetchone()

    if not document:
        raise RuntimeError(
            f"Document ID {SOURCE_DOCUMENT_ID} tidak ditemukan."
        )

    print(
        f"Machine: {machine[0]} - {machine[1]}"
    )
    print(
        f"Document: {document[0]} - {document[1]}"
    )

    # =========================
    # TRANSAKSI
    # =========================

    conn.execute("BEGIN")

    # Hapus hanya data Parts List lama dari dokumen ini
    cur.execute(
        """
        DELETE FROM parts
        WHERE machine_id = ?
          AND source_document_id = ?
        """,
        (MACHINE_ID, SOURCE_DOCUMENT_ID)
    )

    deleted = cur.rowcount

    # Masukkan seluruh hasil parsing
    for item in results:
        cur.execute(
            """
            INSERT INTO parts (
                machine_id,
                source_document_id,
                part_number,
                part_name,
                quantity,
                catalog_ref,
                diagram_page,
                quantity_raw
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                MACHINE_ID,
                SOURCE_DOCUMENT_ID,
                item["part_number"],
                item["part_name"],
                item["quantity"],
                item["ref"],
                item["page"],
                item["quantity_raw"],
            )
        )

    conn.commit()

    print()
    print("IMPORT BERHASIL")
    print(f"Data lama dihapus : {deleted}")
    print(f"Data baru masuk   : {len(results)}")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
