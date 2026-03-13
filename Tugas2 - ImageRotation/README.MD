# Tugas 2 Pengolahan Citra Digital — Rotasi Citra dengan Efek Swirl

> **Mata Kuliah:** Pengolahan Citra Digital — Grup A  
> **Dosen Pengampu:** Aditya Wikan Mahastama  

---

## 📋 Rangkuman Tugas

Program ini mengimplementasikan **Rotasi Citra dengan Efek *Swirl*** (*melintir*), yakni sebuah efek distorsi di mana setiap piksel diputar dengan sudut yang bergantung pada jaraknya dari pusat citra — sehingga menghasilkan tampilan seperti pusaran/uliran.

### Konsep Utama

| Konsep | Penjelasan |
|---|---|
| **Titik Pusat Rotasi** | Tengah citra (`cx`, `cy`) |
| **Rumus Sudut Rotasi** | `θ = d(P, centre) / 8` (dalam derajat), di mana `d` adalah jarak piksel ke pusat |
| **Arah Rotasi** | Searah jarum jam |
| **Batas Ukuran Input** | Maksimal 720×720 piksel (otomatis di-*resize* jika lebih besar) |

### Dua Mode Pemrosesan

1. **Rotasi Tanpa Interpolasi** — menggunakan *forward mapping*: setiap piksel sumber dipetakan ke posisi barunya. Piksel yang tidak terpetakan dibiarkan kosong (putih).

2. **Rotasi Dengan Interpolasi** — menggunakan *backward mapping* dengan **interpolasi bilinear** via `cv2.remap`. Untuk setiap piksel di citra tujuan, nilai warnanya dihitung dari piksel-piksel tetangga di citra sumber, menghasilkan gambar yang padat, halus, dan bebas lubang.

---

## 👥 Detail Anggota Kelompok

| No. | Nama | NIM |
|-----|------|-----|
| 1 | Putu Gde Kenzie Carlen Mataram | 71230994 |
| 2 | Edrian Sepriadi Irawan | 71231011 |
| 3 | Bernadus Xaverius Hitipeuw | 71231018 |

---

## 🖼️ Tampilan Antarmuka Aplikasi (UI)

Aplikasi ini dibangun menggunakan **Tkinter** dengan tata letak tiga kolom yang menampilkan citra asli dan kedua hasil rotasi secara berdampingan. Terdapat dua tombol utama: **"Pilih Gambar"** di bagian atas dan **"Simpan Hasil Rotasi"** di bagian bawah.

---

### 1. Tampilan Awal

![Tampilan awal aplikasi](img/gui1.png)

Saat aplikasi pertama kali dibuka, ketiga panel preview (**Citra Asli**, **Tanpa Interpolasi**, **Dengan Interpolasi**) masih kosong/blank. Hanya label nama panel yang terlihat. Tombol **"Pilih Gambar"** aktif dan siap diklik, sedangkan tombol **"Simpan Hasil Rotasi"** belum dapat digunakan.

---

### 2. Tampilan Saat Memilih Gambar

![Tampilan saat dialog pemilihan file terbuka](img/gui2.png)

Ketika tombol **"Pilih Gambar"** diklik, dialog file explorer sistem operasi akan muncul. Pengguna dapat menelusuri direktori dan memilih file gambar berekstensi **`.jpg`, `.jpeg`,** atau **`.png`**. Setelah file dipilih dan tombol **"Open"** ditekan, aplikasi langsung memulai pemrosesan rotasi secara otomatis.

---

### 3. Tampilan Setelah Pemrosesan Selesai

![Tampilan setelah hasil rotasi ditampilkan](img/gui3.png)

Setelah pemrosesan selesai, ketiga panel terisi penuh:
- **Panel kiri — Citra Asli:** menampilkan gambar input tanpa modifikasi.
- **Panel tengah — Tanpa Interpolasi:** hasil rotasi *swirl* menggunakan *forward mapping*; terlihat ada area piksel kosong (putih) akibat celah pemetaan.
- **Panel kanan — Dengan Interpolasi:** hasil rotasi *swirl* menggunakan *backward mapping + interpolasi bilinear*; gambar tampak padat, halus, dan bebas lubang.

Tombol **"Simpan Hasil Rotasi"** kini aktif dan dapat diklik untuk menyimpan kedua gambar hasil ke direktori pilihan pengguna.

### Contoh Hasil Pemrosesan

| Citra Asli | Tanpa Interpolasi | Dengan Interpolasi |
|:---:|:---:|:---:|
| ![Citra Asli](img/input1.jpg) | ![Tanpa Interpolasi](img/input1_tanpa_interpolasi.jpg) | ![Dengan Interpolasi](img/input1_dengan_interpolasi.jpg) |

| Input original | *Forward mapping* (ada piksel kosong/putih) | *Backward mapping + bilinear* (hasil halus & padat) |

---

## 🚀 Cara Menjalankan Aplikasi

### Cara 1 — Melalui File Executable (`.exe`) ✅ Direkomendasikan

Aplikasi sudah di-*package* menjadi `.exe` sehingga **tidak memerlukan instalasi Python atau library apapun**.

1. Klik ganda pada file **`app_gui.exe`**.
2. Klik tombol **"Pilih Gambar"** → pilih file gambar berekstensi `.jpg` atau `.png`.
3. Tunggu proses selesai. Ketiga panel (Asli, Tanpa Interpolasi, Dengan Interpolasi) akan tampil otomatis.
4. Klik tombol **"Simpan Hasil Rotasi"** → pilih folder tujuan → kedua gambar hasil tersimpan secara otomatis.

---

### Cara 2 — Melalui Python (Mode GUI)

**Prasyarat:** Python 3.x dengan library berikut terinstal.

```bash
pip install opencv-python Pillow
```

**Jalankan aplikasi:**

```bash
python app_gui.py
```

---

### Cara 3 — Melalui Terminal (Mode Headless / Tanpa GUI)

Berguna untuk memproses citra langsung dari *command line* tanpa membuka jendela GUI.

```bash
python imgRotation.py -i <path_ke_gambar_input>
```

**Contoh:**
```bash
python imgRotation.py -i foto_saya.jpg
```

Output akan disimpan otomatis sebagai:
- `hasil_tanpa_interpolasi.jpg`
- `hasil_dengan_interpolasi.jpg`

---

## 📁 Struktur File Proyek

```
Tugas2/
├── app_gui.py              # Antarmuka grafis (GUI) utama — Tkinter
├── imgRotation.py          # Logika pemrosesan rotasi & interpolasi citra
├── app_gui.exe             # File executable (siap pakai, tanpa install Python)
├── img/                   # Aset dokumentasi (gambar untuk README)
│   ├── app_gui_mockup.png
│   ├── input.jpg
│   ├── tanpa_interpolasi.jpg
│   └── dengan_interpolasi.jpg
└── README.MD               # Dokumentasi proyek 
```