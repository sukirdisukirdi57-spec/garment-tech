from pathlib import Path
import csv
import shutil
from datetime import datetime

p = Path("tmp/lbh1790an/proposal_error_codes_stage5.csv")
if not p.is_file():
    raise SystemExit(f"Proposal tidak ditemukan: {p}")

with p.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

expected = [
    "E733", "E798", "E799", "E801", "E802", "E811",
    "E813", "E820", "E901", "E902", "E903", "E904"
]

if not fields or not {
    "code", "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source"
}.issubset(fields):
    raise SystemExit("Kolom CSV tidak sesuai. Proposal tidak diubah.")

if [r["code"] for r in rows] != expected:
    raise SystemExit("Daftar kode tidak sesuai. Proposal tidak diubah.")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = p.with_name(f"{p.stem}-{stamp}.csv.bak")
shutil.copy2(p, backup)

for r in rows:
    code = r["code"]
    r["source"] = (
        "JUKI LBH-1790AN/1795AN Instruction Manual, "
        "VIII. Error Code List, hlm. cetak 78"
    )

    if code in ("E798", "E799"):
        r["symptoms"] = (
            f"Panel menampilkan {code}; operasi ayun jarum tidak sesuai "
            "dengan jumlah jahitan."
        )
        r["possible_cause"] = (
            "Gerakan ayun jarum tidak sesuai dengan jumlah jahitan "
            "yang diprogram atau diperintahkan."
        )
        r["solution"] = (
            "Matikan daya mesin. Jika kode muncul kembali, minta teknisi "
            "memeriksa mekanisme ayun jarum dan sistem kendalinya sesuai "
            "prosedur servis."
        )

    elif code == "E811":
        r["symptoms"] = (
            "Panel menampilkan E811; sumber daya masukan terdeteksi "
            "mencapai atau melampaui batas yang ditentukan."
        )
        r["possible_cause"] = (
            "Tegangan atau kondisi daya masukan mencapai atau melebihi "
            "nilai yang ditentukan untuk mesin."
        )

    elif code == "E813":
        r["symptoms"] = (
            "Panel menampilkan E813; sumber daya masukan terdeteksi "
            "berada pada atau di bawah batas yang ditentukan."
        )
        r["possible_cause"] = (
            "Tegangan atau kondisi daya masukan berada pada atau di bawah "
            "nilai yang ditentukan untuk mesin."
        )

    elif code == "E903":
        r["problem"] = "Nilai suplai daya motor langkah tidak normal"
        r["possible_cause"] = (
            "Suplai daya motor langkah pada papan kendali servo berada "
            "di luar rentang nilai yang ditentukan."
        )

    elif code == "E904":
        r["problem"] = "Nilai suplai daya solenoid tidak normal"
        r["possible_cause"] = (
            "Suplai daya solenoid pada papan kendali servo berada "
            "di luar rentang nilai yang ditentukan."
        )

tmp = p.with_name(p.name + ".tmp")
try:
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with tmp.open(encoding="utf-8-sig", newline="") as f:
        check = list(csv.DictReader(f))

    if [r["code"] for r in check] != expected:
        raise SystemExit("Validasi gagal. Proposal asli tidak diganti.")

    tmp.replace(p)
finally:
    if tmp.exists():
        tmp.unlink()

print("PROPOSAL TAHAP 5 DIPERBAIKI")
print("Jumlah kode:", len(rows))
print("Cadangan:", backup)
print("Database: tidak diubah")
print("Status: proposal saja, belum diimpor")
