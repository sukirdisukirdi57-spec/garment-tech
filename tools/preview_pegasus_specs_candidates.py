import csv
import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
OUT = Path("tools/preview_pegasus_specs_candidates.csv")

# Kandidat dari halaman resmi PEGASUS.
# Semua data masih berstatus pratinjau, bukan data yang sudah diimpor.
rows = [
    ("M922", "M922-A-02", "2 jarum; mesin double chainstitch; 6.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),

    ("M932", "M932-A-38", "2 jarum; 5 benang; 7.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M932", "M932-A-44", "2 jarum; 5 benang; 7.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M932", "M932-A-70", "2 jarum; 5 benang; 7.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M932", "M932-A-86", "2 jarum; 4 benang; 5.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),

    ("M952", "M952-A-52H", "2 jarum; 4 benang; 6.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M952", "M952-A-23B", "2 jarum; 4 benang; 6.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M952", "M952-A-16S2", "1 jarum; 3 benang; 7.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M952", "M952-A-180", "1 jarum; 3 benang; 7.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M952", "M952-A-181", "2 jarum; 4 benang; 7.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),
    ("M952", "M952-A-90", "1 jarum; 2 benang; 5.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s106"),

    ("EX3200", "EX3216-01A/222", "2 jarum; 5 benang; 7.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),
    ("EX3200", "EX3216N-01/222", "2 jarum; 5 benang; 7.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),
    ("EX3200", "EX3216N-01/232", "2 jarum; 5 benang; 7.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),

    ("EX5200", "EX5214N-01/283", "2 jarum; 4 benang; 8.000 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),
    ("EX5200", "EX5204-02/233", "1 jarum; 3 benang; 8.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),
    ("EX5200", "EX5214-03/333", "2 jarum; 4 benang; 7.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),
    ("EX5200", "EX5214-M03/333", "2 jarum; 4 benang; 7.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),
    ("EX5200", "EX5214-M03/333K", "2 jarum; 4 benang; 7.500 sti/min",
     "https://www.pegasus.co.jp/en/machine/series/s102"),

    ("W562P", "W562P-01G", "6.000 sti/min; 2 atau 3 jarum; 4 atau 5 benang",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-01G"),
    ("W562P", "W562P-01M", "6.000 sti/min; 2 jarum; 4 benang; jarak jarum 4,0 mm",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-01M"),
    ("W562P", "W562P-02G", "6.000 sti/min; 2 atau 3 jarum; 4 atau 5 benang",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-02G"),
    ("W562P", "W562P-02H", "6.000 sti/min; 2 atau 3 jarum; 4 atau 5 benang",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-02H"),
    ("W562P", "W562P-05B", "5.500 sti/min; 5.000 dengan perangkat MD; 2 atau 3 jarum; 4 atau 5 benang",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-05B"),
    ("W562P", "W562P-05M", "5.500 sti/min; 5.000 dengan perangkat MD; 2 atau 3 jarum; 4 atau 5 benang",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-05M"),
    ("W562P", "W562P-05T", "5.500 sti/min; 5.000 dengan perangkat MD; 3 jarum; 5 benang",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-05T"),
    ("W562P", "W562P-82A", "5.500 sti/min; 3 jarum; 5 benang",
     "https://www.pegasus.co.jp/en/machine/detail/series/s205/W562P-82A"),
]

con = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

try:
    output = []
    for model, variant, value, url in rows:
        machine = con.execute("""
            SELECT m.id, m.model
            FROM machines m
            JOIN brands b ON b.id = m.brand_id
            WHERE UPPER(b.name) = 'PEGASUS'
              AND UPPER(m.model) = ?
        """, (model.upper(),)).fetchone()

        if not machine:
            output.append({
                "machine_id": "",
                "model": model,
                "variant": variant,
                "specification": f"Spesifikasi varian resmi {variant}",
                "value": value,
                "notes": "PRATINJAU - verifikasi sumber sebelum impor",
                "description": f"Varian {variant}; jangan dianggap berlaku untuk seluruh seri.",
                "source_url": url,
                "status": "MODEL TIDAK DITEMUKAN",
            })
            continue

        exists = con.execute("""
            SELECT COUNT(*) FROM specifications
            WHERE machine_id = ?
              AND LOWER(specification) = LOWER(?)
        """, (machine["id"], f"Spesifikasi varian resmi {variant}")).fetchone()[0]

        output.append({
            "machine_id": machine["id"],
            "model": machine["model"],
            "variant": variant,
            "specification": f"Spesifikasi varian resmi {variant}",
            "value": value,
            "notes": "PRATINJAU - verifikasi sumber sebelum impor",
            "description": f"Varian {variant}; jangan dianggap berlaku untuk seluruh seri.",
            "source_url": url,
            "status": "SUDAH ADA - PERIKSA" if exists else "KANDIDAT - BELUM ADA",
        })

    fields = [
        "machine_id", "model", "variant", "specification", "value",
        "notes", "description", "source_url", "status"
    ]
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    print("CSV pratinjau:", OUT.resolve())
    print("Jumlah kandidat:", len(output))
    for item in output:
        print(
            f'{item["model"]:8} | {item["variant"]:20} | '
            f'{item["status"]}'
        )
    print("Integritas DB:", con.execute("PRAGMA integrity_check").fetchone()[0])
    print("Database diubah: TIDAK")
finally:
    con.close()
