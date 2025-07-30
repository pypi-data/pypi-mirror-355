# cloudku-uploader

`cloudku-uploader` adalah pustaka Python untuk mengunggah file ke layanan [cloudkuimages.guru](https://cloudkuimages.guru). Pustaka ini menangani proses `multipart/form-data` secara otomatis, mendukung tanggal kedaluwarsa, dan akan mencoba beberapa endpoint jika terjadi kegagalan.

## ✨ Fitur

- Unggah file ke cloudkuimages.guru
- Dukungan pengaturan tanggal kedaluwarsa (expire date)
- Coba alternatif endpoint jika endpoint utama gagal
- Konfigurasi header otomatis

## 📦 Instalasi

```bash
pip install cloudku-uploader
