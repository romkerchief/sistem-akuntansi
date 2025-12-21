import json
import os
import django
from decimal import Decimal
from datetime import date

# --- Django setup ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from laporan_keuangan.models import ChartOfAccount, Jurnal, JurnalDetail

JSON_FILE = "csvjson 2.json"
OPENING_DATE = date(2025, 1, 1)
SALDO_LABA_NAMA = "Saldo Laba (Ditahan)"

NERACA_KATEGORI = {"ASET", "LIABILITAS", "EKUITAS"}

EXCLUDE_NAMA_PREFIX = (
    "JUMLAH",
)

def main():
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)

    jurnal = Jurnal.objects.create(
        tanggal=OPENING_DATE,
        keterangan="Jurnal Pembuka FY 2025 (Saldo Akhir 2024)",
        jenis="OPENING",
    )

    total_debit = Decimal("0")
    total_kredit = Decimal("0")

    saldo_laba = ChartOfAccount.objects.get(nama_akun=SALDO_LABA_NAMA)

    for row in data:
        nama = row.get("nama_akun")
        kategori = row.get("Kategori")
        nilai = row.get("Nilai_2024")

        if not nama or nilai is None:
            continue

        # --- STRICT FILTERS ---
        if kategori not in NERACA_KATEGORI:
            continue

        if nama.upper().startswith(EXCLUDE_NAMA_PREFIX):
            continue

        nilai = abs(Decimal(str(nilai)))  # ABSOLUTE BALANCE

        try:
            akun = ChartOfAccount.objects.get(nama_akun=nama)
        except ChartOfAccount.DoesNotExist:
            print(f"[SKIP] Akun tidak ditemukan: {nama}")
            continue

        debit = Decimal("0")
        kredit = Decimal("0")

        if akun.saldo_normal == "DEBIT":
            debit = nilai
            total_debit += nilai
        else:
            kredit = nilai
            total_kredit += nilai

        JurnalDetail.objects.create(
            jurnal=jurnal,
            akun=akun,
            debit=debit,
            kredit=kredit,
        )

    # --- BALANCING ENTRY (SALDO LABA) ---
    selisih = total_debit - total_kredit

    if selisih != 0:
        if selisih > 0:
            # Debit > Kredit → credit saldo laba
            JurnalDetail.objects.create(
                jurnal=jurnal,
                akun=saldo_laba,
                debit=Decimal("0"),
                kredit=selisih,
            )
            total_kredit += selisih
        else:
            # Kredit > Debit → debit saldo laba
            JurnalDetail.objects.create(
                jurnal=jurnal,
                akun=saldo_laba,
                debit=abs(selisih),
                kredit=Decimal("0"),
            )
            total_debit += abs(selisih)

    print("=== JURNAL PEMBUKA FY 2025 (NERACA ONLY) ===")
    print(f"Total Debit  : {total_debit}")
    print(f"Total Kredit : {total_kredit}")

    if total_debit == total_kredit:
        print("✅ Seimbang")
    else:
        print("❌ TIDAK seimbang — cek data!")

if __name__ == "__main__":
    main()
