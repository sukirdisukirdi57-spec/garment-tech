import csv
import shutil
from pathlib import Path
from datetime import datetime

p = Path("tmp/lbh1790an/proposal_error_codes_stage6.csv")

with p.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if len(rows) != 12 or sum(r["code"] == "E905" for r in rows) != 1:
    raise SystemExit("Validasi awal gagal; file tidak diubah.")

r = next(r for r in rows if r["code"] == "E905")
if "LBH-1790A Instruction Manual" not in r["source"]:
    raise SystemExit("Sumber E905 tidak cocok dengan yang diharapkan.")

backup = p.with_name(
    p.stem + "-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv.bak"
)
shutil.copy2(p, backup)

r["source"] = (
    "JUKI LBH-1790AN/1795AN Instruction Manual, "
    "VIII. Error Code List, hlm. cetak 79"
)

tmp = p.with_suffix(".csv.tmp")
with tmp.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

with tmp.open(encoding="utf-8-sig", newline="") as f:
    check = list(csv.DictReader(f))

if len(check) != 12 or next(
    r for r in check if r["code"] == "E905"
)["source"] != r["source"]:
    tmp.unlink(missing_ok=True)
    raise SystemExit("Validasi gagal; proposal asli tidak diganti.")

tmp.replace(p)
print("KOREKSI SUMBER E905 BERHASIL")
print("Cadangan:", backup)
print("Database: tidak diubah")
print("Status: proposal saja, belum diimpor")
