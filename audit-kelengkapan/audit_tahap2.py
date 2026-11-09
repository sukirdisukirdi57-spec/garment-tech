import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "draf_ddl8000c_revisi_manual.csv"
OUTPUT = BASE / "laporan_audit_tahap2.csv"

REQUIRED = [
    "target_machine_id", "target_model",
    "reference_machine_id", "reference_model",
    "code", "problem", "symptoms",
    "possible_cause", "solution",
    "safety_notes", "source", "review_status"
]

TEXT_FIELDS = [
    "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source"
]

NUMBER_PATTERN = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*"
    r"(?:VAC|VDC|V|A|mA|Hz|kHz|mm|cm|°C|ohm|Ω)\b",
    re.IGNORECASE
)

def main():
    if not SOURCE.is_file():
        print("ERROR: CSV sumber tidak ditemukan:", SOURCE)
        return

    with SOURCE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)

    missing_headers = [c for c in REQUIRED if c not in headers]
    if missing_headers:
        print("ERROR: Kolom wajib tidak ditemukan:")
        for c in missing_headers:
            print("-", c)
        print("Tidak ada laporan yang dibuat.")
        return

    codes = [
        (r.get("code") or "").strip().upper()
        for r in rows
    ]
    counts = Counter(c for c in codes if c)

    # Kelompokkan deskripsi masalah yang identik.
    problem_groups = defaultdict(list)
    for r in rows:
        code = (r.get("code") or "").strip().upper()
        problem = " ".join(
            (r.get("problem") or "").casefold().split()
        )
        if code and problem:
            problem_groups[problem].append(code)

    duplicate_problems = {}
    for problem, group in problem_groups.items():
        unique_codes = sorted(set(group))
        if len(unique_codes) > 1:
            for code in unique_codes:
                duplicate_problems.setdefault(code, []).append(
                    ", ".join(unique_codes)
                )

    report = []
    for r in rows:
        code = (r.get("code") or "").strip().upper()
        findings = []
        actions = []
        priority = "RENDAH"

        def add(level, finding, action):
            nonlocal priority
            findings.append(finding)
            actions.append(action)
            if level == "TINGGI":
                priority = "TINGGI"
            elif level == "SEDANG" and priority != "TINGGI":
                priority = "SEDANG"

        # Kode kosong atau duplikat.
        if not code:
            add("TINGGI", "Kode kosong", "Identifikasi kode yang benar")
        elif counts[code] > 1:
            add("TINGGI", f"Kode duplikat: {counts[code]} baris",
                "Periksa duplikasi; jangan hapus otomatis")

        # Kolom wajib kosong.
        empty = [
            c for c in REQUIRED
            if not (r.get(c) or "").strip()
        ]
        if empty:
            add("TINGGI", "Kolom kosong: " + ", ".join(empty),
                "Lengkapi data berdasarkan sumber yang sah")

        # Status review.
        status = (r.get("review_status") or "").strip()
        if status.upper() != "TERVERIFIKASI":
            add("SEDANG", "Status belum final: " + (status or "KOSONG"),
                "Verifikasi isi dan sumber sebelum menyatakan final")

        # Perbedaan model.
        target = (r.get("target_model") or "").strip()
        reference = (r.get("reference_model") or "").strip()
        if target and reference and target.casefold() != reference.casefold():
            add(
                "SEDANG",
                f"Model target '{target}' berbeda dari referensi '{reference}'",
                "Pastikan manual dan kode berlaku untuk varian target"
            )

        # Nilai teknis bersatuan.
        numeric_hits = []
        for field in ["problem", "symptoms", "possible_cause",
                      "solution", "source"]:
            value = r.get(field) or ""
            for match in NUMBER_PATTERN.finditer(value):
                numeric_hits.append(f"{field}: {match.group().strip()}")

        if numeric_hits:
            add(
                "SEDANG",
                "Nilai teknis: " + "; ".join(numeric_hits),
                "Cocokkan angka, konteks, dan varian dengan manual"
            )

        # Sumber dan keselamatan.
        if not (r.get("source") or "").strip():
            add("TINGGI", "Sumber manual kosong",
                "Temukan dan catat sumber yang bisa diverifikasi")

        if not (r.get("safety_notes") or "").strip():
            add("TINGGI", "Catatan keselamatan kosong",
                "Tinjau risiko sebelum menambahkan instruksi kerja")

        # Deskripsi masalah identik.
        if code in duplicate_problems:
            groups = sorted(set(duplicate_problems[code]))
            add(
                "RENDAH",
                "Deskripsi masalah identik dengan kode: " +
                " | ".join(groups),
                "Bandingkan definisi manual; jangan gabungkan otomatis"
            )

        if not findings:
            findings.append("Tidak ada temuan otomatis")
            actions.append("Tetap lakukan verifikasi teknis manual")

        report.append({
            "code": code,
            "target_model": target,
            "reference_model": reference,
            "review_status": status,
            "priority": priority,
            "findings": " || ".join(findings),
            "recommended_actions": " || ".join(actions),
        })

    # Jangan menimpa laporan lama secara tidak sengaja.
    if OUTPUT.exists():
        print("ERROR: Laporan sudah ada:", OUTPUT.name)
        print("Tidak ditimpa. Ganti nama/hapus laporan lama secara manual")
        print("jika memang ingin membuat ulang.")
        return

    fields = [
        "code", "target_model", "reference_model",
        "review_status", "priority", "findings",
        "recommended_actions"
    ]

    with OUTPUT.open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report)

    print("=" * 55)
    print("AUDIT TAHAP 2 SELESAI")
    print("=" * 55)
    print("Baris sumber :", len(rows))
    print("Kode unik    :", len(set(c for c in codes if c)))
    print("Baris laporan:", len(report))
    print("Prioritas:")
    for level in ["TINGGI", "SEDANG", "RENDAH"]:
        print(f"  {level}: {sum(x['priority'] == level for x in report)}")
    print("Laporan:", OUTPUT)
    print("CSV sumber tidak diubah.")
    print("Database tidak disentuh.")
    print("Prioritas adalah alat bantu pemeriksaan, bukan vonis teknis.")

if __name__ == "__main__":
    main()
