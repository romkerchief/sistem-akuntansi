from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, Q
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import ChartOfAccount, Jurnal, JurnalDetail, Period
from datetime import date, timedelta
from collections import defaultdict
from decimal import Decimal
from datetime import datetime


def get_active_period(request):
    period_id = request.session.get("active_period_id")

    if period_id:
        return Period.objects.get(id=period_id)

    period = Period.objects.filter(is_active=True).first()
    if period:
        request.session["active_period_id"] = period.id
    return period

def saldo_per_akun_as_of(date):
    """
    Returns dict:
    {
        akun_id: {
            "akun": akun_obj,
            "debit": Decimal,
            "kredit": Decimal,
            "saldo": Decimal
        }
    }
    """

    details = (
        JurnalDetail.objects
        .filter(
            Q(jurnal__jenis="OPENING") |
            Q(jurnal__jenis="GENERAL", jurnal__tanggal__lte=date)
        )
        .select_related("akun")
    )

    saldo_map = {}

    for d in details:
        kode = d.akun.kode_akun
        entry = saldo_map.setdefault(kode, {
            "akun": d.akun,
            "debit": Decimal("0"),
            "kredit": Decimal("0"),
        })
        entry["debit"] += d.debit
        entry["kredit"] += d.kredit

    # compute saldo
    for acc in saldo_map.values():
        akun = acc["akun"]
        if akun.saldo_normal == "DEBIT":
            acc["saldo"] = acc["debit"] - acc["kredit"]
        else:
            acc["saldo"] = acc["kredit"] - acc["debit"]

    return saldo_map

@require_POST
def delete_jurnal(request, jurnal_id):
    jurnal = get_object_or_404(Jurnal, id=jurnal_id)

    jenis = jurnal.jenis  # keep before delete
    jurnal.delete()

    messages.success(request, "Jurnal berhasil dihapus.")

    return redirect(
        "finance:jurnal_umum" if jenis == "GENERAL"
        else "finance:jurnal_pembuka"
    )

def home(request):
    periods = Period.objects.all().order_by("start_date")

    if request.method == "POST":
        period_id = request.POST.get("period_id")
        request.session["active_period_id"] = period_id

    active_period = get_active_period(request)

    return render(request, "laporan_keuangan/home.html", {
        "periods": periods,
        "active_period": active_period,
    })

def jurnal_pembuka(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    jurnal = (
        Jurnal.objects
        .filter(jenis="OPENING")
        .prefetch_related("details", "details__akun")
        .order_by("tanggal")
    )

    return render(request, "laporan_keuangan/jurnal_pembuka.html", {
        "jurnal_list": jurnal,
        "period_start": period_start,
        "period_end": period_end
    })

def jurnal_umum(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    jurnal_list = (
        Jurnal.objects
        .filter(
            jenis="GENERAL",
            tanggal__range=[period_start, period_end]
        )
        .order_by("tanggal", "id")
        .prefetch_related("details", "details__akun")
    )

    return render(request, "laporan_keuangan/jurnal_umum.html", {
        "jurnal_list": jurnal_list,
        "period_start": period_start,\
        "period_end": period_end
    })

def edit_jurnal(request, jurnal_id):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    jurnal = get_object_or_404(Jurnal, id=jurnal_id)
    details = JurnalDetail.objects.filter(jurnal=jurnal)
    akun_list = ChartOfAccount.objects.all().order_by("kode_akun")

    if request.method == "POST":
        tanggal = request.POST.get("tanggal")
        keterangan = request.POST.get("keterangan")

        akun_ids = request.POST.getlist("akun")
        debits = request.POST.getlist("debit")
        kredits = request.POST.getlist("kredit")

        with transaction.atomic():
            # Update header
            jurnal.tanggal = tanggal
            jurnal.keterangan = keterangan
            jurnal.save()

            # Remove old rows
            details.delete()

            # Recreate rows
            for akun_id, debit, kredit in zip(akun_ids, debits, kredits):
                if not debit:
                    debit = 0
                if not kredit:
                    kredit = 0

                if float(debit) == 0 and float(kredit) == 0:
                    continue

                JurnalDetail.objects.create(
                    jurnal=jurnal,
                    akun_id=akun_id,
                    debit=debit,
                    kredit=kredit
                )

        messages.success(request, "Jurnal berhasil diperbarui.")
        return redirect("finance:jurnal_umum" if jurnal.jenis == "GENERAL" else "finance:jurnal_pembuka")

    context = {
        "jurnal": jurnal,
        "details": details,
        "akun_list": akun_list,
        "period_start": period_start,
        "period_end": period_end,
    }

    return render(request, "laporan_keuangan/edit_jurnal.html", context)

@login_required
def input_transaksi(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    akun_list = ChartOfAccount.objects.all()

    if request.method == "POST":
        tanggal = request.POST.get("tanggal")
        keterangan = request.POST.get("keterangan")

        akun_ids = request.POST.getlist("akun[]")
        posisi_list = request.POST.getlist("posisi[]")
        jumlah_list = request.POST.getlist("jumlah[]")

        total_debit = 0
        total_kredit = 0

        for posisi, jumlah in zip(posisi_list, jumlah_list):
            jumlah = float(jumlah or 0)
            if posisi == "DEBIT":
                total_debit += jumlah
            else:
                total_kredit += jumlah

        if total_debit != total_kredit:
            return render(request, "laporan_keuangan/input_transaksi_test.html", {
                "akun_list": akun_list,
                "today": date.today(),
                "error": "Total debit harus sama dengan total kredit."
            })

        jurnal = Jurnal.objects.create(
            tanggal=tanggal,
            keterangan=keterangan
        )

        for akun_id, posisi, jumlah in zip(akun_ids, posisi_list, jumlah_list):
            jumlah = float(jumlah or 0)
            if jumlah == 0:
                continue

            JurnalDetail.objects.create(
                jurnal=jurnal,
                akun_id=akun_id,
                debit=jumlah if posisi == "DEBIT" else 0,
                kredit=jumlah if posisi == "KREDIT" else 0,
            )

        return redirect("finance:input_transaksi")

    return render(request, "laporan_keuangan/input_transaksi.html", {
        "akun_list": akun_list,
        "today": date.today(),
        "period_start": period_start,
        "period_end": period_end
    })

def buku_besar(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    akun_qs = ChartOfAccount.objects.annotate(
        total_debit=Sum(
            "jurnaldetail__debit",
        ),
        total_kredit=Sum(
            "jurnaldetail__kredit",
        ),
    )

    rows = []
    for akun in akun_qs:
        debit = akun.total_debit or 0
        kredit = akun.total_kredit or 0

        if akun.saldo_normal == "DEBIT":
            saldo = debit - kredit
        else:
            saldo = kredit - debit

        rows.append({
            "akun_id": akun.id,
            "kode": akun.kode_akun,
            "nama": akun.nama_akun,
            "debit": debit,
            "kredit": kredit,
            "saldo": saldo,
        })

    return render(request, "laporan_keuangan/buku_besar.html", {
        "rows": rows,
        "period_start": period_start,
        "period_end": period_end,
    })

def buku_besar_detail(request, akun_id):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    akun = get_object_or_404(ChartOfAccount, id=akun_id)

    details = (
        JurnalDetail.objects
        .filter(akun=akun)
        .select_related("jurnal")
        .order_by("jurnal__tanggal", "id")
    )

    rows = []
    saldo = 0

    for d in details:
        debit = d.debit or 0
        kredit = d.kredit or 0

        if akun.saldo_normal == "DEBIT":
            saldo += debit - kredit
        else:
            saldo += kredit - debit

        rows.append({
            "tanggal": d.jurnal.tanggal,
            "keterangan": d.jurnal.keterangan,
            "debit": debit,
            "kredit": kredit,
            "saldo": saldo,
        })

    return render(request, "laporan_keuangan/buku_besar_detail.html", {
        "akun": akun,
        "rows": rows,
        "saldo_akhir": saldo,
        "period_start": period_start,
        "period_end": period_end,
    })

def laba_rugi(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    # Laba Rugi hanya dari jurnal umum (OPENING TIDAK ikut)
    details = (
        JurnalDetail.objects
        .filter(jurnal__jenis="GENERAL")
        .filter(
            jurnal__tanggal__range=[period_start, period_end]
        )
    )

    pendapatan = (
        details
        .filter(akun__kategori="PENDAPATAN")
        .values("akun__kode_akun", "akun__nama_akun")
        .annotate(
            total=Sum(F("kredit") - F("debit"))
        )
    )

    beban = (
        details
        .filter(akun__kategori="BEBAN")
        .values("akun__kode_akun", "akun__nama_akun")
        .annotate(
            total=Sum(F("debit") - F("kredit"))
        )
    )

    total_pendapatan = sum(p["total"] for p in pendapatan)
    total_beban = sum(b["total"] for b in beban)
    laba_bersih = total_pendapatan - total_beban

    context = {
        "pendapatan": pendapatan,
        "beban": beban,
        "total_pendapatan": total_pendapatan,
        "total_beban": total_beban,
        "laba_bersih": laba_bersih,
        "period_start": period_start,
        "period_end": period_end,
    }

    return render(request, "laporan_keuangan/laba_rugi.html", context)

from collections import defaultdict
from decimal import Decimal

def neraca(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    # 1. Tentukan jurnal yang relevan
    opening_journals = Jurnal.objects.filter(
        jenis="OPENING",
        tanggal__lte=period_start
    )

    closing_journals = Jurnal.objects.filter(
        keterangan__icontains="Penutupan laba rugi",
        tanggal__lte=period_end
    )

    journals = (
        Jurnal.objects.filter(
            jenis="OPENING",
            tanggal__lte=period_start
        )
        |
        Jurnal.objects.filter(
            jenis="GENERAL",
            tanggal__range=(period_start, period_end)
        )
        |
        Jurnal.objects.filter(
            jenis="CLOSING",
            tanggal__lte=period_end
        )
    )

    # 2. Ambil detail jurnal hanya untuk akun Neraca
    details = (
        JurnalDetail.objects
        .filter(
            jurnal__in=journals,
            akun__kategori__in=["ASET", "LIABILITAS", "EKUITAS"]
        )
        .select_related("akun")
    )

    # 3. Akumulasi saldo per akun
    saldo_map = defaultdict(lambda: {
        "akun": None,
        "debit": Decimal("0"),
        "kredit": Decimal("0"),
    })

    for d in details:
        entry = saldo_map[d.akun_id]
        entry["akun"] = d.akun
        entry["debit"] += d.debit
        entry["kredit"] += d.kredit

    aset = []
    liabilitas = []
    ekuitas = []

    total_aset = Decimal("0")
    total_liabilitas = Decimal("0")
    total_ekuitas = Decimal("0")

    # 4. Hitung saldo akhir per akun
    for data in saldo_map.values():
        akun = data["akun"]
        debit = data["debit"]
        kredit = data["kredit"]

        if akun.saldo_normal == "DEBIT":
            saldo = debit - kredit
        else:
            saldo = kredit - debit

        row = {
            "kode": akun.kode_akun,
            "nama": akun.nama_akun,
            "saldo": saldo,
        }

        if akun.kategori == "ASET":
            aset.append(row)
            total_aset += saldo
        elif akun.kategori == "LIABILITAS":
            liabilitas.append(row)
            total_liabilitas += saldo
        elif akun.kategori == "EKUITAS":
            ekuitas.append(row)
            total_ekuitas += saldo

    context = {
        "aset": aset,
        "liabilitas": liabilitas,
        "ekuitas": ekuitas,
        "total_aset": total_aset,
        "total_liabilitas": total_liabilitas,
        "total_ekuitas": total_ekuitas,
        "period_start": period_start,
        "period_end": period_end,
    }

    return render(request, "laporan_keuangan/neraca.html", context)

def neraca_saldo_disesuaikan(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    journals = (
        Jurnal.objects.filter(
            jenis="OPENING",
            tanggal__lte=period_start
        )
        |
        Jurnal.objects.filter(
            jenis="GENERAL",
            tanggal__range=(period_start, period_end)
        )
    ).exclude(
        keterangan__icontains="Penutupan laba rugi"
    )

    details = (
        JurnalDetail.objects
        .filter(jurnal__in=journals)
        .select_related("akun")
    )

    saldo_map = defaultdict(lambda: {
        "akun": None,
        "debit": Decimal("0"),
        "kredit": Decimal("0"),
    })

    for d in details:
        entry = saldo_map[d.akun_id]
        entry["akun"] = d.akun
        entry["debit"] += d.debit
        entry["kredit"] += d.kredit

    rows = []
    total_debit = Decimal("0")
    total_kredit = Decimal("0")

    for data in saldo_map.values():
        akun = data["akun"]
        debit = data["debit"]
        kredit = data["kredit"]

        rows.append({
            "kode": akun.kode_akun,
            "nama": akun.nama_akun,
            "kategori": akun.kategori,
            "debit": debit,
            "kredit": kredit,
            "saldo": (
                debit - kredit
                if akun.saldo_normal == "DEBIT"
                else kredit - debit
            )
        })

        total_debit += debit
        total_kredit += kredit

    context = {
        "rows": rows,
        "total_debit": total_debit,
        "total_kredit": total_kredit,
        "period_start": period_start,
        "period_end": period_end,
    }

    return render(
        request,
        "laporan_keuangan/neraca_saldo_disesuaikan.html",
        context
    )

def perubahan_ekuitas(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    saldo_awal_map = saldo_per_akun_as_of(period_start - timedelta(days=1))
    saldo_akhir_map = saldo_per_akun_as_of(period_end)

    # --- Laba / Rugi periode berjalan ---
    total_pendapatan = (
        JurnalDetail.objects
        .filter(
            akun__kategori="PENDAPATAN",
            jurnal__jenis="GENERAL",
            jurnal__tanggal__range=(period_start, period_end)
        )
        .aggregate(total=Sum("kredit"))["total"] or Decimal("0")
    )

    total_beban = (
        JurnalDetail.objects
        .filter(
            akun__kategori="BEBAN",
            jurnal__jenis="GENERAL",
            jurnal__tanggal__range=(period_start, period_end)
        )
        .aggregate(total=Sum("debit"))["total"] or Decimal("0")
    )

    laba_bersih = total_pendapatan - total_beban

    # --- Dividen (debit saldo laba selama periode) ---
    dividen = (
        JurnalDetail.objects
        .filter(
            akun__kode_akun="3000-RE",
            jurnal__jenis="GENERAL",
            jurnal__tanggal__range=(period_start, period_end),
            debit__gt=0
        )
        .aggregate(total=Sum("debit"))["total"] or Decimal("0")
    )

    # --- Bangun baris laporan ---
    rows = []
    total_awal = Decimal("0")
    total_perubahan = Decimal("0")
    total_akhir = Decimal("0")

    ekuitas_accounts = ChartOfAccount.objects.filter(
        kategori="EKUITAS"
    ).order_by("kode_akun")

    for akun in ekuitas_accounts:
        kode = akun.kode_akun

        awal = saldo_awal_map.get(kode, {}).get("saldo", Decimal("0"))
        akhir = saldo_akhir_map.get(kode, {}).get("saldo", Decimal("0"))
        perubahan = akhir - awal

        rows.append({
            "kode": kode,
            "nama": akun.nama_akun,
            "awal": awal,
            "perubahan": perubahan,
            "akhir": akhir,
        })

        total_awal += awal
        total_perubahan += perubahan
        total_akhir += akhir

    context = {
        "rows": rows,
        "total_awal": total_awal,
        "total_perubahan": total_perubahan,
        "total_akhir": total_akhir,
        "laba_bersih": laba_bersih,
        "dividen": dividen,
        "period_start": period_start,
        "period_end": period_end,
    }

    return render(
        request,
        "laporan_keuangan/perubahan_ekuitas.html",
        context
    )

def arus_kas(request):
    period = get_active_period(request)
    period_start = period.start_date
    period_end = period.end_date

    saldo_awal = saldo_per_akun_as_of(period_start - timedelta(days=1))
    saldo_akhir = saldo_per_akun_as_of(period_end)

    def delta(kode):
        awal = saldo_awal.get(kode, {}).get("saldo", Decimal("0"))
        akhir = saldo_akhir.get(kode, {}).get("saldo", Decimal("0"))
        return akhir - awal

    # 1️⃣ Laba bersih (from laba rugi)
    laba_bersih = (
        JurnalDetail.objects
        .filter(
            jurnal__jenis="GENERAL",
            jurnal__tanggal__range=(period_start, period_end),
            akun__kategori="PENDAPATAN"
        )
        .aggregate(total=Sum("kredit"))["total"] or Decimal("0")
    ) - (
        JurnalDetail.objects
        .filter(
            jurnal__jenis="GENERAL",
            jurnal__tanggal__range=(period_start, period_end),
            akun__kategori="BEBAN"
        )
        .aggregate(total=Sum("debit"))["total"] or Decimal("0")
    )

    # 2️⃣ Operating activities
    operasi = {
        "Laba bersih": laba_bersih,
        "Kenaikan Piutang Usaha": -delta("1002"),
        "Kenaikan Persediaan": -delta("1004"),
        "Kenaikan Utang Usaha": delta("2001"),
        "Kenaikan Beban Akrual": delta("2003"),
    }

    kas_operasi = sum(operasi.values())

    # 3️⃣ Investing activities
    investasi = {
        "Perolehan Aset Tetap": -delta("1009"),
        "Perubahan Investasi": -delta("1008"),
    }

    kas_investasi = sum(investasi.values())

    # 4️⃣ Financing activities
    pendanaan = {
        "Penarikan / Pelunasan Pinjaman": delta("2005"),
        "Dividen Dibayar": -delta("3000-RE"),
    }

    kas_pendanaan = sum(pendanaan.values())

    # 5️⃣ Rekonsiliasi kas
    kas_awal = saldo_awal.get("1001", {}).get("saldo", Decimal("0"))
    kas_akhir = saldo_akhir.get("1001", {}).get("saldo", Decimal("0"))

    context = {
        "operasi": operasi,
        "investasi": investasi,
        "pendanaan": pendanaan,
        "kas_operasi": kas_operasi,
        "kas_investasi": kas_investasi,
        "kas_pendanaan": kas_pendanaan,
        "kenaikan_kas": kas_operasi + kas_investasi + kas_pendanaan,
        "kas_awal": kas_awal,
        "kas_akhir": kas_akhir,
        "period_start": period_start,
        "period_end": period_end,
    }

    return render(request, "laporan_keuangan/arus_kas.html", context)
