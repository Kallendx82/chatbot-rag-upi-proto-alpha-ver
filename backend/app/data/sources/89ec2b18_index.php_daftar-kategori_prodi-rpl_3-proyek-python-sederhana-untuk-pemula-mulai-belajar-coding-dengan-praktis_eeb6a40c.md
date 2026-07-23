# 3 Proyek Python Sederhana untuk Pemula: Mulai Belajar Coding dengan Praktis

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-rpl/3-proyek-python-sederhana-untuk-pemula-mulai-belajar-coding-dengan-praktis

3 Proyek Python Sederhana untuk Pemula: Mulai Belajar Coding dengan Praktis
24 April 2025
Admin RPL
Prodi RPL
3 Proyek Python Sederhana untuk Pemula: Mulai Belajar Coding dengan Praktis

Python adalah salah satu bahasa pemrograman yang paling populer untuk pemula karena sintaksnya sederhana dan mudah dipahami. Untuk memulai perjalanan coding, membuat proyek sederhana adalah cara terbaik untuk belajar sambil berlatih. Artikel ini akan membahas 5 proyek Python yang cocok untuk pemula.

1. Kalkulator Sederhana

Deskripsi:
Proyek ini mengajarkan cara menggunakan operasi dasar seperti penjumlahan, pengurangan, perkalian, dan pembagian.

Fitur Utama:

Input angka dari pengguna.
Memilih operasi matematika.
Menampilkan hasil akhir.

Manfaat:
Pemula dapat mempelajari konsep fungsi, input/output, dan logika dasar dalam Python.

Kode Contoh:

def kalkulator():
    print("Pilih operasi:\n1. Tambah\n2. Kurang\n3. Kali\n4. Bagi")
    pilihan = input("Masukkan pilihan (1/2/3/4): ")
    angka1 = float(input("Masukkan angka pertama: "))
    angka2 = float(input("Masukkan angka kedua: "))

    if pilihan == '1':
        print(f"Hasil: {angka1 + angka2}")
    elif pilihan == '2':
        print(f"Hasil: {angka1 - angka2}")
    elif pilihan == '3':
        print(f"Hasil: {angka1 * angka2}")
    elif pilihan == '4':
        print(f"Hasil: {angka1 / angka2}")
    else:
        print("Pilihan tidak valid.")

kalkulator()

2. Game Tebak Angka

Deskripsi:
Pengguna mencoba menebak angka acak yang dihasilkan oleh program dalam beberapa percobaan.

Fitur Utama:

Angka acak dihasilkan menggunakan pustaka random.
Memberi petunjuk apakah angka yang ditebak lebih tinggi atau lebih rendah.

Manfaat:
Mengenalkan pustaka bawaan Python dan penggunaan loop.

Kode Contoh:

import random

def tebak_angka():
    angka_rahasia = random.randint(1, 100)
    percobaan = 0

    print("Tebak angka antara 1 hingga 100!")

    while True:
        tebakan = int(input("Masukkan tebakanmu: "))
        percobaan += 1

        if tebakan < angka_rahasia:
            print("Terlalu kecil!")
        elif tebakan > angka_rahasia:
            print("Terlalu besar!")
        else:
            print(f"Selamat! Kamu menebak dalam {percobaan} percobaan.")
            break

tebak_angka()

3. Pengelola Daftar Tugas (To-Do List)

Deskripsi:
Proyek ini memungkinkan pengguna untuk menambahkan, menghapus, dan melihat tugas dalam daftar.

Fitur Utama:

Menambahkan tugas baru.
Menghapus tugas tertentu.
Menampilkan semua tugas.

Manfaat:
Memahami penggunaan list, fungsi, dan manipulasi data.

Kode Contoh:

def to_do_list():
    daftar_tugas = []

    while True:
        print("\nMenu:")
        print("1. Tambah Tugas")
        print("2. Hapus Tugas")
        print("3. Lihat Daftar Tugas")
        print("4. Keluar")
        pilihan = input("Pilih opsi: ")

        if pilihan == '1':
            tugas = input("Masukkan tugas: ")
            daftar_tugas.append(tugas)
            print("Tugas berhasil ditambahkan!")
        elif pilihan == '2':
            tugas = input("Masukkan tugas yang ingin dihapus: ")
            if tugas in daftar_tugas:
                daftar_tugas.remove(tugas)
                print("Tugas berhasil dihapus!")
            else:
                print("Tugas tidak ditemukan.")
        elif pilihan == '3':
            print("Daftar Tugas:")
            for i, tugas in enumerate(daftar_tugas, 1):
                print(f"{i}. {tugas}")
        elif pilihan == '4':
            print("Keluar dari program.")
            break
        else:
            print("Pilihan tidak valid.")

to_do_list()

Kesimpulan

Dengan mengerjakan proyek-proyek sederhana ini, Anda tidak hanya mempraktikkan dasar-dasar Python tetapi juga mempersiapkan diri untuk tantangan pemrograman yang lebih kompleks. Mulailah dari proyek yang paling menarik bagi Anda, dan nikmati proses belajar!

Dilihat: 3523
Previous article: Bahasa Pemrograman Python Sebelum
Next article: Mengoptimalkan Kinerja Program dengan Python: Panduan Praktis untuk Developer Berikut
FaLang translation system by Faboba
