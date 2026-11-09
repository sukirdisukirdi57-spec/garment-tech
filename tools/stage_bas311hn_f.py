import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp/bas311hn/f_staging_review.csv"

# F. Lubrication — Brother BAS-311HN/326H Parts Book

# Halaman cetak 31-33. Semua status perlu ditinjau sebelum impor.

rows = [
(1, "SA3244001", 1, "SET SCREW"),
(2, "SA4785101", 1, "CRANK COVER"),
(3, "SB4155001", 1, "BAND"),
(4, "062061016", 3, "SCREW PAN M6X10"),
(5, "SA4787001", 1, "CRANK WICK PLATE"),
(6, "062400616", 2, "SCREW PAN M4X6"),
(7, "SA5294001", 1, "FLAT WICK L=90"),
(8, "SA4786101", 1, "FELT"),
(9, "SA3503201", 1, "LOWER SHAFT WICK SUPPORT"),
(10, "SA3504201", 1, "LOWER SHAFT GEAR FELT"),
(11, "018400636", 2, "BOLT SOCKET M4X6"),
(12, "SA4788001", 1, "WICK SUPPORT"),
(13, "062400616", 1, "SCREW PAN M4X6"),
(14, "SA6593001", 1, "FLAT WICK L=180"),
(15, "SA6580001", 1, "WICK L=780"),
(16, "S07459100", 1, "OIL TUBE L=240"),
(17, "SA6576001", 1, "OIL TUBE L=210"),
(18, "SA6087001", 1, "WICK SUPPORT"),
(19, "104567101", 1, "WICK SUPPORT"),
(20, "S49992000", 2, "OIL GAUGE WINDOW"),
(21, "SA4025001", 1, "WICK, 4X4 L=180"),
(22, "SA2864001", 1, "OIL TUBE L=193"),
(23, "SB4524001", 1, "WICK 6X6 L=380"),
(24, "S09043000", 4, "FELT"),
(25, "S49982000", 1, "WICK, 4X4 L=400"),
(26, "S48189000", 1, "OIL TUBE L=280"),
(27, "SA3246001", 1, "GEAR WICK SUPPORT"),
(28, "SA3280001", 1, "GEAR FELT"),
(29, "SA4789101", 1, "LOWER SHAFT WICK SUPPORT B"),
(30, "062060816", 1, "SCREW PAN M6X8"),
(31, "145547021", 1, "TUBE HOLDER"),
(32, "062400616", 1, "SCREW PAN M4X6"),
(33, "026040136", 1, "WASHER PLAIN S 4"),
(34, "S49957000", 1, "WICK, 4X4 L=700"),
(35, "SA4791101", 1, "OIL TUBE L=620"),
(36, "SB6613001", 1, "CORD HOLDER"),
(37, "525567000", 1, "CORD HOLDER #8"),
(38, "0A5401006", 1, "SCREW PAN (S/P WASHER) M4X10"),
(39, "0A5401006", 1, "SCREW PAN (S/P WASHER) M4X10"),
(40, "525664000", 2, "CORD HOLDER #6"),
(41, "SA1394101", 2, "CORD HOLDER U3"),
(42, "SB4468001", 3, "TERMINAL"),
(43, "S38266000", 3, "ROTARY HOOK SHAFT FELT"),
(44, "SA2929001", 3, "RUBBER CAP, 12.5"),
(45, "0A5401006", 3, "SCREW PAN (S/P WASHER) M4X10"),
(46, "0A5401006", 2, "SCREW PAN (S/P WASHER) M4X10"),
(47, "0A5401006", 3, "SCREW PAN (S/P WASHER) M4X10"),
(48, "SB4387001", 1, "OIL COVER"),
(49, "SB4388001", 1, "OIL COVER PACKING"),
(50, "018401036", 10, "BOLT SOCKET M4X10"),
(51, "S50359001", 1, "TUBE SUPPORT, D"),
(52, "S38265000", 1, "TERMINAL, L"),
(53, "142274101", 1, "RUBBER CAP, 4.2"),
(54, "S59886001", 1, "FELT, L=360"),
(55, "SA9793001", 1, "VINYL TUBE L=160"),
(56, "SA5339101", 5, "OIL FEEDING PIPE"),
(57, "SB4570001", 2, "FELT L=230"),
(58, "SB4037001", 2, "VINYL TUBE"),
(59, "S08003000", 1, "WICK 4X4"),
(60, "SA6576001", 1, "OIL TUBE L=210"),
(61, "SB4736001", 1, "WICK 3X3 L=145"),
(62, "S50547000", 1, "OIL TUBE"),
(63, "SB4352001", 2, "Y-RACK SHAFT FELT ASSY"),
(64, "S50527000", 2, "OIL TUBE"),
(65, "SB4189001", 2, "Y-RACK SHAFT COVER"),
]

fields = [
"catalog_ref", "part_number", "quantity_raw", "part_name",
"diagram_page", "mechanism", "verification", "review_note",
]

if [r[0] for r in rows] != list(range(1, 66)):
    raise SystemExit("STOP: referensi harus lengkap 1–65")

for ref, code, qty, name in rows:
    if not code or not name or qty < 1:
        raise SystemExit(f"STOP: data tidak valid pada ref {ref}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for ref, code, qty, name in rows:
        writer.writerow({
            "catalog_ref": ref,
            "part_number": code,
            "quantity_raw": qty,
            "part_name": name,
            "diagram_page": 31,
            "mechanism": "F Lubrication (BAS-311HN/326H)",
            "verification": "REVIEW_REQUIRED",
            "review_note": "Transkripsi awal dari tabel katalog cetak halaman 31-33; perlu ditinjau sebelum impor.",
        })

print("Staging dibuat:", OUTPUT.relative_to(ROOT))
print("Jumlah referensi:", len(rows))
print("Rentang ref: 1–65")
print("Halaman katalog cetak: 31–33; diagram_page diset 31")
print("Status awal semua baris: REVIEW_REQUIRED")
print("Database diubah: TIDAK")
