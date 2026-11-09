from pathlib import Path
import shutil
import sys

p = Path("templates/needle_series_admin.html")
if not p.exists():
    sys.exit("GAGAL: template Master Seri Jarum tidak ditemukan.")

s = p.read_text()

if 'href="/admin/needle-series/{{ item[&quot;id&quot;] }}/edit"' in s:
    sys.exit("Tombol Edit tampaknya sudah ada.")

notice_old = """    {% if error %}
    <div class="notice error" role="alert">{{ error }}</div>
    {% endif %}"""

notice_new = """    {% if request.args.get('edited') == '1' %}
    <div class="notice" role="status">
        Perubahan seri jarum berhasil disimpan.
    </div>
    {% endif %}

    {% if error %}
    <div class="notice error" role="alert">{{ error }}</div>
    {% endif %}"""

entry_old = """        {% if item["verification_notes"] %}
        <p class="muted">{{ item["verification_notes"] }}</p>
        {% endif %}
    </section>"""

entry_new = """        {% if item["verification_notes"] %}
        <p class="muted">{{ item["verification_notes"] }}</p>
        {% endif %}

        <p>
            <a class="edit-link"
               href="/admin/needle-series/{{ item['id'] }}/edit">
                Edit seri ini
            </a>
        </p>
    </section>"""

if s.count(notice_old) != 1:
    sys.exit("GAGAL: lokasi pemberitahuan tidak cocok.")
if s.count(entry_old) != 1:
    sys.exit("GAGAL: lokasi daftar seri tidak cocok.")

new_s = s.replace(notice_old, notice_new, 1)
new_s = new_s.replace(entry_old, entry_new, 1)

css_marker = "        .muted { color: #555; font-size: 14px; }"
css_new = css_marker + """
        .edit-link {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 6px;
            background: #075bb5;
            color: white;
            text-decoration: none;
        }"""

if new_s.count(css_marker) != 1:
    sys.exit("GAGAL: lokasi CSS tidak cocok.")
new_s = new_s.replace(css_marker, css_new, 1)

backup = Path("templates/needle_series_admin.html.backup-before-edit-auto")
if not backup.exists():
    shutil.copy2(p, backup)

p.write_text(new_s)
print("BERHASIL: tombol Edit ditambahkan.")
print("Pemberitahuan setelah edit juga ditambahkan.")
print(f"Cadangan template: {backup}")
