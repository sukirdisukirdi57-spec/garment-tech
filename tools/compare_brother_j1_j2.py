import re
import subprocess
from pathlib import Path

pdf = Path(
    "assets/documents/brother/t8421d/"
    "t8421d_t8422d_parts_en.pdf"
)

if not pdf.is_file():
    raise SystemExit(f"PDF tidak ditemukan: {pdf}")

result = subprocess.run(
    ["pdftotext", "-layout", str(pdf), "-"],
    capture_output=True,
    text=True,
    check=True,
)
lines = result.stdout.splitlines()

# Batas bagian berdasarkan nomor baris hasil ekstraksi PDF yang sudah diperiksa.
# Nomor di sini mengikuti nomor baris pdftotext (dimulai dari 1).
sections = {
    "J1": (1003, 1137),
    "J2": (1138, 1329),
}

# Nomor referensi | nomor part | jumlah | deskripsi
part_pattern = re.compile(
    r"^\s*(\d+\+?)\s+([A-Z0-9-]{6,})\s+(\d+)\s+(.+?)\s*$"
)

def extract_parts(start, end):
    found = {}
    for line_no in range(start, min(end, len(lines)) + 1):
        line = lines[line_no - 1]
        match = part_pattern.match(line)
        if not match:
            continue

        ref, code, qty, description = match.groups()
        code = code.strip()
        found.setdefault(code, {
            "ref": ref,
            "qty": qty,
            "description": description.strip(),
            "line": line_no,
        })
    return found

j1 = extract_parts(*sections["J1"])
j2 = extract_parts(*sections["J2"])

if not j1 or not j2:
    print("GAGAL: daftar part tidak berhasil dibaca.")
    print("Jumlah part terbaca:", "J1 =", len(j1), "| J2 =", len(j2))
    print("\nPeriksa batas tabel PDF dengan perintah:")
    print(
        "pdftotext -layout "
        "assets/documents/brother/t8421d/"
        "t8421d_t8422d_parts_en.pdf - | "
        "nl -ba | sed -n '990,1340p'"
    )
    raise SystemExit(1)

shared = sorted(set(j1) & set(j2))
only_j1 = sorted(set(j1) - set(j2))
only_j2 = sorted(set(j2) - set(j1))

def print_group(title, codes, left, right=None):
    print(f"\n{'=' * 76}\n{title} ({len(codes)} nomor part)\n{'=' * 76}")
    if not codes:
        print("Tidak ada.")
        return
    print(f"{'PART NUMBER':<16} {'REF J1':<9} {'REF J2':<9} DESKRIPSI")
    print("-" * 76)
    for code in codes:
        a = left.get(code, {})
        b = (right or {}).get(code, {})
        ref1 = a.get("ref", "-")
        ref2 = b.get("ref", "-")
        desc = a.get("description") or b.get("description", "")
        print(f"{code:<16} {ref1:<9} {ref2:<9} {desc}")

print("PERBANDINGAN KATALOG BROTHER")
print("J1 = T-8421D | J2 = T-8422D")
print(f"Jumlah nomor part unik J1 : {len(j1)}")
print(f"Jumlah nomor part unik J2 : {len(j2)}")
print(f"Nomor part yang sama      : {len(shared)}")
print(f"Khusus J1                 : {len(only_j1)}")
print(f"Khusus J2                 : {len(only_j2)}")

print_group("PART YANG SAMA", shared, j1, j2)
print_group("PART KHUSUS J1 / T-8421D", only_j1, j1)
print_group("PART KHUSUS J2 / T-8422D", only_j2, {}, j2)

output = Path("tools/hasil_perbandingan_j1_j2.txt")
with output.open("w", encoding="utf-8") as f:
    import contextlib
    with contextlib.redirect_stdout(f):
        print("PERBANDINGAN KATALOG BROTHER")
        print("J1 = T-8421D | J2 = T-8422D")
        print(f"Jumlah nomor part unik J1 : {len(j1)}")
        print(f"Jumlah nomor part unik J2 : {len(j2)}")
        print(f"Nomor part yang sama      : {len(shared)}")
        print(f"Khusus J1                 : {len(only_j1)}")
        print(f"Khusus J2                 : {len(only_j2)}")
        print_group("PART YANG SAMA", shared, j1, j2)
        print_group("PART KHUSUS J1 / T-8421D", only_j1, j1)
        print_group("PART KHUSUS J2 / T-8422D", only_j2, {}, j2)

print(f"\nLaporan disimpan: {output}")
