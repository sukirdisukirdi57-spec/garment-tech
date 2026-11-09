from pathlib import Path
import shutil

path = Path("templates/needle_systems.html")
content = path.read_text()

target = '''    {% if request.args.get("added") == "1" %}
    <div class="note" role="status">
        Sistem jarum berhasil disimpan. Status awal: Belum diverifikasi.
    </div>
    {% endif %}
'''

replacement = target + '''
    {% if request.args.get("edited") == "1" %}
    <div class="note" role="status" style="background:#e7f7e9;color:#17652b;padding:12px;border-radius:6px;margin:12px 0;">
        ✓ Perubahan sistem jarum berhasil disimpan.
    </div>
    {% endif %}
'''

if '{% if request.args.get("edited") == "1" %}' in content:
    raise SystemExit("Notifikasi edit sudah ada. Tidak ada perubahan.")

if target not in content:
    raise SystemExit("GAGAL: lokasi notifikasi tambah tidak ditemukan. File tidak diubah.")

backup = Path("templates/needle_systems.html.backup-before-edit-notice")
shutil.copy2(path, backup)

path.write_text(content.replace(target, replacement, 1))

print("BERHASIL: notifikasi edit ditambahkan.")
print("Cadangan dibuat:", backup)
