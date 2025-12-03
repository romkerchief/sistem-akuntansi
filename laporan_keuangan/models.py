from django.db import models

# Create your models here.
class Akun(models.Model):
    # This matches your JSON keys: "Id", "Kategori", "nama_akun"
    kode_akun = models.IntegerField(primary_key=True) # Assuming "Id" is the code like 101, 102
    nama_akun = models.CharField(max_length=255)
    kategori = models.CharField(max_length=50) # ASET, BEBAN, etc.
    
    def __str__(self):
        return f"{self.kode_akun} - {self.nama_akun}"

class Jurnal(models.Model):
    # This stores the "Header" (Date, Description)
    tanggal = models.DateField()
    keterangan = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class JurnalItem(models.Model):
    # This stores the lines: Account, Debit, Credit
    jurnal = models.ForeignKey(Jurnal, on_delete=models.CASCADE, related_name='items')
    akun = models.ForeignKey(Akun, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    kredit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.akun.nama_akun}: D{self.debit} | K{self.kredit}"