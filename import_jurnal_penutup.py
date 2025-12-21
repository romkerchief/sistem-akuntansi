import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from django.db.models import Sum
from laporan_keuangan.models import Jurnal, JurnalDetail, ChartOfAccount

CLOSING_DATE = date(2025, 9, 30)

# --------------------------------------------------
# Helper
# --------------------------------------------------

def akun(nama):
    return ChartOfAccount.objects.get(nama_akun=nama)

def buat_jurnal(keterangan, lines):
    j = Jurnal.objects.create(
        tanggal=CLOSING_DATE,
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

# --------------------------------------------------
# SAFETY: prevent double closing
# --------------------------------------------------

if Jurnal.objects.filter(
    keterangan__icontains="PENUTUPAN FINAL"
).exists():
    print("⚠️ Closing journal already exists. Aborting.")
    exit()

# --------------------------------------------------
# 1. Compute laba rugi (authoritative)
# --------------------------------------------------

pendapatan = (
    JurnalDetail.objects
    .filter(akun__kategori="PENDAPATAN")
    .aggregate(total=Sum("kredit"))
)["total"] or Decimal("0")

beban = (
    JurnalDetail.objects
    .filter(akun__kategori="BEBAN")
    .aggregate(total=Sum("debit"))
)["total"] or Decimal("0")

laba_bersih = pendapatan - beban

# --------------------------------------------------
# 2. Compute dividen
# --------------------------------------------------

dividen = (
    JurnalDetail.objects
    .filter(akun__kategori="DIVIDEN")
    .aggregate(total=Sum("kredit"))
)["total"] or Decimal("0")

# --------------------------------------------------
# 3. Closing journal
# --------------------------------------------------

lines = []

# Close laba rugi → saldo laba
if laba_bersih != 0:
    lines.append((
        "Saldo Laba (Ditahan)",
        Decimal("0"),
        laba_bersih
    ))

# Close dividen → saldo laba
if dividen != 0:
    lines.append((
        "Saldo Laba (Ditahan)",
        dividen,
        Decimal("0")
    ))

if not lines:
    print("ℹ️ Nothing to close.")
    exit()

buat_jurnal(
    "PENUTUPAN FINAL: laba rugi & dividen ke saldo laba",
    lines
)

print("✅ Closing journal created successfully.")
print(f"   Laba Bersih : {laba_bersih}")
print(f"   Dividen     : {dividen}")
