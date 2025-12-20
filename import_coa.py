import json
import os
import django

# --- Django setup ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laporan_keuangan_telkom.settings")
django.setup()

from laporan_keuangan.models import ChartOfAccount

JSON_FILE = "csvjson 2.json"

# Mapping kategori → kode awal
KODE_AWAL = {
    "ASET": 1000,
    "LIABILITAS": 2000,
    "EKUITAS": 3000,
    "PENDAPATAN": 4000,
    "BEBAN": 5000,
    "DIVIDEN": 6000,
    "ARUS_KAS": 7000,
}

# Saldo normal rule (Indonesia standard)
SALDO_NORMAL = {
    "ASET": "DEBIT",
    "BEBAN": "DEBIT",
    "DIVIDEN": "DEBIT",
    "LIABILITAS": "KREDIT",
    "EKUITAS": "KREDIT",
    "PENDAPATAN": "KREDIT",
    "ARUS_KAS": "DEBIT",  # treated as flow, debit-normal is acceptable academically
}


def is_aggregate(nama):
    nama = nama.upper()
    return (
        nama.startswith("JUMLAH")
        or "LABA" in nama
    )


def main():
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)

    counters = {k: 0 for k in KODE_AWAL.keys()}
    created = 0
    skipped = 0

    for row in data:
        kategori = row.get("Kategori")
        if kategori:
            kategori = kategori.replace(" ", "_")
        nama_akun = row.get("nama_akun")

        if not kategori or not nama_akun:
            skipped += 1
            continue

        if is_aggregate(nama_akun):
            skipped += 1
            continue

        counters[kategori] += 1
        kode_akun = str(KODE_AWAL[kategori] + counters[kategori])

        obj, is_created = ChartOfAccount.objects.get_or_create(
            kode_akun=kode_akun,
            defaults={
                "nama_akun": nama_akun,
                "kategori": kategori,
                "saldo_normal": SALDO_NORMAL[kategori],
            }
        )

        if is_created:
            created += 1

    print("=== COA IMPORT RESULT ===")
    print(f"Created : {created}")
    print(f"Skipped : {skipped}")
    print(f"Total COA: {ChartOfAccount.objects.count()}")


if __name__ == "__main__":
    main()
