import argparse
from pathlib import Path

BACKUP_DIR = Path("database")

# Pola khusus file backup, bukan database aktif atau database pengujian.
PATTERNS = [
    "garment-before-*.db",
    "garment-backup-*.db",
    "garment_backup_*.db",
]

KEEP = 10

parser = argparse.ArgumentParser(
    description="Pertahankan 10 backup database terbaru."
)
parser.add_argument(
    "--delete",
    action="store_true",
    help="Hapus backup yang lebih lama setelah menampilkan daftar."
)
args = parser.parse_args()

files = {}

for pattern in PATTERNS:
    for path in BACKUP_DIR.glob(pattern):
        if path.is_file():
            files[path.resolve()] = path

backups = sorted(
    files.values(),
    key=lambda p: (p.stat().st_mtime, p.name),
    reverse=True
)

print("=== BACKUP DATABASE ===")
print("Folder          :", BACKUP_DIR)
print("Jumlah backup   :", len(backups))
print("Dipertahankan   :", min(KEEP, len(backups)))

retained = backups[:KEEP]
to_delete = backups[KEEP:]

print("\n=== 10 BACKUP TERBARU ===")
for i, path in enumerate(retained, 1):
    print(f"{i:2}. {path.name}")

print("\n=== BACKUP LAMA ===")
if not to_delete:
    print("Tidak ada backup yang perlu dihapus.")
else:
    for path in to_delete:
        print(f"  {path.name}")

if not args.delete:
    print("\nMODE DRY RUN: belum ada file yang dihapus.")
    print("Jika daftar sudah benar, jalankan:")
    print("python cleanup_old_backups.py --delete")
else:
    deleted = 0

    for path in to_delete:
        path.unlink()
        print("DIHAPUS:", path.name)
        deleted += 1

    print("\nPEMBERSIHAN SELESAI")
    print("Backup dipertahankan:", len(retained))
    print("Backup dihapus      :", deleted)
