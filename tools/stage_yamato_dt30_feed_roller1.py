import csv
from pathlib import Path

OUT = Path("tmp/yamato-dt30/feed_roller_mechanism_1_staging.csv")

# Feed Roller Mechanism (1), catalog page 7.
# Data ditranskripsi dari daftar part katalog yang sudah diperiksa.
DATA = [
    (1,  "69171", "Adjusting Screw for 69170", 1),
    (2,  "443",   "Washer for 69170", 1),
    (3,  "69170", "Feed Roller Pressing Spring", 1),
    (4,  "69168", "Feed Roller Pressing Bar Connection", 1),
    (5,  "4437",  "Screw for 69168", 1),
    (6,  "9517",  "Screw for 69168", 1),
    (7,  "334",   "Lock Nut for 9931", 1),
    (8,  "9931",  "Adjusting Screw for 69168", 1),
    (9,  "69054", "Feed Roller Connecting Link", 1),
    (10, "6038",  "Screw for 69054", 2),
    (11, "69167", "Feed Roller Pressing Bar", 1),
    (12, "69160", "Feed Roller Bracket", 1),
    (13, "4440",  "Screw for 69160", 1),
    (14, "69166", "Feed Roller Driving Gear Collar", 1),
    (15, "1457",  "Screw for 69166", 2),
    (16, "69165", "Feed Roller Drive Gear", 1),
    (17, "69164", "Feed Roller Driven Gear", 1),
    (18, "654",   "Roll Pin for 69164", 1),
    (19, "69161", "Needle Bearing for 69163", 2),
    (20, "69162", "Feed Roller", 1),
    (21, "655",   "Roll Pin for 69162", 1),
    (22, "69163", "Feed Roller Shaft", 1),
    (23, "69173", "Gear Cover (Rear)", 1),
    (24, "4404",  "Screw for 69173", 2),
    (25, "4228",  "Screw for 69172", 1),
    (26, "69172", "Gear Cover (Front)", 1),
]

fields = [
    "machine_id", "source_document_id", "part_number", "part_name",
    "quantity", "catalog_ref", "diagram_page", "source_url", "notes"
]

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for ref, part_no, name, qty in DATA:
        writer.writerow({
            "machine_id": 159,
            "source_document_id": 182,
            "part_number": part_no,
            "part_name": name,
            "quantity": qty,
            "catalog_ref": ref,
            "diagram_page": 8,
            "source_url": "https://www.yamato-sewing.com/en/product/support/dt-series/dt-30-partsbook-je/",
            "notes": "Feed Roller Mechanism (1); catalog list page 7; diagram page 8; staging only",
        })

print(f"Jumlah baris: {len(DATA)}")
print(f"Total quantity: {sum(row[3] for row in DATA)}")
print(f"CSV staging: {OUT}")
print("Database tidak diubah.")
