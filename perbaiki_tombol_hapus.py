from pathlib import Path
import shutil

path = Path("templates/needle_systems.html")
content = path.read_text()

old = '''        </p>
        {% endif %}

        <form method="post"
              action="/admin/needle-systems/{{ item['id'] }}/delete"
              onsubmit="return confirm('Yakin ingin menghapus sistem jarum {{ item['system_code']|e }}? Data yang dihapus tidak dapat dipulihkan dari halaman ini.');"
              style="margin-top:8px;">
            <button type="submit" name="confirm-delete-needle" value="1"
                    style="padding:9px 14px;background:#b42318;color:white;border:0;border-radius:6px;">
                Hapus Sistem Jarum
            </button>
        </form>
'''

new = '''        </p>

        <form method="post"
              action="/admin/needle-systems/{{ item['id'] }}/delete"
              onsubmit="return confirm('Yakin ingin menghapus sistem jarum {{ item['system_code']|e }}? Data yang dihapus tidak dapat dipulihkan dari halaman ini.');"
              style="margin-top:8px;">
            <button type="submit" name="confirm-delete-needle" value="1"
                    style="padding:9px 14px;background:#b42318;color:white;border:0;border-radius:6px;">
                Hapus Sistem Jarum
            </button>
        </form>
        {% endif %}
'''

if content.count(old) != 1:
    raise SystemExit(
        "GAGAL: pola tombol tidak cocok tepat satu kali. File tidak diubah."
    )

backup = Path(
    "templates/needle_systems.html.backup-before-fix-delete-visibility"
)
shutil.copy2(path, backup)
path.write_text(content.replace(old, new, 1))

print("BERHASIL: tombol Edit dan Hapus sekarang sama-sama dibatasi untuk admin.")
print("Cadangan:", backup)
