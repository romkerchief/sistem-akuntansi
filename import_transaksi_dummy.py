import json
import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from laporan_keuangan.models import Jurnal, JurnalDetail, ChartOfAccount

JSON_FILE = "csvjson 2.json"

EXCLUDE_PREFIX = ("JUMLAH",)
EXCLUDE_NAMA = {
    "Laba Usaha (Operating Profit)",
    "Laba Periode Berjalan",
}

def akun(nama):
    return ChartOfAccount.objects.get(nama_akun=nama)

def buat_jurnal(tanggal, keterangan, lines):
    j = Jurnal.objects.create(
        tanggal=tanggal,
        keterangan=keterangan,
        jenis="GENERAL",
    )
    for nama_akun, debit, kredit in lines:
        JurnalDetail.objects.create(
            jurnal=j,
            akun=akun(nama_akun),
            debit=Decimal(debit),
            kredit=Decimal(kredit),
        )

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

# --- 1. Compute deltas ---
deltas = []
for row in data:
    nama = row["nama_akun"]
    kategori = row["Kategori"]
    if nama.upper().startswith(EXCLUDE_PREFIX):
        continue
    if nama in EXCLUDE_NAMA:
        continue
    if kategori == "ARUS_KAS":
        continue
    delta = Decimal(row["Nilai_2025"]) - Decimal(row["Nilai_2024"])
    if delta != 0:
        deltas.append((kategori, nama, delta))


# --- 2. Revenue recognition ---
pendapatan = sum(
    d for k, _, d in deltas if k == "PENDAPATAN" and d > 0
)

if pendapatan:
    buat_jurnal(
        date(2025, 9, 30),
        "Pengakuan pendapatan usaha YTD 2025",
        [
            ("Piutang Usaha (Pihak Berelasi + Ketiga)", pendapatan, 0),
            ("Pendapatan Usaha", 0, pendapatan),
        ],
    )

# --- 3. Operating expenses ---
for kategori, nama, delta in deltas:
    if kategori == "BEBAN":
        buat_jurnal(
            date(2025, 9, 30),
            f"Pengakuan {nama} YTD 2025",
            [
                (nama, abs(delta), 0),
                ("Kas dan setara kas", 0, abs(delta)),
            ],
        )

# --- 4. Depreciation ---
for kategori, nama, delta in deltas:
    if nama == "Aset Tetap" and delta < 0:
        buat_jurnal(
            date(2025, 9, 30),
            "Penyusutan aset tetap YTD 2025",
            [
                ("Beban Penyusutan & Amortisasi", abs(delta), 0),
                ("Aset Tetap", 0, abs(delta)),
            ],
        )

# --- 5. Dividends ---
for kategori, nama, delta in deltas:
    if kategori == "DIVIDEN":
        buat_jurnal(
            date(2025, 6, 30),
            "Pembayaran dividen tunai",
            [
                ("Saldo Laba (Ditahan)", abs(delta), 0),
                ("Kas dan setara kas", 0, abs(delta)),
            ],
        )

print("✅ Dummy transactions generated from JSON deltas.")
