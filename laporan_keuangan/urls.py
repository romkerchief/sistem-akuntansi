from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path("", views.home, name="home"),
    path("jurnal-pembuka/", views.jurnal_pembuka, name="jurnal_pembuka"),
    path("jurnal-umum/", views.jurnal_umum, name="jurnal_umum"),
    path("input/", views.input_transaksi, name="input_transaksi"),
    path("jurnal/edit/<int:jurnal_id>/", views.edit_jurnal, name="edit_jurnal"),
    path("jurnal/delete/<int:jurnal_id>/", views.delete_jurnal, name="delete_jurnal"),
    path("buku-besar/", views.buku_besar, name="buku_besar"),
    path("buku-besar/<int:akun_id>/", views.buku_besar_detail, name="buku_besar_detail"),
    path("laba-rugi/", views.laba_rugi, name="laba_rugi"),
    path("neraca/", views.neraca, name="neraca"),
    path(
        "neraca-saldo-disesuaikan/",
        views.neraca_saldo_disesuaikan,
        name="neraca_saldo_disesuaikan"
    ),
    path(
        "perubahan-ekuitas/",
        views.perubahan_ekuitas,
        name="perubahan_ekuitas"
    ),
    path("laporan/arus-kas/", views.arus_kas, name="arus_kas"),
    
    # Dashboard API endpoints
    path("api/neraca-data/", views.api_neraca_data, name="api_neraca_data"),
    path("api/laba-rugi-data/", views.api_laba_rugi_data, name="api_laba_rugi_data"),
    path("api/arus-kas-data/", views.api_arus_kas_data, name="api_arus_kas_data"),
    path("api/ekuitas-data/", views.api_ekuitas_data, name="api_ekuitas_data"),
]
