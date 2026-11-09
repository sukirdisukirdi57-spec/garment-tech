import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp/bas311hn/g_staging_review.csv"

# G. Threading mechanism — printed page 35
# Semua baris wajib ditinjau sebelum keputusan impor.

rows = [
(1, "SB6587001", "1", "THREAD BREAKAGE DETECTOR UNIT", "RAW"),
(2, "SB2636001", "1", "THREAD RETAINER", "RAW"),
(3, "012500536", "2", "SET SCREW SOCKET (FT) M5X5", "RAW"),
(4, "SA3306001", "1", "SHOULDER SCREW, 7-3", "RAW"),
(5, "120265002", "1", "SPRING WASHER", "RAW"),
(6, "S07350002", "1", "WASHER PLAIN", "RAW"),
(7, "S55485001", "1", "BOLT SOCKET (S/P WASHER) M5X12", "RAW"),
(8, "SA4333001", "1", "ARM THREAD GUIDE, B", "RAW"),
(9, "062500616", "1", "SCREW PAN M5X6", "RAW"),
(10, "SA6391001", "1", "ARM THREAD GUIDE C", "RAW"),
(11, "062500616", "1", "SCREW PAN M5X6", "RAW"),
(12, "SB1086001", "1", "ARM THREAD GUIDE D", "RAW"),
(13, "062500616", "1", "SCREW PAN M5X6", "RAW"),
(14, "SA3256001", "1", "TENSION STUD A", "RAW"),
(15, "145446001", "2", "DISC TENSION", "RAW"),
(16, "SA8691001", "1", "THREAD GUIDE ARM", "RAW"),
(17, "021400306", "1", "NUT 3 M4", "RAW"),
(18, "SA9207001", "1", "RUBBER COVER", "RAW"),
(19, "SA3257-101", "1", "NEEDLE BAR THREAD GUIDE,A", "PLUS"),
(20, "SA3258001", "1", "N-BAR BUSH THREAD GUIDE,D", "RAW"),
(21, "100136001", "1", "TENSION NUT", "RAW"),
(22, "SA4146-101", "1", "SUB TENSION SPRING", "PLUS"),
(23, "", "1", "WASHER", "VARIANT_REVIEW"),
(24, "SA6193-001", "1", "THREAD TAKE-UP SPRING", "PLUS"),
(25, "SB6468002", "1", "D TENSION ASSY", "03_05"),
(26, "SB6433001", "1", "DT TENSION STUD", "03_05"),
(27, "SB1088101", "1", "SET COLLAR DT", "03_05"),
(28, "SB1180201", "1", "SHAFT", "03_05"),
(29, "SB1181001", "1", "DT CUSHION", "03_05"),
(30, "SA6190001", "1", "DISC DT", "03_05"),
(31, "SB1267001", "1", "COIL SPRING", "03_05"),
(32, "145446001", "1", "DISC TENSION", "03_05"),
(33, "SB1281001", "1", "TAPER DISC PRESSER", "03_05"),
(34, "018301036", "1", "BOLT SOCKET M3X10", "03_05"),
(35, "SB1182101", "1", "TENSION BRACKET ASSY", "03_05"),
(36, "012400436", "1", "SET SCREW SOCKET (FT) M4X4", "03_05"),
(37, "048060142", "1", "RETAINING RING EXTERNAL C6", "03_05"),
(38, "109763022", "1", "WASHER", "03_05"),
(39, "SB6264001", "1", "PIN 1.8X25", "03_05"),
(40, "SA3520501", "", "TENSION BRACKET D ASSY", "07A"),
(41, "SA3254001", "1", "TENSION BRACKET", "07A"),
(42, "100402004", "1", "SET SCREW SM3.57", "07A"),
(43, "SA3255001", "1", "TENSION STUD", "07A"),
(44, "145446001", "2", "DISC TENSION", "07A"),
(45, "159805001", "1", "TENSION DISC PRESSER", "07A"),
(46, "S12441001", "1", "WASHER", "07A"),
(47, "S31032002", "1", "TENSION NUT", "07A"),
(48, "", "1", "TENSION SPRING", "VARIANT_REVIEW"),
(49, "S12699000", "1", "TENSION RELEASE PIN", "RAW"),
(50, "152881101", "1", "NEEDLE COOLER ASSY", "OPTION"),
(51, "012060636", "1", "SET SCREW SOCKET (FT) M6X6", "OPTION"),
(52, "152883000", "1", "FELT, 8X15.5", "OPTION"),
(53, "152884001", "1", "NEEDLE COOLER THREAD GUIDE", "OPTION"),
(54, "062670412", "1", "SCREW PAN SM3.57-40X4", "OPTION"),
]

fields = [
    "catalog_ref", "part_number", "quantity_raw", "part_name",
    "diagram_page", "mechanism", "verification", "review_note",
]

if OUTPUT.exists():
    raise SystemExit(f"STOP: staging sudah ada, tidak ditimpa: {OUTPUT}")

if [r[0] for r in rows] != list(range(1, 55)):
    raise SystemExit("STOP: referensi harus lengkap 1–54")

for ref, code, qty, name, group in rows:
    if not name:
        raise SystemExit(f"STOP: nama kosong pada ref {ref}")
    if qty and not qty.isdigit():
        raise SystemExit(f"STOP: kuantitas tidak valid pada ref {ref}")

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for ref, code, qty, name, group in rows:
        note = {
            "RAW": "Transkripsi awal halaman cetak 35; perlu dicocokkan.",
            "PLUS": "Kode dipetakan dari Different parts list halaman 73 untuk -03S; perlu audit.",
            "VARIANT_REVIEW": "Kode/varian belum terverifikasi untuk BAS-311HN-03S.",
            "03_05": "Kelompok For -03[],-05[]; perlu verifikasi penerapan ke -03S.",
            "07A": "Kelompok For -07A; jangan terapkan ke -03S tanpa bukti.",
            "OPTION": "Kelompok Option parts; perlu audit penerapan ke -03S.",
        }[group]
        writer.writerow({
            "catalog_ref": ref,
            "part_number": code,
            "quantity_raw": qty,
            "part_name": name,
            "diagram_page": 35,
            "mechanism": "G Threading mechanism (BAS-311HN/326H)",
            "verification": "REVIEW_REQUIRED",
            "review_note": note,
        })

print("Staging dibuat:", OUTPUT.relative_to(ROOT))
print("Jumlah referensi:", len(rows))
print("Rentang ref: 1–54")
print("Halaman cetak: 35; diagram_page diset 35")
print("Semua status: REVIEW_REQUIRED")
print("Database diubah: TIDAK")
