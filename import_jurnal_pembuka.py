import json
import os
import django
from decimal import Decimal

# --- Django setup ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from laporan_keuangan.models import ChartOfAccount, Jurnal, JurnalDetail

JSON_FILE = "csvjson 2.json"

INCLUDE_KATEGORI = {"ASET", "LIABILITAS", "EKUITAS"}

def is_aggregate(nama):
    nama = nama.upper()
    return nama.startswith("JUMLAH")

def main():
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)

    jurnal = Jurnal.objects.create(
        tanggal="2025-01-01",
        keterangan="Jurnal Pembuka FY 2025 (Saldo Akhir 2024)",
        jenis="OPENING"
    )

    total_debit = Decimal("0")
    total_kredit = Decimal("0")
    created = 0
    skipped = 0

    for row in data:
        kategori = row.get("Kategori")
        nama_akun = row.get("nama_akun")
        nilai = row.get("Nilai_2024")

        if not kategori or not nama_akun:
            skipped += 1
            continue

        kategori = kategori.replace(" ", "_")

        if kategori not in INCLUDE_KATEGORI:
            skipped += 1
            continue

        if is_aggregate(nama_akun):
            skipped += 1
            continue

        try:
            akun = ChartOfAccount.objects.get(nama_akun=nama_akun)
        except ChartOfAccount.DoesNotExist:
            print(f"[WARNING] Akun tidak ditemukan di COA: {nama_akun}")
            skipped += 1
            continue

        nilai = Decimal(str(nilai))

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
            kredit=kredit
        )

        created += 1

    print("=== IMPORT JURNAL PEMBUKA ===")
    print(f"Jurnal ID      : {jurnal.id}")
    print(f"Baris dibuat  : {created}")
    print(f"Baris dilewati: {skipped}")
    print(f"Total Debit   : {total_debit}")
    print(f"Total Kredit : {total_kredit}")

    if total_debit != total_kredit:
        print("Debit dan Kredit TIDAK seimbang!")
    else:
        print("Debit dan Kredit seimbang.")

if __name__ == "__main__":
    main()
