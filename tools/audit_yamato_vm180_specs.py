import csv
import sqlite3
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

DB = Path("database/garment.db")
OUT = Path("audit_yamato_vm180_specs.csv")
URL = "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/"

class SpecTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.table_depth = 0
        self.in_row = False
        self.in_cell = False
        self.in_anchor = False
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table" and "spec-list" in attrs.get("class", "").split():
            self.in_table = True
            self.table_depth = 1
            return
        if not self.in_table:
            return
        if tag == "table":
            self.table_depth += 1
        elif tag == "tr":
            self.in_row = True
            self.row = []
        elif tag in ("td", "th") and self.in_row:
            self.in_cell = True
            self.cell = {"text": [], "anchor": "", "href": ""}
            self.row.append(self.cell)
        elif tag == "a" and self.in_cell:
            self.in_anchor = True
            self.cell["href"] = attrs.get("href", "")

    def handle_data(self, data):
        if self.in_cell and self.cell is not None:
            self.cell["text"].append(data.strip())
            if self.in_anchor:
                self.cell["anchor"] += data.strip()

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag == "a":
            self.in_anchor = False
        elif tag in ("td", "th"):
            self.in_cell = False
            self.cell = None
        elif tag == "tr":
            if self.in_row and self.row:
                self.rows.append(self.row)
            self.in_row = False
        elif tag == "table":
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.in_table = False

def cell_text(cell):
    return " ".join(x for x in cell["text"] if x).strip()

req = urllib.request.Request(
    URL,
    headers={"User-Agent": "Mozilla/5.0 (compatible; GarmentTechAudit/1.0)"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    html = response.read().decode("utf-8", errors="replace")
    print("HTTP:", response.status)
    print("URL akhir:", response.geturl())

parser = SpecTableParser()
parser.feed(html)

official = {}
for row in parser.rows:
    if len(row) < 9:
        continue
    model = row[0]["anchor"].strip().upper()
    if not model.startswith("VM180"):
        continue
    official[model] = {
        "official_url": row[0]["href"],
        "description": cell_text(row[0]).replace(model, "", 1).strip(),
        "needles": cell_text(row[1]),
        "threads": cell_text(row[2]),
        "needle_distance_mm": cell_text(row[3]),
        "stitch_length_mm": cell_text(row[4]),
        "presser_foot_lift_mm": cell_text(row[5]),
        "needle_stroke_mm": cell_text(row[6]),
        "machine_speed_sti_min": cell_text(row[7]),
        "remarks": cell_text(row[8]),
    }

# Baca database secara read-only.
db_uri = "file:" + str(DB.resolve()) + "?mode=ro"
con = sqlite3.connect(db_uri, uri=True)
con.row_factory = sqlite3.Row

machines = con.execute("""
    SELECT m.id AS machine_id, m.model
    FROM machines m
    JOIN brands b ON b.id = m.brand_id
    WHERE UPPER(b.name) LIKE '%YAMATO%'
      AND UPPER(m.model) LIKE 'VM180%'
    ORDER BY m.model
""").fetchall()

fields = [
    "machine_id", "model", "match_status", "review_flag",
    "official_url", "description", "needles", "threads",
    "needle_distance_mm", "stitch_length_mm",
    "presser_foot_lift_mm", "needle_stroke_mm",
    "machine_speed_sti_min", "remarks"
]

matched = 0
unmatched = []
with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for machine in machines:
        model = machine["model"].strip().upper()
        spec = official.get(model)

        if not spec:
            unmatched.append(model)
            writer.writerow({
                "machine_id": machine["machine_id"],
                "model": machine["model"],
                "match_status": "TIDAK DITEMUKAN",
                "review_flag": "Perlu pemeriksaan manual"
            })
            continue

        matched += 1
        flags = []
        if model == "VM1804PR-382-003":
            flags.append("ANOMALI SUMBER: baris resmi menyebut 6 jarum/12 benang")
        if spec["needles"] == "" or spec["threads"] == "":
            flags.append("Jumlah jarum/benang kosong")
        if not spec["official_url"]:
            flags.append("URL model resmi kosong")

        writer.writerow({
            "machine_id": machine["machine_id"],
            "model": machine["model"],
            "match_status": "COCOK PERSIS",
            "review_flag": "; ".join(flags) if flags else "Belum ada anomali otomatis",
            **spec
        })

con.close()

print()
print("===== HASIL AUDIT VM180 =====")
print("Model VM180 di database :", len(machines))
print("Model cocok persis      :", matched)
print("Model tidak ditemukan   :", len(unmatched))
print("CSV dibuat              :", OUT.resolve())
if unmatched:
    print("Perlu dicocokkan manual :", ", ".join(unmatched))
print("Database tidak diubah.")
