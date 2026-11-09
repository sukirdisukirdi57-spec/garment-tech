from pathlib import Path
from datetime import datetime
import shutil
import sys

template = Path("templates/needle_series_admin.html")
backup_dir = Path("backup/pencarian-katalog")
backup_dir.mkdir(parents=True, exist_ok=True)

if not template.is_file():
    sys.exit("GAGAL: template Master Seri tidak ditemukan.")

content = template.read_text(encoding="utf-8")

if 'id="seriesSearch"' in content or "seriesSearchResult" in content:
    sys.exit("DIBATALKAN: penanda pencarian sudah ada. Tidak ada perubahan.")

heading = '<h2>Daftar seri tersimpan ({{ series|length }})</h2>'
entry = '<section class="entry">'
closing = '</body>'

if content.count(heading) != 1:
    sys.exit("GAGAL: judul daftar seri tidak ditemukan secara unik.")

if content.count(entry) != 1:
    sys.exit("GAGAL: bagian kartu seri tidak ditemukan secara unik.")

if content.count(closing) != 1:
    sys.exit("GAGAL: penutup HTML tidak ditemukan secara unik.")

backup = backup_dir / (
    "needle_series_admin.html.sebelum-search-"
    + datetime.now().strftime("%Y%m%d-%H%M%S")
)
shutil.copy2(template, backup)

search_html = """
    <div class="field">
        <label for="seriesSearch">Cari seri jarum</label>
        <input id="seriesSearch" type="search"
               placeholder="Contoh: DB, Seri 134, diverifikasi"
               autocomplete="off">
        <p id="seriesSearchResult" class="muted" aria-live="polite"></p>
    </div>
"""

content = content.replace(
    heading,
    search_html + '\n    <h2 id="seriesHeading">Daftar seri tersimpan ({{ series|length }})</h2>',
    1,
)

content = content.replace(
    entry,
    """<section class="entry series-entry"
             data-search="{{ (item['series_code'] ~ ' ' ~ item['series_name'] ~ ' ' ~ item['verification_status'] ~ ' ' ~ (item['description'] or '') ~ ' ' ~ (item['verification_notes'] or ''))|lower|e }}">""",
    1,
)

content = content.replace(
    closing,
    """
<script>
(function () {
    const input = document.getElementById("seriesSearch");
    const cards = Array.from(document.querySelectorAll(".series-entry"));
    const result = document.getElementById("seriesSearchResult");
    const heading = document.getElementById("seriesHeading");
    const originalCount = cards.length;

    function filterSeries() {
        const keyword = input.value.trim().toLocaleLowerCase("id");
        let visible = 0;

        cards.forEach(function (card) {
            const text = card.dataset.search || "";
            const matches = text.includes(keyword);
            card.hidden = !matches;
            if (matches) visible++;
        });

        heading.textContent =
            "Daftar seri tersimpan (" + visible + " dari " +
            originalCount + ")";

        if (keyword) {
            result.textContent = visible
                ? visible + " seri cocok dengan pencarian."
                : "Tidak ada seri yang cocok. Coba kata kunci lain.";
        } else {
            result.textContent = originalCount + " seri tersedia.";
        }
    }

    input.addEventListener("input", filterSeries);
    filterSeries();
})();
</script>
</body>
""",
    1,
)

template.write_text(content, encoding="utf-8")
print("BERHASIL: pencarian Master Seri Jarum ditambahkan.")
print("Backup:", backup)
print("Jumlah kartu yang akan dicari: {{ series|length }}")
