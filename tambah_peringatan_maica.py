from pathlib import Path
from datetime import datetime
import shutil
import sys

file = Path("templates/troubleshooting.html")
marker = "CATATAN VERIFIKASI DATA MAICA"

if not file.exists():
    sys.exit("GAGAL: File template tidak ditemukan.")

content = file.read_text(encoding="utf-8")

if marker in content:
    sys.exit("AMAN: Peringatan MAICA sudah tersedia. Tidak ada perubahan.")

target = """        {% endif %}
        <p><strong>📊 Jumlah hasil:</strong>"""

if content.count(target) != 1:
    sys.exit("GAGAL: Pola target tidak ditemukan atau tidak unik. File tidak diubah.")

warning = """        {% endif %}

        {% if machine_id %}
            {% for machine in machines %}
                {% if machine_id == machine['id']|string and machine['model'] in ['MA-04', 'UAM-02', 'UAM-03', 'UAM-04'] %}
        <div class="warning" role="alert" style="padding:12px; margin:12px 0; border:1px solid #c58b24; border-radius:6px;">
            <strong>⚠️ CATATAN VERIFIKASI DATA MAICA</strong>
            <p>Data troubleshooting {{ machine['model'] }} merupakan panduan pemeriksaan umum berdasarkan referensi spesifikasi mesin. Data ini bukan daftar kode alarm resmi MAICA dan belum diverifikasi satu per satu menggunakan manual troubleshooting resmi.</p>
            <p>Kolom kode error yang kosong berarti kode resmi belum tersedia. Jangan mengarang atau menggunakan kode error yang belum dikonfirmasi.</p>
            {% if machine['model'] == 'UAM-02' %}
            <p>Catatan: referensi spesifikasi UAM-02 yang tersedia berasal dari sumber pihak ketiga, belum dari halaman resmi MAICA.</p>
            {% endif %}
        </div>
                {% endif %}
            {% endfor %}
        {% endif %}

        <p><strong>📊 Jumlah hasil:</strong>"""

backup = file.with_name(
    file.name + ".backup-" + datetime.now().strftime("%Y%m%d-%H%M%S")
)

shutil.copy2(file, backup)

updated = content.replace(target, warning, 1)

try:
    file.write_text(updated, encoding="utf-8")
except Exception:
    shutil.copy2(backup, file)
    sys.exit("GAGAL menulis file. Template dipulihkan dari backup.")

print("BERHASIL: Peringatan MAICA ditambahkan.")
print("Backup:", backup)
print("Template:", file)
