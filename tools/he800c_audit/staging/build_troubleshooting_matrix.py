import csv
import sqlite3
from pathlib import Path

DB = "database/garment.db"
OUT = Path("tools/he800c_audit/staging/he800c_troubleshooting_matrix.csv")

categories = [
    (1, "Upper thread breakage", 78),
    (2, "Skipped stitches", 79),
    (3, "Uneven seams (1) - at sewing start", 81),
    (4, "Uneven seams (2) - lower thread lifted at sewing start", 82),
    (5, "Uneven seams (3) - seam lifts at sewing start", 82),
    (6, "Uneven seams (4) - uneven sewing pitch at sewing start", 83),
    (7, "Uneven seams (5) - poor rounding of seam", 83),
    (8, "Uneven seams (6) - around rear tack or front tack", 84),
    (9, "Uneven seams (7) - loose thread end at end backtack", 84),
    (10, "Uneven seams (8) - thread sticking out at end backtack", 84),
    (11, "Uneven seams (9) - sticking in needle plate", 85),
    (12, "Uneven seams (10) - all stitches", 85),
    (13, "Upper thread run out", 86),
    (14, "Unraveling of thread trimmed by upper thread trimmer", 88),
    (15, "Upper thread miss-trimming", 89),
    (16, "Needle strikes upper thread trimmer", 90),
    (17, "Needle breakage", 91),
    (18, "Imperfect cutter function / material cutting", 91),
    (19, "Cutter does not return", 92),
    (20, "Cutter and upper thread trimmer touch", 93),
    (21, "Seam is cut", 93),
    (22, "Upper thread miss-winding", 94),
    (23, "Work clamp is not raised (1) - no pulse motor sound", 94),
    (24, "Work clamp is not raised (2) - pulse motor sound audible", 95),
    (25, "Lower thread is not trimmed", 96),
    (26, "Feed mechanism does not operate / motor out of step", 96),
    (27, "Needle does not zigzag / noise during zigzag", 97),
    (28, "Sewing machine stops during sewing", 97),
    (29, "Upper shaft does not reach needle-up stop position", 97),
    (30, "Operation panel display freezes", 97),
]

with sqlite3.connect(DB) as con:
    con.row_factory = sqlite3.Row
    machine = con.execute(
        "SELECT model FROM machines WHERE id = 102"
    ).fetchone()
    if not machine or machine["model"] != "HE-800C":
        raise SystemExit("Dibatalkan: ID 102 bukan HE-800C.")

    existing = con.execute("""
        SELECT id, problem, symptoms, possible_cause,
               solution, safety_notes, source
        FROM troubleshooting
        WHERE machine_id = 102
        ORDER BY id
    """).fetchall()

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "manual_category", "manual_title", "manual_page",
        "existing_ids", "existing_problems", "audit_status",
        "cause_verified", "solution_verified",
        "technician_only_check", "review_notes"
    ])
    writer.writeheader()

    for number, title, page in categories:
        # Pencocokan ini hanya kandidat; bukan penetapan bahwa dua masalah sama.
        matches = []
        key = title.lower()
        for row in existing:
            problem = (row["problem"] or "").lower()
            if (
                (number == 1 and "benang" in problem and "putus" in problem)
                or (number == 17 and "jarum patah" in problem)
                or (number == 18 and "pemotongan" in problem)
                or (number in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
                    and "jahitan" in problem)
            ):
                matches.append(row)

        writer.writerow({
            "manual_category": f"11-{number}",
            "manual_title": title,
            "manual_page": page,
            "existing_ids": "; ".join(str(r["id"]) for r in matches),
            "existing_problems": "; ".join(r["problem"] for r in matches),
            "audit_status": "PERLU_AUDIT_SUMBER",
            "cause_verified": "BELUM",
            "solution_verified": "BELUM",
            "technician_only_check": "PERIKSA_TANDA_BINTANG_DI_MANUAL",
            "review_notes": (
                "Baca bagian manual ini; bedakan pemeriksaan operator "
                "dari penyetelan khusus teknisi."
            )
        })

print("Matriks audit dibuat; database tidak diubah.")
print("Kategori manual:", len(categories))
print("Troubleshooting lama:", len(existing))
print("File:", OUT)
