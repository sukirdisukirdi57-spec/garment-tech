import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp/bas311hn/j_staging_review.csv"

# Transkripsi awal katalog Brother BAS-311HN/326H.
# Semua baris wajib diaudit sebelum boleh diimpor.
rows = [
    (1, "SA4131001", "1", "THREAD TRIMMER CAM"),
    (2, "S23651001", "2", "SET SCREW SOCKET (FT) M6X6"),
    (3, "SA4798001", "1", "SETTING PLATE SOLENOID"),
    (4, "SB6577001", "1", "THREAD TRIMMER SOLENOID"),
    (5, "021400216", "2", "NUT 2 M4"),
    (6, "028040246", "2", "WASHER SPRING 2-4"),
    (7, "SB3848001", "2", "WASHER PLAIN M 4"),
    (8, "SA3307001", "1", "SOLENOID LEVER"),
    (9, "012400436", "1", "SET SCREW SOCKET (FT) M4X4"),
    (10, "154599000", "1", "SOLENOID CUSHION"),
    (11, "S02652021", "1", "WASHER"),
    (12, "S55484001", "2", "BOLT SOCKET (S/P WASHER) M5X10"),
    (13, "SA4799001", "1", "PUSHING LEVER D-LEVER"),
    (14, "SA3306001", "1", "SHOULDER SCREW, 7-3"),
    (15, "SA3309201", "1", "TR-DRIVING LEVER"),
    (16, "SA3310001", "1", "COLLAR TR-TRIMMER"),
    (17, "SA3311001", "1", "COLLAR SHAFT"),
    (18, "S46903001", "1", "SET SCREW, M4X5"),
    (19, "048040342", "1", "RETAINING RING E4"),
    (20, "SB4416001", "1", "THREAD TRIMMER ROD ASSY V"),
    (21, "SB4393001", "1", "THREAD TRIMMER ROD V"),
    (22, "S32465101", "2", "BALL JOINT ASSY"),
    (23, "021060306", "2", "NUT 3 M6"),
    (24, "SB4401001", "1", "SHOULDER SCREW 6.35-6"),
    (25, "SB4401001", "1", "SHOULDER SCREW 6.35-6"),
    (26, "S23651001", "1", "SET SCREW SOCKET (FT) M6X6"),
    (27, "231071001", "1", "BUSH, 8X15"),
    (28, "SA3312201", "1", "GUIDE SHAFT"),
    (29, "SA6572001", "1", "WICK L=140"),
    (30, "SA3313101", "1", "SPRING, COMPRESSION"),
    (31, "021060306", "1", "NUT 3 M6"),
    (32, "154596000", "1", "CUSHION"),
    (33, "S25475101", "1", "SET SCREW M6X19"),
    (34, "021060106", "1", "NUT 1 M6"),
    (35, "SB4397001", "1", "THREAD TRIMMER LEVER"),
    (36, "SB4415001", "1", "THREAD TRIMMER ROD ASSY H"),
    (37, "SB4391001", "1", "THREAD TRIMMER ROD H"),
    (38, "S32465101", "2", "BALL JOINT ASSY"),
    (39, "021060306", "2", "NUT 3 M6"),
    (40, "SB4399001", "1", "SHAFT TR-TRIMMER LEVER"),
    (41, "SA4545001", "2", "SPACER"),
    (42, "012060636", "2", "SET SCREW SOCKET (FT) M6X6"),
    (43, "021060306", "1", "NUT 3 M6"),
    (44, "SB4398001", "1", "SPRING HOOK"),
    (45, "SA3321001", "1", "SPRING, EXTENSION"),
    (46, "SB4401001", "1", "SHOULDER SCREW 6.35-6"),
    (47, "021060306", "1", "NUT 3 M6"),
    (48, "SB4395001", "1", "MOVING KNIFE LEVER"),
    (49, "SA4588001", "1", "SET COLLAR"),
    (50, "012500536", "2", "SET SCREW SOCKET (FT) M5X5"),
    (51, "SB4401001", "1", "SHOULDER SCREW 6.35-6"),
    (52, "021060306", "1", "NUT 3 M6"),
    (53, "018061636", "1", "BOLT SOCKET M6X16"),
    (54, "SB4396001", "1", "SHAFT MOVABLE KNIFE LEVER"),
    (55, "SB4400001", "2", "THRUST WASHER"),
    (56, "SB4394001", "1", "M-KNIFE CONNECTING PLATE"),
    (57, "SA4354001", "1", "SHOULDER SCREW, 6-1.8"),
    (58, "SB4595001", "1", "NEEDLE PLATE"),
    (59, "SA6596001", "1", "MOVABLE KNIFE SET F"),
    (60, "SA4518001", "1", "MOVABLE KNIFE SHOULDER SCREW"),
    (61, "SA4519001", "1", "THRUST WASHER"),
    (62, "S00705001", "1", "MOVABLE KNIFE COLLAR"),
    # Ref 63 dan 66 menggunakan kode dari Different parts list -03S.
    (63, "SA7944-101", "1", "FIXED KNIFE FL"),
    (64, "062300416", "6", "SCREW PAN M3X4"),
    (65, "SB3847001", "6", "WASHER PLAIN M 3"),
    (66, "SA5221-001", "1", "NEEDLE HOLE PLATE 2.2"),
    (67, "100360003", "2", "SCREW"),
    (68, "S25310101", "2", "SCREW, FLAT M4"),
    (69, "SA3538001", "2", "SCREW M4X8"),
    (70, "SA6273101", "1", "SHUTTLE RACE COVER HOOK U"),
    (71, "028030246", "4", "WASHER SPRING 2-3"),
    (72, "SB0713001", "1", "BOBBIN THREAD CLAMP SPRING"),
]

if OUTPUT.exists():
    raise SystemExit(f"STOP: staging sudah ada, tidak ditimpa: {OUTPUT}")

if len(rows) != 72 or [r[0] for r in rows] != list(range(1, 73)):
    raise SystemExit("STOP: referensi harus lengkap dan berurutan 1–72")

fields = [
    "catalog_ref", "part_number", "quantity_raw", "part_name",
    "diagram_page", "mechanism", "verification", "review_note",
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for ref, code, qty, name in rows:
        note = "Transkripsi awal; cocokkan dengan katalog resmi sebelum impor."
        if ref in (63, 66):
            note = (
                "Kode awal dari Different parts list untuk -03S; "
                "wajib audit varian dan nama komponen."
            )
        writer.writerow({
            "catalog_ref": ref,
            "part_number": code,
            "quantity_raw": qty,
            "part_name": name,
            "diagram_page": 39,
            "mechanism": "J Thread trimmer mechanism (BAS-311HN/326H)",
            "verification": "REVIEW_REQUIRED",
            "review_note": note,
        })

print("Staging dibuat:", OUTPUT.relative_to(ROOT))
print("Jumlah referensi:", len(rows))
print("Rentang ref: 1–72")
print("Diagram page: 39")
print("Status: seluruh baris REVIEW_REQUIRED")
print("Database diubah: TIDAK")
