import os, django
from decimal import Decimal
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from laporan_keuangan.models import Jurnal, JurnalDetail, ChartOfAccount

def akun(nama):
    return ChartOfAccount.objects.get(nama_akun=nama)

def buat_jurnal(tanggal, keterangan, lines):
    j = Jurnal.objects.create(
        tanggal=tanggal,
        keterangan=keterangan,
    )
    for nama_akun, debit, kredit in lines:
        JurnalDetail.objects.create(
            jurnal=j,
            akun=akun(nama_akun),
            debit=Decimal(debit),
            kredit=Decimal(kredit)
        )

for i, d in enumerate([
    date(2025,1,15), date(2025,2,15), date(2025,3,15),
    date(2025,4,15), date(2025,5,15), date(2025,6,15),
    date(2025,7,15), date(2025,8,15), date(2025,9,15),
    date(2025,9,30),
]):
    buat_jurnal(
        d,
        f"Pendapatan jasa telekomunikasi {i+1}",
        [
            ("Piutang Usaha (Pihak Berelasi + Ketiga)", "10900", "0"),
            ("Pendapatan Usaha", "0", "10900"),
        ]
    )

for d in [
    date(2025,1,31), date(2025,2,28), date(2025,3,31),
    date(2025,4,30), date(2025,5,31), date(2025,6,30),
]:
    buat_jurnal(
        d,
        "Pembayaran beban karyawan",
        [
            ("Beban Karyawan", "4000", "0"),
            ("Kas dan setara kas", "0", "4000"),
        ]
    )

for d in [
    date(2025,2,15), date(2025,3,15), date(2025,4,15),
    date(2025,5,15), date(2025,6,15),
]:
    buat_jurnal(
        d,
        "Beban operasi dan pemeliharaan jaringan",
        [
            ("Beban Operasi & Pemeliharaan", "6000", "0"),
            ("Kas dan setara kas", "0", "6000"),
        ]
    )

for d in [
    date(2025,3,31), date(2025,4,30),
    date(2025,5,31), date(2025,6,30),
]:
    buat_jurnal(
        d,
        "Beban umum dan administrasi",
        [
            ("Beban Umum & Administrasi", "4000", "0"),
            ("Kas dan setara kas", "0", "4000"),
        ]
    )

for d in [
    date(2025,4,30), date(2025,5,31),
]:
    buat_jurnal(
        d,
        "Beban pemasaran",
        [
            ("Beban Pemasaran", "5000", "0"),
            ("Kas dan setara kas", "0", "5000"),
        ]
    )

for d in [
    date(2025,3,31), date(2025,6,30),
    date(2025,9,30), date(2025,9,30),
]:
    buat_jurnal(
        d,
        "Beban penyusutan dan amortisasi",
        [
            ("Beban Penyusutan & Amortisasi", "3000", "0"),
            ("Aset Tetap", "0", "3000"),
        ]
    )

buat_jurnal(
    date(2025,4,10),
    "Penarikan pinjaman bank",
    [
        ("Kas dan setara kas", "8000", "0"),
        ("Pinjaman Bank & Obligasi (Jangka Pendek+Panjang)", "0", "8000"),
    ]
)

for d in [
    date(2025,3,31), date(2025,6,30),
    date(2025,9,30), date(2025,9,30),
]:
    buat_jurnal(
        d,
        "Beban bunga pinjaman",
        [
            ("Biaya Pendanaan (Bunga)", "1000", "0"),
            ("Kas dan setara kas", "0", "1000"),
        ]
    )

buat_jurnal(
    date(2025,9,30),
    "Beban pajak penghasilan",
    [
        ("Beban Pajak Penghasilan", "7000", "0"),
        ("Utang Pajak", "0", "7000"),
    ]
)

buat_jurnal(
    date(2025,6,30),
    "Pembayaran dividen tunai",
    [
        ("Saldo Laba (Ditahan)", "5000", "0"),
        ("Kas dan setara kas", "0", "5000"),
    ]
)
