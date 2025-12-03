import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laporan_keuangan_telkom.settings')
django.setup()

from laporan_keuangan.models import Akun

def load_json():
    with open('csvjson.json', 'r') as f:
        data = json.load(f)
        
    for item in data:
        # The JSON uses "Id", "nama_akun", "Kategori"
        Akun.objects.get_or_create(
            kode_akun=item['Id'],
            defaults={
                'nama_akun': item['nama_akun'],
                'kategori': item['Kategori']
            }
        )
    print("Success! Data loaded.")

if __name__ == '__main__':
    load_json()