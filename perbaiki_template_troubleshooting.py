from pathlib import Path
import re
import shutil

path = Path("templates/troubleshooting.html")
content = path.read_text(encoding="utf-8")

start = content.find('<form method="GET" action="/troubleshooting"')
end = content.find("{% if troubleshooting_data %}", start)

if start == -1 or end == -1:
    raise SystemExit(
        "GAGAL: formulir atau batas hasil tidak ditemukan. "
        "Template tidak diubah."
    )

# Pastikan bagian yang akan diganti memang berakhir pada </form>
form_end = content.rfind("</form>", start, end)
if form_end == -1:
    raise SystemExit("GAGAL: penutup formulir tidak ditemukan.")

form_end += len("</form>")

new_form = '''<form method="GET" action="/troubleshooting"
      style="margin-bottom: 20px;">

    <label for="brand_id"><strong>1. Pilih Brand:</strong></label>
    <select id="brand_id" name="brand_id" required
            style="width: 100%; padding: 10px; box-sizing: border-box;"
            onchange="this.form.submit()">
        <option value="">Pilih brand</option>
        {% for brand in brands %}
        <option value="{{ brand['id'] }}"
            {% if brand_id == brand['id']|string %}selected{% endif %}>
            {{ brand['name'] }}
        </option>
        {% endfor %}
    </select>

    <br><br>

    <label for="machine_id"><strong>2. Pilih Seri Mesin:</strong></label>
    <select id="machine_id" name="machine_id" required
            style="width: 100%; padding: 10px; box-sizing: border-box;"
            {% if not brand_id %}disabled{% endif %}>
        <option value="">Pilih seri mesin</option>
        {% for machine in machines %}
            {% if brand_id == machine['brand_id']|string %}
            <option value="{{ machine['id'] }}"
                {% if machine_id == machine['id']|string %}selected{% endif %}>
                {{ machine['model'] }}
            </option>
            {% endif %}
        {% endfor %}
    </select>

    <br><br>

    <label for="search">
        <strong>3. Cari kode error atau gejala:</strong>
    </label>
    <input type="text" id="search" name="search"
           value="{{ search or '' }}"
           placeholder="Contoh: E71 atau masalah motor"
           style="width: 100%; box-sizing: border-box; padding: 10px;">

    <br><br>

    <button type="submit" class="add-button">
        Cari Troubleshooting
    </button>

    {% if search or machine_id or brand_id %}
    <a href="/troubleshooting" class="back-button">
        Hapus Pencarian
    </a>
    {% endif %}
</form>'''

backup = path.with_name("troubleshooting.html.sebelum-filter-brand")
if not backup.exists():
    shutil.copy2(path, backup)

path.write_text(
    content[:start] + new_form + content[form_end:],
    encoding="utf-8"
)

print("Form pencarian berhasil diperbarui.")
print("Cadangan template:", backup)
