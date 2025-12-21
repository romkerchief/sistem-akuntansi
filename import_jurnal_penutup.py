from django.db import transaction
from django.db.models import Sum
from laporan_keuangan.models import Jurnal, JurnalDetail, ChartOfAccount

def close_period(period_start, period_end):
    pendapatan = JurnalDetail.objects.filter(
        akun__kategori="PENDAPATAN",
        jurnal__jenis="GENERAL",
        jurnal__tanggal__range=(period_start, period_end)
    )

    beban = JurnalDetail.objects.filter(
        akun__kategori="BEBAN",
        jurnal__jenis="GENERAL",
        jurnal__tanggal__range=(period_start, period_end)
    )

    total_pendapatan = pendapatan.aggregate(total=Sum("kredit"))["total"] or 0
    total_beban = beban.aggregate(total=Sum("debit"))["total"] or 0
    laba_bersih = total_pendapatan - total_beban

    saldo_laba = ChartOfAccount.objects.get(kode_akun="3000-RE")

    with transaction.atomic():
        jurnal = Jurnal.objects.create(
            tanggal=period_end,
            keterangan="Penutupan laba rugi periode",
            jenis="GENERAL"
        )

        for d in pendapatan:
            JurnalDetail.objects.create(
                jurnal=jurnal,
                akun=d.akun,
                debit=d.kredit,
                kredit=0
            )

        for d in beban:
            JurnalDetail.objects.create(
                jurnal=jurnal,
                akun=d.akun,
                debit=0,
                kredit=d.debit
            )

        # ONLY net income
        if laba_bersih != 0:
            JurnalDetail.objects.create(
                jurnal=jurnal,
                akun=saldo_laba,
                debit=0 if laba_bersih > 0 else abs(laba_bersih),
                kredit=laba_bersih if laba_bersih > 0 else 0
            )
