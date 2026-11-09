import csv
from pathlib import Path

source = Path("tools/he800c_audit/source/he800c_in.txt")
out = Path(
    "tools/he800c_audit/staging/"
    "he800c_sections_11_2_to_11_8_candidates.csv"
)

if not source.is_file():
    raise SystemExit("GAGAL: sumber manual tidak ditemukan.")
if out.exists():
    raise SystemExit(f"File sudah ada; tidak ditimpa: {out}")

text = source.read_text(encoding="utf-8", errors="replace")
sections = [
    ("11-2. Skipped stitches", "11-2"),
    ("11-3. Uneven seams (1)", "11-3"),
    ("11-4. Uneven seams (2)", "11-4"),
    ("11-5. Uneven seams (3)", "11-5"),
    ("11-6. Uneven seams (4)", "11-6"),
    ("11-7. Uneven seams (5)", "11-7"),
    ("11-8. Uneven seams (6)", "11-8"),
]

for heading, section in sections:
    if heading not in text:
        raise SystemExit(f"GAGAL: judul sumber {section} tidak ditemukan.")

rows = [
    {
        "manual_section": "11-2",
        "manual_pages": "79-80",
        "proposed_title": "Jahitan loncat",
        "symptoms": "Jahitan tidak terbentuk secara konsisten karena beberapa tusukan terlewat.",
        "possible_causes": "Orientasi, pemasangan, kondisi, atau ukuran jarum; thread take-up spring; tekanan atau kesesuaian work clamp; rotary hook dan timing; tegangan benang atas; kelonggaran needle bar; lower thread clamp yang kotor atau rusak; needle plate; atau penjepitan material pada sambungan.",
        "operator_actions": "Matikan sakelar dan cabut kabel daya. Periksa pemasangan dan kondisi jarum, jalur benang, serta tegangan benang sesuai prosedur operator. Bersihkan sisa benang yang dapat dijangkau dengan aman tanpa membongkar mekanisme.",
        "technician_actions": "Periksa penyetelan thread take-up spring; tekanan dan kesesuaian work clamp; rotary hook, tinggi dan timing needle bar, celah jarum-hook 0,01–0,08 mm; kelonggaran needle bar; lower thread clamp/presser; needle plate; dan penjepitan sambungan. Ikuti semua penanda * pada manual.",
    },
    {
        "manual_section": "11-3",
        "manual_pages": "81",
        "proposed_title": "Jahitan tidak rata saat mulai menjahit",
        "symptoms": "Jahitan tidak rata pada awal proses menjahit.",
        "possible_causes": "Tinggi, timing, atau operasi upper thread trimmer; jumlah benang atas yang ditarik; tegangan benang bawah; tekanan pegas bobbin holder; posisi lower thread retainer; posisi bobbin presser; atau pemasangan bobbin.",
        "operator_actions": "Matikan sakelar dan cabut kabel daya sebelum pemeriksaan. Periksa pemasangan benang atas dan bobbin serta tegangan benang yang dapat disetel operator sesuai manual.",
        "technician_actions": "Periksa tinggi dan timing upper thread trimmer, operasi opening cam, thread take-up amount, pegas bobbin holder, posisi lower thread retainer dan bobbin presser. Penyetelan bertanda * hanya untuk teknisi berkualifikasi.",
    },
    {
        "manual_section": "11-4",
        "manual_pages": "82",
        "proposed_title": "Benang bawah terangkat saat mulai menjahit",
        "symptoms": "Ujung benang bawah menonjol di atas jahitan pada awal proses menjahit.",
        "possible_causes": "Jumlah benang yang ditahan lower thread retainer; timing pembukaan lower thread clamp; atau lower thread clamp/presser bengkok maupun sekrupnya kendur.",
        "operator_actions": "Matikan sakelar dan cabut kabel daya. Periksa pemasangan bobbin dan jalur benang bawah sesuai petunjuk operator.",
        "technician_actions": "Periksa jumlah benang yang ditahan, timing pembukaan lower thread clamp pada pergerakan feed 6–7 mm, kondisi clamp/presser, dan kekencangan sekrup. Penyetelan bertanda * hanya untuk teknisi berkualifikasi.",
    },
    {
        "manual_section": "11-5",
        "manual_pages": "82",
        "proposed_title": "Jahitan terangkat dan tidak mengencang saat mulai menjahit",
        "symptoms": "Jahitan terangkat dan tidak mengencang pada awal proses menjahit.",
        "possible_causes": "Timing pembukaan bertahap upper thread trimmer; operasi opening cam; atau jumlah benang atas yang ditarik.",
        "operator_actions": "Matikan sakelar dan cabut kabel daya. Periksa pemasangan benang atas sesuai manual.",
        "technician_actions": "Periksa timing pembukaan upper thread trimmer pada pergerakan feed sekitar 1,5–2,5 mm, pelumasan inclined face opening cam, dan thread take-up amount. Penyetelan bertanda * hanya untuk teknisi berkualifikasi.",
    },
    {
        "manual_section": "11-6",
        "manual_pages": "83",
        "proposed_title": "Jarak jahitan tidak rata saat mulai menjahit",
        "symptoms": "Benang menggumpal pada awal jahitan, kemudian jarak jahitan tiba-tiba membesar setelah sekitar 5–6 mm.",
        "possible_causes": "Timing pembukaan lower thread clamp.",
        "operator_actions": "Matikan mesin dan hentikan penggunaan jika gejala berulang. Catat kondisi saat gejala terjadi; jangan menyetel timing mekanisme.",
        "technician_actions": "Periksa dan setel timing pembukaan lower thread clamp sesuai manual. Penyetelan bertanda * hanya untuk teknisi berkualifikasi.",
    },
    {
        "manual_section": "11-7",
        "manual_pages": "83",
        "proposed_title": "Bentuk lengkung jahitan tidak sempurna",
        "symptoms": "Bentuk lengkung jahitan tidak terbentuk dengan baik.",
        "possible_causes": "Tegangan benang atas zigzag; pembukaan cakram tegangan zigzag atau tension release solenoid; tegangan dan pemasangan benang bawah; pemasangan benang atas; pola purl/whip stitch; atau timing pelepasan tegangan.",
        "operator_actions": "Matikan sakelar dan cabut kabel daya. Periksa pemasangan benang atas dan bawah. Verifikasi pola serta parameter sesuai prosedur operator dan spesifikasi pola yang digunakan.",
        "technician_actions": "Periksa pembukaan cakram tegangan zigzag dan tension release solenoid. Verifikasi parameter 53 serta timing parameter 54–57 berdasarkan pola dan prosedur manual.",
    },
    {
        "manual_section": "11-8",
        "manual_pages": "84",
        "proposed_title": "Jahitan tidak sempurna di area tack depan atau belakang",
        "symptoms": "Masalah jahitan terjadi di sekitar front tack atau rear tack.",
        "possible_causes": "Timing pelepasan tegangan; pemasangan benang atas/bawah; pembukaan cakram tegangan zigzag; tension release solenoid; atau operasi upper thread trimmer/opening cam.",
        "operator_actions": "Matikan sakelar dan cabut kabel daya. Periksa pemasangan benang atas dan bawah. Catat apakah masalah muncul pada front tack, rear tack, atau keduanya.",
        "technician_actions": "Periksa timing parameter 54–57, pembukaan cakram tegangan zigzag, tension release solenoid, dan pelumasan inclined face opening cam. Ikuti penanda * pada manual.",
    },
]

fields = [
    "manual_section", "manual_pages", "proposed_title", "symptoms",
    "possible_causes", "operator_actions", "technician_actions",
    "source", "status"
]

for row in rows:
    row["source"] = (
        f"Brother HE-800C Instruction Manual, section "
        f"{row['manual_section']}, pages {row['manual_pages']}"
    )
    row["status"] = "KANDIDAT BELUM DISETUJUI"

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

with out.open(encoding="utf-8-sig", newline="") as f:
    check = list(csv.DictReader(f))

assert len(check) == 7
assert len({r["manual_section"] for r in check}) == 7
assert all(r["status"] == "KANDIDAT BELUM DISETUJUI" for r in check)

print("CSV kandidat berhasil dibuat.")
print("Jumlah kandidat:", len(check))
print("Status seluruh kandidat: KANDIDAT BELUM DISETUJUI")
print("File:", out)
print("Database tidak dibuka dan tidak diubah.")
