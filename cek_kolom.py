filename = "data/maica/UAM02-parts.txt"

with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for nomor in range(153, 160):
    line = lines[nomor - 1].rstrip("\n")

    print()
    print("=" * 100)
    print(f"BARIS {nomor}")
    print("=" * 100)

    # Tampilkan nomor kolom setiap 10 karakter
    print("".join(str((i // 10) % 10) for i in range(len(line))))
    print("".join(str(i % 10) for i in range(len(line))))
    print(line)
