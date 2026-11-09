import csv
import re
from collections import Counter
from pathlib import Path

FILE = Path(__file__).with_name(
    "draf_ddl8000c_revisi_manual.csv"
)

WAJIB = [
    "target_machine_id", "target_model",
    "reference_machine_id", "reference_model",
    "code", "problem", "symptoms",
    "possible_cause", "solution",
    "safety_notes", "source", "review_status"
]

TEKS = [
    "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source"
]

def audit():
    if not FILE.exists():
        print("ERROR: CSV tidak ditemukan:", FILE)
        return

    with FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []

    print("=" * 60)
    print("AUDIT OTOMATIS TROUBLESHOOTING JUKI")
    print("=" * 60)
    print("File :", FILE.name)
    print("Baris:", len(rows))
    print()

    masalah = 0

    def lapor(pesan):
        nonlocal masalah
        masalah += 1
        print(f"[PERIKSA] {pesan}")

    # 1. Struktur kolom
    for kolom in WAJIB:
        if kolom not in headers:
            lapor(f"Kolom wajib tidak ditemukan: {kolom}")

    if any(k not in headers for k in WAJIB):
        print("\nAudit dihentikan karena struktur kolom tidak lengkap.")
        return

    # 2. Kode kosong dan duplikat
    kode = [r["code"].strip().upper() for r in rows]
    hitung = Counter(k for k in kode if k)

    for i, r in enumerate(rows, start=2):
        if not r["code"].strip():
            lapor(f"Kode kosong pada baris CSV {i}")

    for k, n in sorted(hitung.items()):
        if n > 1:
            lapor(f"Kode {k} muncul {n} kali")

    print(f"Kode unik: {len(hitung)}")
    print()

    # 3. Kolom kosong
    for i, r in enumerate(rows, start=2):
        k = r["code"].strip() or f"baris {i}"
        for kolom in WAJIB:
            if not r.get(kolom, "").strip():
                lapor(f"{k}: kolom '{kolom}' kosong")

    # 4. Status verifikasi
    print("\n--- STATUS VERIFIKASI ---")
    status_count = Counter(
        r["review_status"].strip() or "(KOSONG)"
        for r in rows
    )
    for status, jumlah in sorted(status_count.items()):
        print(f"{status}: {jumlah}")

    for r in rows:
        status = r["review_status"].strip().upper()
        if status != "TERVERIFIKASI":
            print(
                f"[BELUM FINAL] {r['code']}: "
                f"{r['review_status']}"
            )

    # 5. Model target dan referensi
    print("\n--- MODEL ---")
    for r in rows:
        target = r["target_model"].strip()
        referensi = r["reference_model"].strip()
        if target and referensi and target.casefold() != referensi.casefold():
            lapor(
                f"{r['code']}: model target '{target}' "
                f"berbeda dari referensi '{referensi}'; "
                "periksa kompatibilitas"
            )

    # 6. Angka teknis yang perlu dicocokkan ke manual
    print("\n--- ANGKA / NILAI TEKNIS ---")
    pola = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*"
        r"(?:VAC|VDC|V|A|mA|Hz|kHz|mm|cm|°C|ohm|Ω)\b",
        re.IGNORECASE
    )
    temuan_angka = 0

    for r in rows:
        for kolom in ["problem", "symptoms", "possible_cause",
                      "solution", "source"]:
            teks = r[kolom]
            for cocok in pola.finditer(teks):
                print(
                    f"[CEK MANUAL] {r['code']} / {kolom}: "
                    f"{cocok.group()}"
                )
                temuan_angka += 1

    if temuan_angka == 0:
        print("Tidak ditemukan angka dengan satuan yang dikenali.")

    # 7. Sumber dan keselamatan
    print("\n--- SUMBER DAN KESELAMATAN ---")
    for r in rows:
        if not r["source"].strip():
            lapor(f"{r['code']}: sumber manual belum dicantumkan")
        if not r["safety_notes"].strip():
            lapor(f"{r['code']}: catatan keselamatan kosong")

    # 8. Deskripsi identik
    print("\n--- DESKRIPSI YANG SAMA ---")
    kelompok = {}
    for r in rows:
        teks = " ".join(r["problem"].lower().split())
        if teks:
            kelompok.setdefault(teks, []).append(r["code"])

    ada_sama = False
    for teks, daftar in kelompok.items():
        if len(daftar) > 1:
            print(
                f"[BANDINGKAN] Kode {', '.join(daftar)} "
                f"memiliki deskripsi masalah sama: {teks}"
            )
            ada_sama = True

    if not ada_sama:
        print("Tidak ditemukan deskripsi masalah yang identik.")

    print("\n" + "=" * 60)
    print("RINGKASAN")
    print("Jumlah baris       :", len(rows))
    print("Jumlah kode unik   :", len(hitung))
    print("Temuan pemeriksaan :", masalah)
    print("Angka teknis       :", temuan_angka)
    print("CSV TIDAK diubah.")
    print("Database TIDAK disentuh.")
    print("=" * 60)
    print("Catatan: temuan adalah peringatan, bukan bukti kesalahan.")

if __name__ == "__main__":
    audit()
