from urllib.request import Request, urlopen
from html.parser import HTMLParser


URL = "https://www.juki.co.jp/industrial_e/products_e/apparel_e/1needle_lock_e/detail.php?cd=DDL-8700_E"


class TableParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False

        self.current_row = []
        self.current_cell = ""

        self.tables = []
        self.current_table = []

    def handle_starttag(self, tag, attrs):

        if tag == "table":
            self.in_table = True
            self.current_table = []

        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row = []

        elif tag in ("th", "td") and self.in_row:
            self.in_cell = True
            self.current_cell = ""

    def handle_data(self, data):

        if self.in_cell:
            self.current_cell += data

    def handle_endtag(self, tag):

        if tag in ("th", "td") and self.in_cell:
            value = " ".join(self.current_cell.split())

            if value:
                self.current_row.append(value)

            self.in_cell = False

        elif tag == "tr" and self.in_row:
            if self.current_row:
                self.current_table.append(self.current_row)

            self.in_row = False

        elif tag == "table" and self.in_table:
            if self.current_table:
                self.tables.append(self.current_table)

            self.current_table = []
            self.in_table = False


print("Mengambil halaman resmi JUKI...")
print(URL)
print()

request = Request(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

with urlopen(request, timeout=15) as response:
    html = response.read().decode("utf-8", errors="ignore")

print("Berhasil mengambil halaman.")
print("Ukuran HTML:", len(html), "karakter")
print()

parser = TableParser()
parser.feed(html)

print("Jumlah tabel ditemukan:", len(parser.tables))
print()

target_table = None

for table in parser.tables:

    if not table:
        continue

    header = " ".join(table[0])

    if (
        len(table[0]) >= 2
        and table[0][1].strip() == "DDL-8700"
    ):
        target_table = table
        break


if target_table is None:
    print("Tabel DDL-8700 tidak ditemukan.")
    raise SystemExit



print("=" * 70)
print("SPESIFIKASI DDL-8700 YANG AKAN DIIMPORT")
print("=" * 70)

if not target_table:
    print("Tabel DDL-8700 tidak ditemukan.")
    raise SystemExit

for row in target_table[1:]:
    if len(row) >= 2:
        specification = row[0]
        value = row[1]

        print()
        print("Specification :", specification)
        print("Value         :", value)

print()
print("=" * 70)
print("MODE PREVIEW — DATABASE BELUM DIUBAH")
print("=" * 70)

print()
print("=" * 70)
print("IMPORT KE DATABASE")
print("=" * 70)

import sqlite3

DB_PATH = "database/garment.db"
MACHINE_ID = 3

conn = sqlite3.connect(DB_PATH)

inserted = 0
skipped = 0

for row in target_table[1:]:

    if len(row) < 2:
        continue

    specification = row[0].strip()
    value = row[1].strip()

    existing = conn.execute(
        """
        SELECT id
        FROM specifications
        WHERE machine_id = ?
          AND specification = ?
        """,
        (MACHINE_ID, specification)
    ).fetchone()

    if existing:
        skipped += 1
        print("SKIP :", specification)
        continue

    conn.execute(
        """
        INSERT INTO specifications
        (
            machine_id,
            specification,
            value,
            notes
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            MACHINE_ID,
            specification,
            value,
            "Sumber resmi JUKI"
        )
    )

    inserted += 1
    print("OK   :", specification)

conn.commit()
conn.close()

print()
print("=" * 70)
print("IMPORT SELESAI")
print("Data ditambahkan :", inserted)
print("Data dilewati    :", skipped)
print("=" * 70)
