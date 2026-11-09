import csv
import re
from pathlib import Path

text_file = Path("ps800-12080-instruction.txt")
out_file = Path("ps800-error-codes-review.csv")

if not text_file.exists():
    raise SystemExit("GAGAL: file teks manual tidak ditemukan.")

# Hanya kode yang benar-benar tercantum dalam tabel manual.
expected = (
    [f"E{i:03d}" for i in range(1, 8)]
    + [f"E{i:03d}" for i in range(20, 112)]
    + [f"E{i:03d}" for i in range(200, 251)]
)
expected_set = set(expected)

records = {}
current = None

def finish():
    global current
    if current:
        code, problem, solution = current
        problem = " ".join(" ".join(problem).split())
        solution = " ".join(" ".join(solution).split())
        if problem:
            records[code] = {
                "code": code,
                "problem": problem,
                "symptoms": f"Panel menampilkan kode {code}.",
                "possible_cause": "",
                "solution": solution or
                    "Solusi tidak dicantumkan dalam tabel kode error manual.",
                "safety_notes":
                    "Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, "
                    "servo, dan komponen internal dilakukan teknisi kompeten.",
                "source":
                    "JUKI PS-800-12080 Instruction Manual, bagian 4-26, "
                    "List of error codes, halaman 46-50."
            }
    current = None

for line in text_file.read_text(
        encoding="utf-8", errors="replace").splitlines():

    match = re.match(r"^\s*(E\d{3})\s+(.*)$", line)

    if match and match.group(1) in expected_set:
        finish()
        code = match.group(1)
        payload = match.group(2).strip()
        parts = re.split(r"\s{2,}", payload, maxsplit=1)

        description = parts[0].strip()
        solution = parts[1].strip() if len(parts) > 1 else ""
        current = [code, [description], [solution] if solution else []]
        continue

    if current is None:
        continue

    stripped = line.strip()
    if not stripped:
        continue

    indent = len(line) - len(line.lstrip())

    # Abaikan judul tabel, judul bab, dan nomor halaman.
    if stripped.startswith("Error code") or stripped.startswith("–"):
        continue
    if "MAINTENANCE OF" in stripped:
        finish()
        continue

    # Teks solusi yang berlanjut pada kolom sebelah kanan.
    if indent >= 55:
        current[2].append(stripped)
    # Teks deskripsi yang berlanjut pada kolom sebelah kiri.
    elif indent >= 12:
        current[1].append(stripped)

finish()

missing = [code for code in expected if code not in records]
unexpected = [code for code in records if code not in expected_set]

if missing or unexpected or len(records) != 150:
    print("AUDIT BELUM LENGKAP — CSV final tidak dibuat.")
    print("Jumlah kode terbaca:", len(records), "dari 150")
    print("Kode yang belum terbaca:", ", ".join(missing) or "tidak ada")
    print("Kode di luar daftar:", ", ".join(unexpected) or "tidak ada")
    print("Periksa hasil ekstraksi dan format teks PDF terlebih dahulu.")
    raise SystemExit(1)

fields = [
    "code", "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source"
]

with out_file.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records[code] for code in expected)

print("CSV audit berhasil dibuat:", out_file)
print("Jumlah kode:", len(records))
print("Kode pertama:", expected[0])
print("Kode terakhir:", expected[-1])
print("Database tidak diubah.")
print()
print("Periksa beberapa baris pertama:")
for code in expected[:7]:
    row = records[code]
    print(f"{code}: {row['problem']} | {row['solution']}")
