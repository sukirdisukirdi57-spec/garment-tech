import csv
import os
import time
import urllib.request
from bs4 import BeautifulSoup

BASE = "https://partsbook.brother.co.jp"
OUT = "tmp/catalog-audit/s6200a_all_mechanisms_preview.csv"

mechanisms = [
    (23, "A. Machine body"),
    (24, "B. Needle bar and thread take-up mechanism"),
    (25, "C. Presser foot mechanism"),
    (26, "D. Feed mechanism"),
    (27, "E. Knee lifter mechanism"),
    (28, "F. Quick reverse mechanism"),
    (29, "G. Rotary hook mechanism"),
    (30, "H. Lubrication"),
    (31, "J. Threading mechanism"),
    (32, "K. Bobbin winder mechanism"),
    (33, "L. Thread trimmer mechanism"),
    (34, "M. Tension release mechanism"),
    (35, "N. Thread wiper mechanism (-40[] or Option parts)"),
    (36, "P1. Control box and motor mechanism"),
    (37, "P2. Control box mechanism"),
    (38, "P3. Control box mechanism"),
    (39, "Q. Quick reverse switch mechanism"),
    (40, "R. Power supply equipment mechanism"),
    (41, "Z. Accessories"),
    (42, "Wa. Warning labels"),
    (43, "Ga. Gauge parts list"),
]

headers = [
    "mechanism_id", "mechanism", "catalog_ref",
    "quantity_raw", "rm", "part_number", "part_name",
    "source_url", "diagram_url"
]

all_rows = []
errors = []

for index, (mid, name) in enumerate(mechanisms):
    url = f"{BASE}/pub/machine/detail/en/3/{mid}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            html = response.read()

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            errors.append((mid, name, "Tabel tidak ditemukan"))
            print(f"GAGAL ID {mid}: tabel tidak ditemukan")
        else:
            image_tag = soup.find(
                "img", src=lambda x: x and ".svg" in x.lower()
            )
            diagram = ""
            if image_tag:
                diagram = urllib.parse.urljoin(url, image_tag.get("src", ""))

            count = 0
            for tr in table.find_all("tr"):
                cells = [
                    c.get_text(" ", strip=True)
                    for c in tr.find_all(["th", "td"])
                ]
                if len(cells) < 5 or cells[0] in ("REF-NO", "QTY"):
                    continue

                if mid in (42, 43):
                    # Halaman ini memakai kolom QTY, RM, CODE, NAME OF PARTS.
                    # Tidak ada kolom REF-NO pada sumber.
                    all_rows.append([
                        str(mid), name, "", cells[0],
                        cells[1], cells[2], cells[3], url, diagram
                    ])
                else:
                    all_rows.append([
                        str(mid), name, cells[0], cells[1],
                        cells[2], cells[3], cells[4], url, diagram
                    ])
                count += 1

            print(f"ID {mid} | {name} | {count} baris")

    except Exception as exc:
        errors.append((mid, name, str(exc)))
        print(f"GAGAL ID {mid}: {exc}")

    if index < len(mechanisms) - 1:
        time.sleep(1)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(all_rows)

print("\n===== RINGKASAN PRATINJAU =====")
print("Mekanisme terdaftar:", len(mechanisms))
print("Total baris part:", len(all_rows))
print("Mekanisme gagal:", len(errors))
print("CSV:", OUT)
print("Database tidak diubah.")

if errors:
    print("\n===== MEKANISME YANG PERLU DIPERIKSA ULANG =====")
    for error in errors:
        print(error)
