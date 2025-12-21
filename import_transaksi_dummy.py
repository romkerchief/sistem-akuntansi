import json
import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from laporan_keuangan.models import Jurnal, JurnalDetail, ChartOfAccount

JSON_FILE = "csvjson 2.json"

SPLITS = [
    ("Q1 2025", date(2025, 3, 31), Decimal("0.30")),
    ("Q2 2025", date(2025, 6, 30), Decimal("0.35")),
    ("Q3 2025", date(2025, 9, 30), Decimal("0.35")),
]

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
            debit=debit,
            kredit=kredit,
        )

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

# --- compute deltas ---
deltas = []
for row in data:
    nama = row["nama_akun"]
    kategori = row["Kategori"]

    if kategori == "ARUS_KAS":
        continue
    if nama.upper().startswith(EXCLUDE_PREFIX):
        continue
    if nama in EXCLUDE_NAMA:
        continue

    delta = Decimal(row["Nilai_2025"]) - Decimal(row["Nilai_2024"])
    if delta != 0:
        deltas.append((kategori, nama, delta))

# --- generate journals ---
for label, tanggal, ratio in SPLITS:
    for kategori, nama, delta in deltas:
        portion = (abs(delta) * ratio).quantize(Decimal("1"))

        if portion == 0:
            continue

        # Pendapatan
        if kategori == "PENDAPATAN" and delta > 0:
            buat_jurnal(
                tanggal,
                f"Pengakuan pendapatan {label}",
                [
                    ("Piutang Usaha (Pihak Berelasi + Ketiga)", portion, Decimal("0")),
                    ("Pendapatan Usaha", Decimal("0"), portion),
                ],
            )

        # Beban
        elif kategori == "BEBAN":
            buat_jurnal(
                tanggal,
                f"Pengakuan {nama} {label}",
                [
                    (nama, portion, Decimal("0")),
                    ("Kas dan setara kas", Decimal("0"), portion),
                ],
            )

        # Aset Tetap (penyusutan)
        elif nama == "Aset Tetap" and delta < 0:
            buat_jurnal(
                tanggal,
                f"Penyusutan aset tetap {label}",
                [
                    ("Beban Penyusutan & Amortisasi", portion, Decimal("0")),
                    ("Aset Tetap", Decimal("0"), portion),
                ],
            )

        # Dividen
        elif kategori == "DIVIDEN":
            buat_jurnal(
                tanggal,
                f"Pembayaran dividen {label}",
                [
                    ("Saldo Laba (Ditahan)", portion, Decimal("0")),
                    ("Kas dan setara kas", Decimal("0"), portion),
                ],
            )

print("✅ Dummy transactions split across Q1–Q3 generated.")
