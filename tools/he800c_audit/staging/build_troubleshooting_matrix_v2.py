import csv
import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
OUT = Path("tools/he800c_audit/staging/he800c_troubleshooting_matrix_v2.csv")

categories = [
    (1, "Upper thread breakage", "78-79", [672]),
    (2, "Skipped stitches", "79", []),
    (3, "Uneven seams (1) - at sewing start", "81", []),
    (4, "Uneven seams (2) - lower thread lifted at sewing start", "82", []),
    (5, "Uneven seams (3) - seam lifts at sewing start", "82", []),
    (6, "Uneven seams (4) - uneven sewing pitch at sewing start", "83", []),
    (7, "Uneven seams (5) - poor rounding of seam", "83", []),
    (8, "Uneven seams (6) - around rear tack or front tack", "84", []),
    (9, "Uneven seams (7) - loose thread end at end backtack", "83", []),
    (10, "Uneven seams (8) - thread sticking out at end backtack", "84", []),
    (11, "Uneven seams (9) - sticking in needle plate", "84", []),
    (12, "Uneven seams (10) - all stitches", "85", []),
    (13, "Upper thread run out", "86-87", []),
    (14, "Unraveling of thread trimmed by upper thread trimmer", "88", []),
    (15, "Upper thread miss-trimming", "89", []),
    (16, "Needle strikes upper thread trimmer", "90-91", []),
    (17, "Needle breakage", "91", [674]),
    (18, "Imperfect cutter function / material cutting", "91-92", [675]),
    (19, "Cutter does not return", "92", []),
    (20, "Cutter and upper thread trimmer touch", "93", []),
    (21, "Seam is cut", "93", []),
    (22, "Upper thread miss-winding", "94", []),
    (23, "Work clamp is not raised (1) - no pulse motor sound", "94", []),
    (24, "Work clamp is not raised (2) - pulse motor sound audible", "95", []),
    (25, "Lower thread is not trimmed / pulls when material removed", "96", []),
    (26, "Feed mechanism does not operate / motor out of step", "96", []),
    (27, "Needle does not zigzag / noise during zigzag", "97", []),
    (28, "Sewing machine stops during sewing", "97", []),
    (29, "Upper shaft does not reach needle-up stop position", "97", []),
    (30, "Operation panel display freezes", "97", []),
]

fields = [
    "manual_category", "manual_title", "manual_page",
    "existing_ids", "existing_problems", "audit_status",
    "cause_verified", "solution_verified",
    "technician_only_check", "review_notes",
]

if OUT.exists():
    raise SystemExit(f"Dibatalkan: file sudah ada, tidak ditimpa: {OUT}")

# Buka database dalam mode baca-saja.
uri = f"file:{DB.resolve()}?mode=ro"
with sqlite3.connect(uri, uri=True) as con:
    con.row_factory = sqlite3.Row
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id = 102"
    ).fetchone()

    if not machine or machine["model"] != "HE-800C":
        raise SystemExit("Dibatalkan: machine ID 102 bukan HE-800C.")

    rows = con.execute("""
        SELECT id, problem
        FROM troubleshooting
        WHERE machine_id = 102
        ORDER BY id
    """).fetchall()

existing = {row["id"]: row["problem"] for row in rows}

expected = {
    672: "Benang sering putus",
    674: "Jarum patah",
    675: "Pemotongan lubang kancing tidak sempurna",
}
for row_id, expected_problem in expected.items():
    if existing.get(row_id) != expected_problem:
        raise SystemExit(
            f"Dibatalkan: judul troubleshooting ID {row_id} berubah."
        )

OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("x", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for number, title, page, candidate_ids in categories:
        matched = [
            (row_id, existing[row_id])
            for row_id in candidate_ids
            if row_id in existing
        ]

        writer.writerow({
            "manual_category": f"11-{number}",
            "manual_title": title,
            "manual_page": page,
            "existing_ids": "; ".join(str(x[0]) for x in matched),
            "existing_problems": "; ".join(x[1] for x in matched),
            "audit_status": (
                "KANDIDAT_PERLU_REVIEW"
                if matched else "PERLU_AUDIT_SUMBER"
            ),
            "cause_verified": "BELUM",
            "solution_verified": "BELUM",
            "technician_only_check": "PERIKSA_TANDA_BINTANG_DI_MANUAL",
            "review_notes": (
                "Belum disetujui. Verifikasi gejala, penyebab, solusi "
                "dan halaman manual. Pisahkan tindakan operator dari "
                "penyetelan bertanda bintang khusus teknisi."
            ),
        })

print("Matriks v2 berhasil dibuat.")
print("Kategori:", len(categories))
print("Troubleshooting lama:", len(rows))
print("Database hanya dibaca; tidak diubah.")
print("File:", OUT)
