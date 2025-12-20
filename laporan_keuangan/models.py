from django.db import models


class ChartOfAccount(models.Model):
    KATEGORI_CHOICES = [
        ("ASET", "Aset"),
        ("LIABILITAS", "Liabilitas"),
        ("EKUITAS", "Ekuitas"),
        ("PENDAPATAN", "Pendapatan"),
        ("BEBAN", "Beban"),
        ("DIVIDEN", "Dividen"),
        ("ARUS_KAS", "Arus Kas"),
    ]

    SALDO_NORMAL_CHOICES = [
        ("DEBIT", "Debit"),
        ("KREDIT", "Kredit"),
    ]

    kode_akun = models.CharField(max_length=10, unique=True)
    nama_akun = models.CharField(max_length=255)
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES)
    saldo_normal = models.CharField(max_length=6, choices=SALDO_NORMAL_CHOICES)

    def __str__(self):
        return f"{self.kode_akun} - {self.nama_akun}"
    
class Jurnal(models.Model):
    JENIS_CHOICES = [
        ("OPENING", "Jurnal Pembuka"),
        ("GENERAL", "Jurnal Umum"),
        ("CLOSING", "Jurnal Penutup"),
    ]

    tanggal = models.DateField()
    keterangan = models.CharField(max_length=255)
    jenis = models.CharField(
        max_length=10,
        choices=JENIS_CHOICES,
        default="GENERAL"
    )

    def __str__(self):
        return f"{self.tanggal} - {self.keterangan}"

class JurnalDetail(models.Model):
    jurnal = models.ForeignKey(
        Jurnal,
        related_name="details",
        on_delete=models.CASCADE
    )
    akun = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.CASCADE
    )
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    kredit = models.DecimalField(max_digits=18, decimal_places=2, default=0)

class Period(models.Model):
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.nama
    