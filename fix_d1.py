from pathlib import Path
p = Path("templates/component_detail.html")
s = p.read_text()
old = "url_for(static, filename=images/mechanisms/brother/bas311hn/d1-work-clamp-lifter.png)"
new = "url_for('static', filename='images/mechanisms/brother/bas311hn/d1-work-clamp-lifter.png')"
n = s.count(old)
print("Alamat salah ditemukan:", n)
assert n == 2, "Dibatalkan: jumlah alamat tidak sesuai."
p.write_text(s.replace(old, new))
print("Kedua alamat gambar D1 berhasil diperbaiki.")
