import csv
import os
from collections import Counter

OUT = "audit-kelengkapan/draf_brother_bas311hn_03s.csv"
SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/"
    "-/media/ap2/ism/pdf/manual-download/"
    "bas311hn_326h_in.pdf?rev=-1"
)
SOURCE = SOURCE_URL + " | Manual BAS-311HN/BAS-326H; DRAF_PERLU_VERIFIKASI_TEKNIS"

rows = []

def add(code, problem, symptoms, cause, solution, safety="Matikan mesin sebelum pemeriksaan."):
    rows.append({
        "machine_id": 227,
        "problem": problem,
        "symptoms": symptoms,
        "possible_cause": cause,
        "solution": solution,
        "safety_notes": safety,
        "source": SOURCE,
        "code": code,
    })

# Kode error yang terbaca dari daftar manual.
errors = [
("E010","STOP switch ditekan","Kode E010 muncul","STOP switch ditekan","Tekan RESET untuk menghapus error."),
("E011","STOP switch ditekan","Kode E011 muncul","STOP switch ditekan","Tekan RESET; ikuti petunjuk panel/manual sebelum melanjutkan."),
("E012","STOP switch ditekan","Kode E012 muncul","STOP switch ditekan","Tekan RESET, lalu tekan start switch untuk menggerakkan feed ke posisi home."),
("E015","Gangguan STOP switch saat mesin dinyalakan","Kode E015 muncul","STOP switch ditekan saat power-on atau koneksi switch bermasalah","Matikan daya; periksa konektor P9 pada main PCB oleh teknisi."),
("E016","Gangguan koneksi STOP switch","Kode E016 muncul","Koneksi STOP switch bermasalah","Matikan daya; periksa konektor P9 pada main PCB oleh teknisi."),
("E020","Start switch ditekan sebelum work clamp turun","Kode E020 muncul","Work clamp belum diturunkan","Turunkan work clamp sebelum menekan start."),
("E025","Start switch aktif saat power-on","Kode E025 muncul","Start switch tertahan saat mesin dinyalakan","Lepaskan switch; bila menggunakan foot switch dan masalah berulang, periksa setelan langkah sesuai manual."),
("E035","Work clamp switch aktif saat power-on","Kode E035 muncul","Work clamp switch tertahan saat mesin dinyalakan","Lepaskan switch; periksa setelan langkah sesuai manual jika diperlukan."),
("E050","Posisi kepala mesin miring terdeteksi setelah power-on","Kode E050 muncul","Kepala mesin tidak pada posisi awal atau koneksi terkait bermasalah","Matikan daya; kembalikan kepala ke posisi awal dan minta teknisi memeriksa konektor P14."),
("E051","Kepala mesin miring terdeteksi saat operasi","Kode E051 muncul","Head tilt terdeteksi saat mesin berjalan","Matikan daya; minta teknisi memeriksa konektor P14."),
("E055","Kepala mesin miring terdeteksi saat power-on","Kode E055 muncul","Kepala mesin belum pada posisi awal","Matikan daya; kembalikan kepala ke posisi awal dan periksa konektor P14 melalui teknisi."),
("E064","Panel sentuh aktif saat power-on","Kode E064 muncul","Panel sentuh tersentuh saat mesin dinyalakan","Lepaskan sentuhan dari panel."),
("E065","Tombol panel LCD aktif saat power-on","Kode E065 muncul","Tombol tertahan atau tombol mengalami gangguan","Lepaskan tombol; jika berulang, minta teknisi memeriksa panel."),
("E110","Poros atas tidak berhenti di posisi jarum atas","Kode E110 muncul","Posisi berhenti poros atas tidak sesuai","Putar pulley sesuai petunjuk manual sampai error hilang."),
("E111","Poros atas gagal berhenti di posisi jarum atas","Kode E111 muncul","Gangguan motor/sinkronisasi atau konektor terkait","Matikan daya; teknisi memeriksa konektor P11/P1 motor PCB dan P6 main PCB."),
("E121","Pemotongan benang tidak selesai","Kode E121 muncul","Mata pisau tetap/gerak rusak atau aus","Matikan daya; periksa mata pisau tetap dan pisau gerak."),
("E130","Motor poros atas berhenti atau synchronizer bermasalah","Kode E130 muncul","Motor bermasalah, mesin macet, atau synchronizer rusak","Matikan daya; periksa kemungkinan mesin terkunci. Pemeriksaan konektor/motor dilakukan teknisi."),
("E131","Synchronizer tidak tersambung benar","Kode E131 muncul","Koneksi synchronizer bermasalah","Matikan daya; minta teknisi memeriksa konektor P11 pada motor PCB."),
("E132","Gangguan operasi motor poros atas","Kode E132 muncul","Gangguan motor atau konektor terkait","Matikan daya; minta teknisi memeriksa konektor motor dan papan kontrol sesuai manual."),
("E133","Posisi berhenti motor poros atas tidak tepat","Kode E133 muncul","Posisi berhenti motor tidak sesuai","Matikan daya; teknisi memeriksa konektor motor dan papan kontrol."),
("E150","Motor poros atas terlalu panas","Kode E150 muncul","Motor panas atau sensor suhu bermasalah; siklus pendek berulang dapat memicu error","Matikan daya dan periksa motor melalui teknisi; hindari siklus pendek berulang."),
("E200","Posisi home motor feed X tidak terdeteksi","Kode E200 muncul","Motor X atau sensor posisi home/konektornya bermasalah","Matikan daya; teknisi memeriksa konektor P17, P21, dan P8 pada main PCB."),
("E201","Motor feed X berhenti karena gangguan","Kode E201 muncul","Ada hambatan atau masalah gerak sumbu X","Matikan daya; periksa hambatan mekanis dan konektor P17/P21 melalui teknisi."),
("E204","Motor feed X berhenti saat menjahit","Kode E204 muncul","Gangguan gerak sumbu X","Matikan daya; periksa area gerak X dan konektor terkait."),
("E205","Motor feed X berhenti saat menuju posisi awal jahit","Kode E205 muncul","Gangguan gerak sumbu X","Matikan daya; periksa area gerak X dan konektor terkait."),
("E206","Motor feed X berhenti saat test feeding","Kode E206 muncul","Gangguan gerak sumbu X","Matikan daya; periksa area gerak X dan konektor terkait."),
("E210","Posisi home motor feed Y tidak terdeteksi","Kode E210 muncul","Motor Y atau sensor posisi home/konektornya bermasalah","Matikan daya; teknisi memeriksa konektor P18, P22, dan P8 pada main PCB."),
("E211","Motor feed Y berhenti karena gangguan","Kode E211 muncul","Ada hambatan atau masalah gerak sumbu Y","Matikan daya; periksa hambatan mekanis dan konektor P18/P22 melalui teknisi."),
("E214","Motor feed Y berhenti saat menjahit","Kode E214 muncul","Gangguan gerak sumbu Y","Matikan daya; periksa area gerak Y dan konektor terkait."),
("E215","Motor feed Y berhenti saat menuju posisi awal jahit","Kode E215 muncul","Gangguan gerak sumbu Y","Matikan daya; periksa area gerak Y dan konektor terkait."),
("E216","Motor feed Y berhenti saat test feeding","Kode E216 muncul","Gangguan gerak sumbu Y","Matikan daya; periksa area gerak Y dan konektor terkait."),
("E230","Motor feed berhenti karena gangguan","Kode E230 muncul","Beban/operasi feed berlebihan atau setelan material tidak sesuai","Kurangi kecepatan jahit atau gunakan setelan untuk material berat sesuai manual."),
("E300","Posisi home work clamp tidak terdeteksi","Kode E300 muncul","Motor work clamp atau sensor home/konektornya bermasalah","Matikan daya; teknisi memeriksa konektor P19, P23, dan P8 pada main PCB."),
("E301","Posisi atas/bawah work clamp tidak terdeteksi","Kode E301 muncul","Gangguan gerak vertikal work clamp","Matikan daya; periksa gerak work clamp dan konektor P19/P23 melalui teknisi."),
("E400","Gangguan komunikasi main PCB dan panel saat power-on","Kode E400 muncul","Komunikasi papan kontrol/panel terganggu","Matikan daya; teknisi memeriksa konektor panel dan konektor P2/P3 motor PCB."),
("E401","Gangguan komunikasi main PCB dan motor PCB saat power-on","Kode E401 muncul","Komunikasi antar papan terganggu","Matikan daya; teknisi memeriksa konektor sesuai manual."),
("E410","Gangguan komunikasi main PCB dan panel","Kode E410 muncul","Komunikasi antar papan terganggu","Matikan daya lalu nyalakan kembali; jika berulang, teknisi memeriksa konektor terkait."),
("E411","Gangguan komunikasi main PCB dan motor PCB","Kode E411 muncul","Komunikasi antar papan terganggu","Matikan daya lalu nyalakan kembali; jika berulang, teknisi memeriksa konektor terkait."),
("E420","Media penyimpanan tidak terpasang","Kode E420 muncul","Media penyimpanan belum dimasukkan","Tekan RESET; masukkan media penyimpanan yang sesuai lalu coba kembali."),
("E421","Nomor program tidak valid atau data tidak tersedia","Kode E421 muncul","Data program tidak ada pada media penyimpanan","Tekan RESET; pastikan data untuk nomor program tersedia."),
("E422","Gagal membaca media penyimpanan","Kode E422 muncul","Data atau media penyimpanan bermasalah","Tekan RESET; periksa data pada media penyimpanan."),
("E424","Ruang media penyimpanan tidak cukup","Kode E424 muncul","Media penyimpanan penuh","Tekan RESET dan gunakan media penyimpanan lain."),
("E425","Gagal menulis ke media penyimpanan","Kode E425 muncul","Media bermasalah atau terkunci tulis","Tekan RESET; periksa media dan status write-protect."),
("E427","Program siklus yang dirujuk telah dihapus","Kode E427 muncul","Program siklus tidak lagi tersedia","Tekan RESET dan buat ulang program siklus."),
("E430","Data tidak dapat dicadangkan ke flash memory main PCB","Kode E430 muncul","Gangguan penyimpanan flash","Matikan daya lalu nyalakan kembali; jika berulang, hubungi teknisi."),
("E440","Data tidak dapat dicadangkan ke EEPROM main PCB","Kode E440 muncul","Gangguan penyimpanan EEPROM","Matikan daya lalu nyalakan kembali; jika berulang, hubungi teknisi."),
("E450","Pemilihan model tidak dapat dibaca dari memori kepala mesin","Kode E450 muncul","Memori kepala mesin atau koneksi terkait bermasalah","Matikan daya; teknisi memeriksa konektor P16 pada main PCB."),
("E452","Memori kepala mesin tidak tersambung","Kode E452 muncul","Koneksi memori kepala mesin bermasalah","Matikan daya; teknisi memeriksa konektor P16. Gunakan backup hanya sesuai manual."),
("E453","Data memori kepala mesin bermasalah","Kode E453 muncul","Data memori kepala mesin tidak valid","Matikan daya lalu nyalakan kembali; jika berulang, hubungi teknisi."),
("E471","Nomor program internal tidak valid atau data tidak tersedia","Kode E471 muncul","Data program tidak ada di memori internal","Pastikan data tersedia untuk nomor program tersebut."),
("E474","Memori internal penuh sehingga penyalinan gagal","Kode E474 muncul","Memori internal penuh","Tekan RESET dan hapus data jahit yang tidak diperlukan sesuai prosedur."),
("E500","Data jahit melampaui area jahit karena rasio pembesaran","Kode E500 muncul","Setelan rasio pembesaran tidak sesuai","Atur ulang rasio pembesaran; tekan RESET."),
("E502","Pitch data melebihi maksimum 12,7 mm","Kode E502 muncul","Rasio pembesaran membuat pitch data terlalu besar","Atur ulang rasio pembesaran; tekan RESET."),
("E510","Kesalahan data jahit","Kode E510 muncul","Data jahit rusak atau gagal dibaca/direvisi","Tekan RESET; periksa dan revisi data jahit."),
("E511","Data pola tidak memiliki end code","Kode E511 muncul","End code tidak dimasukkan ke data pola","Tambahkan end code pada data pola; tekan RESET."),
("E512","Jumlah jahitan melebihi batas","Kode E512 muncul","Jumlah stitch terlalu banyak","Periksa dan sesuaikan data pola."),
("E520","Nomor output extended option sudah digunakan","Kode E520 muncul","Nomor output ganda","Ubah nomor output; jika fitur tidak dipakai, inisialisasi data terkait sesuai manual."),
("E581","File memory switch tidak dapat dibaca atau model tidak cocok","Kode E581 muncul","Model data berbeda dari model mesin","Tekan RESET; gunakan data untuk model mesin yang sesuai."),
("E582","Versi memory switch tidak cocok","Kode E582 muncul","Versi data berbeda","Tekan RESET; gunakan data dengan versi yang sesuai."),
("E583","Versi user program tidak cocok","Kode E583 muncul","Versi program berbeda","Tekan RESET; gunakan data dengan versi yang sesuai."),
("E600","Benang atas putus","Kode E600 muncul","Benang atas putus","Pasang ulang benang atas; jahitan dapat dilanjutkan setelah prosedur manual."),
("E670","Gangguan detektor benang bawah","Kode E670 muncul","Detektor benang bawah bermasalah","Matikan daya; periksa detektor melalui teknisi."),
("E700","Tegangan suplai meningkat abnormal","Kode E700 muncul","Tegangan input tidak normal","Matikan mesin; minta teknisi memeriksa tegangan input."),
("E701","Tegangan penggerak motor poros atas meningkat abnormal","Kode E701 muncul","Tegangan drive tidak normal","Matikan mesin; pemeriksaan kelistrikan dilakukan teknisi."),
("E705","Tegangan suplai turun abnormal","Kode E705 muncul","Tegangan input tidak normal","Matikan mesin; minta teknisi memeriksa tegangan input."),
("E710","Arus motor poros atas abnormal","Kode E710 muncul","Motor bermasalah atau mesin mengalami hambatan","Matikan daya; teknisi memeriksa mekanisme dan konektor motor."),
("E711","Arus motor pulse abnormal","Kode E711 muncul","Gangguan operasi work clamp atau motor pulse","Matikan daya; periksa mekanisme work clamp melalui teknisi."),
("E730","Input error eksternal AIRSW","Kode E730 muncul","Tekanan udara tidak sesuai","Matikan mesin; periksa tekanan udara sesuai spesifikasi manual."),
("E860","Program kontrol utama tidak tersedia","Kode E860 muncul","Program kontrol utama tidak ada","Pemulihan program dilakukan teknisi menggunakan prosedur resmi."),
("E870","Program kontrol panel tidak tersedia","Kode E870 muncul","Program kontrol panel tidak ada","Pemulihan program dilakukan teknisi menggunakan prosedur resmi."),
("E880","Permintaan pembaruan versi tidak dapat diterima","Kode E880 muncul","Proses pembaruan versi terganggu","Matikan daya lalu nyalakan kembali; jika berulang, hubungi teknisi."),
("E881","Pembaruan versi tidak selesai normal","Kode E881 muncul","Proses pembaruan versi gagal","Ulangi prosedur pembaruan resmi melalui teknisi."),
("E883","Program kontrol tidak ada di media penyimpanan","Kode E883 muncul","File program tidak berada di folder yang benar","Pastikan file berada di folder yang ditentukan manual."),
("E884","File program kontrol bermasalah","Kode E884 muncul","File program tidak sesuai","Gunakan file yang benar dari sumber resmi."),
]

for item in errors:
    add(*item)

# Troubleshooting umum dari bagian 9 manual; bukan kode error.
general = [
("","Mesin tidak mulai saat dinyalakan dan foot switch ditekan","Mesin tidak bergerak","Machine head switch tidak bekerja, kabel terlepas, atau posisi switch salah","Periksa kabel dan posisi switch; penggantian/penyetelan dilakukan teknisi."),
("","Work clamp tidak bekerja","Penjepit kain tidak bergerak","Air cock tertutup, tekanan udara lemah, atau speed controller terlalu rapat","Buka air cock; periksa regulator sekitar 0,5 MPa dan setelan speed controller sesuai manual."),
("","Thread wiper tidak bekerja","Pembersih benang tidak bergerak","Setelan thread wiper OFF","Atur thread wiper ke ON pada panel sesuai manual."),
("","Work clamp tidak naik ke tinggi maksimum","Gerak naik penjepit terbatas","Posisi tuas atau stopper work clamp tidak tepat","Periksa dan setel posisi mekanisme sesuai manual."),
("","Tekanan work clamp lemah","Penjepit kain kurang kuat","Tekanan udara lemah pada model pneumatic","Periksa regulator; manual menyebut sekitar 0,5 MPa untuk spesifikasi pneumatic."),
("","Tekanan work clamp tidak merata depan-belakang","Penjepitan kain tidak seragam","Work clamp miring","Periksa dan sesuaikan kemiringan work clamp."),
("","Thread wiper bekerja tidak benar","Thread wiper mengganggu jarum atau geraknya tidak tepat","Tinggi, langkah, atau posisi thread wiper salah","Setel tinggi, langkah operasi, dan posisi sesuai manual."),
("","Gulungan benang bawah tidak merata","Benang pada bobbin menumpuk di satu sisi","Tinggi tension bobbin winder tidak tepat","Setel tinggi tension assembly bobbin winder."),
("","Jumlah benang bawah tergulung tidak sesuai","Bobbin terlalu sedikit atau terlalu banyak benang","Posisi bobbin presser tidak tepat","Setel posisi bobbin presser."),
("","Jahitan loncat","Sebagian tusukan tidak terbentuk","Jarum bengkok/tidak sesuai, pemasangan salah, timing atau clearance hook tidak tepat, atau material berkibar","Periksa jarum, pemasangan, needle guard, clearance, timing, dan penahanan material sesuai manual."),
("","Benang atas terurai pada awal jahitan","Ujung benang terurai saat mulai menjahit","Ujung benang atas terlalu pendek, benang bawah keluar terlalu sedikit, atau kecepatan awal terlalu tinggi","Sesuaikan panjang ujung benang dan setelan sesuai manual; manual menyebut sekitar 42 mm untuk panjang ujung benang atas."),
("","Benang atas putus","Benang atas terputus saat menjahit","Tegangan berlebihan, jarum/timing tidak tepat, burr pada jalur benang, atau panas akibat kecepatan","Periksa jalur benang, jarum, timing, dan tegangan; lakukan perbaikan mekanis oleh teknisi."),
("","Benang bawah putus","Benang bobbin terputus","Tegangan benang bawah berlebihan atau bagian hook/bobbin case rusak","Periksa tegangan dan kondisi komponen; ganti atau perbaiki komponen jika diperlukan."),
("","Jarum patah","Jarum patah selama menjahit","Jarum bengkok/tidak sesuai, bersentuhan dengan hook, atau timing salah","Ganti jarum dan minta teknisi memeriksa clearance serta timing."),
("","Benang atas tidak terpotong","Benang atas tertinggal setelah trimming","Pisau tumpul, timing salah, atau movable knife tidak menangkap benang","Periksa pisau dan setelan trimming sesuai manual."),
("","Benang bawah tidak terpotong","Benang bobbin tetap tersambung","Tegangan benang bawah terlalu lemah","Setel tegangan sesuai manual."),
("","Tegangan jahitan benang atas tidak baik","Jahitan longgar atau hasil tidak rata","Tegangan atas/bawah tidak seimbang, komponen aus, atau pelumasan hook kurang","Periksa tegangan, kondisi komponen, dan pelumasan sesuai manual."),
("","Tegangan benang bawah tidak baik","Jahitan bawah longgar","Tegangan benang bawah terlalu lemah atau tegangan atas terlalu kuat","Sesuaikan tegangan berdasarkan prosedur manual."),
("","Hasil jahitan sisi bawah kurang baik pada awal jahitan","Jahitan awal tidak rapi","Ujung benang atas setelah trimming terlalu panjang","Sesuaikan panjang ujung benang setelah trimming; manual menyebut sekitar 42 mm."),
]

for item in general:
    add(*item, safety=(
        "Matikan mesin dan cabut kabel listrik sebelum pemeriksaan mekanis. "
        "Pekerjaan kelistrikan, konektor internal, timing, dan perbaikan komponen "
        "dilakukan teknisi yang kompeten."
    ))

fields = [
    "machine_id", "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source", "code"
]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

codes = [r["code"] for r in rows if r["code"]]
duplicates = [c for c, n in Counter(codes).items() if n > 1]
required_missing = [
    i + 2 for i, r in enumerate(rows)
    if not r["problem"].strip() or not r["source"].strip()
]
print("CSV dibuat:", OUT)
print("Total baris:", len(rows))
print("Baris kode error:", len(codes))
print("Kasus tanpa kode error:", sum(not r["code"] for r in rows))
print("Kode duplikat:", duplicates)
print("Baris dengan problem/source kosong:", required_missing)
print("Kode kosong pada kasus umum:", sum(not r["code"] for r in rows))
print("Status: DRAF_PERLU_VERIFIKASI_TEKNIS")
print("Database tidak dibuka atau diubah oleh skrip ini.")
