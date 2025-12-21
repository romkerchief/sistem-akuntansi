import json
import os
import django
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from laporan_keuangan.models import Jurnal, JurnalDetail, ChartOfAccount

JSON_FILE = "csvjson 2.json"

QUARTERS = [
    ("Q1 2025", date(2025, 3, 31), Decimal("0.30")),
    ("Q2 2025", date(2025, 6, 30), Decimal("0.35")),
    ("Q3 2025", date(2025, 9, 30), Decimal("0.35")),  # absorbs rounding
]

EXCLUDE_PREFIX = ("JUMLAH",)
EXCLUDE_NAMA = {
    "Laba Usaha (Operating Profit)",
    "Laba Periode Berjalan",
}

FLOW_KATEGORI = {"PENDAPATAN", "BEBAN", "DIVIDEN"}
STOCK_KATEGORI = {"ASET", "LIABILITAS", "EKUITAS"}

def D(x):
    return Decimal(str(x))

def round_amt(x):
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

def akun(nama):
    return ChartOfAccount.objects.get(nama_akun=nama)

def buat_jurnal(tanggal, keterangan, lines):
    j = Jurnal.objects.create(
        tanggal=tanggal,
        keterangan=keterangan,
        jenis="GENERAL",
    )
    for nama_akun, debit, kredit in lines:
        if debit == 0 and kredit == 0:
            continue
        JurnalDetail.objects.create(
            jurnal=j,
            akun=akun(nama_akun),
            debit=debit,
            kredit=kredit,
        )

saldo_laba = akun("Saldo Laba (Ditahan)")
kas = akun("Kas dan setara kas")

# --------------------------------------------------
# 1. Load JSON safely
# --------------------------------------------------

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

flows = []   # (kategori, nama, nilai_2025)
stocks = []  # (kategori, nama, delta)

for row in data:
    nama = row.get("nama_akun")
    kategori = row.get("Kategori")

    if not nama or not kategori:
        continue
    if kategori == "ARUS_KAS":
        continue
    if nama.upper().startswith(EXCLUDE_PREFIX):
        continue
    if nama in EXCLUDE_NAMA:
        continue

    raw_2025 = row.get("Nilai_2025", 0)
    raw_2024 = row.get("Nilai_2024", 0)

    nilai_2025 = D(raw_2025) if raw_2025 not in ("", None, "-") else Decimal("0")
    nilai_2024 = D(raw_2024) if raw_2024 not in ("", None, "-") else Decimal("0")

    if kategori in FLOW_KATEGORI and nilai_2025 != 0:
        flows.append((kategori, nama, abs(nilai_2025)))

    elif kategori in STOCK_KATEGORI:
        delta = nilai_2025 - nilai_2024
        if delta != 0:
            stocks.append((kategori, nama, delta))

# --------------------------------------------------
# 2. Journal FLOW accounts (Nilai_2025)
# --------------------------------------------------

for kategori, nama, total in flows:
    remaining = total

    for i, (label, tanggal, ratio) in enumerate(QUARTERS):
        if i < len(QUARTERS) - 1:
            portion = round_amt(total * ratio)
            if portion > remaining:
                portion = remaining
        else:
            portion = remaining

        remaining -= portion
        if portion == 0:
            continue

        # Pendapatan
        if kategori == "PENDAPATAN":
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

# --------------------------------------------------
# 3. Journal STOCK accounts (delta-based)
#    Counter-account = Saldo Laba
# --------------------------------------------------

for kategori, nama, delta_total in stocks:
    remaining = abs(delta_total)

    for i, (label, tanggal, ratio) in enumerate(QUARTERS):
        if i < len(QUARTERS) - 1:
            portion = round_amt(abs(delta_total) * ratio)
            if portion > remaining:
                portion = remaining
        else:
            portion = remaining

        remaining -= portion
        if portion == 0:
            continue

        # Aset turun = depreciation-like
        if nama == "Aset Tetap" and delta_total < 0:
            buat_jurnal(
                tanggal,
                f"Penyusutan aset tetap {label}",
                [
                    ("Beban Penyusutan & Amortisasi", portion, Decimal("0")),
                    ("Aset Tetap", Decimal("0"), portion),
                ],
            )
            continue

        # Generic balance-sheet delta → equity sink
        if delta_total > 0:
            buat_jurnal(
                tanggal,
                f"Penyesuaian {nama} {label}",
                [
                    (nama, portion, Decimal("0")),
                    ("Saldo Laba (Ditahan)", Decimal("0"), portion),
                ],
            )
        else:
            buat_jurnal(
                tanggal,
                f"Penyesuaian {nama} {label}",
                [
                    ("Saldo Laba (Ditahan)", portion, Decimal("0")),
                    (nama, Decimal("0"), portion),
                ],
            )

print("✅ Dummy transactions generated (final, equity-sink model).")
