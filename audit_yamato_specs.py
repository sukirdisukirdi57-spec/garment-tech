import csv
import sqlite3
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

DB = Path("database/garment.db").resolve()
OUT = Path("audit_yamato_specs_from_official_pages.csv")

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = []
        self.in_title = False
        self.tables = []
        self.depth = 0
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        elif tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table = []
                self.tables.append(self.table)
        elif tag == "tr" and self.depth:
            self.row = []
        elif tag in ("td", "th") and self.depth and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        value = " ".join(data.split())
        if not value:
            return
        if self.in_title:
            self.title.append(value)
        if self.cell is not None:
            self.cell.append(value)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(self.cell))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.table is not None and any(self.row):
                self.table.append(self.row)
            self.row = None
        elif tag == "table":
            self.depth = max(0, self.depth - 1)

if not DB.is_file():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
try:
    rows = con.execute("""
        SELECT m.id, m.model, d.id AS doc_id, d.source_url
        FROM machines m
        JOIN brands b ON b.id = m.brand_id
        JOIN documents d ON d.machine_id = m.id
        WHERE UPPER(b.name) = 'YAMATO'
          AND d.source_url LIKE '%yamato-sewing.com%'
          AND d.source_url LIKE '%/specifications/%'
          AND NOT EXISTS (
              SELECT 1 FROM specifications s
              WHERE s.machine_id = m.id
          )
        ORDER BY m.model, d.id
    """).fetchall()
finally:
    con.close()

targets = []
seen = set()
for row in rows:
    if row["model"] not in seen:
        seen.add(row["model"])
        targets.append(row)

print("Model YAMATO yang diperiksa:", len(targets))
records = []

for index, item in enumerate(targets, 1):
    url = item["source_url"]
    print(f'[{index}/{len(targets)}] {item["model"]} (ID {item["id"]})', flush=True)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read(3_000_000).decode(
                response.headers.get_content_charset() or "utf-8",
                errors="replace"
            )
            status = response.status
            final_url = response.geturl()

        parser = PageParser()
        parser.feed(html)
        title = " ".join(parser.title)
        count = 0

        for table_no, table in enumerate(parser.tables, 1):
            for row_no, cells in enumerate(table, 1):
                records.append({
                    "machine_id": item["id"],
                    "model": item["model"],
                    "document_id": item["doc_id"],
                    "http_status": status,
                    "page_title": title,
                    "table_no": table_no,
                    "row_no": row_no,
                    "cells": " | ".join(cells),
                    "source_url": final_url,
                })
                count += 1

        print(f"    HTTP {status}; tabel {len(parser.tables)}; baris {count}")
    except Exception as exc:
        print(f"    GAGAL: {type(exc).__name__}: {exc}")
        records.append({
            "machine_id": item["id"],
            "model": item["model"],
            "document_id": item["doc_id"],
            "http_status": "ERROR",
            "page_title": str(exc),
            "table_no": "",
            "row_no": "",
            "cells": "",
            "source_url": url,
        })

fields = [
    "machine_id", "model", "document_id", "http_status",
    "page_title", "table_no", "row_no", "cells", "source_url"
]
with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)

print("\nCSV hasil audit:", OUT.resolve())
print("Total baris hasil:", len(records))
print("Database tidak diubah.")
