# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('qiymetlendir/<int:qiymetlendirme_id>/', views.qiymetlendirme_etmek, name='qiymetlendirme_etmek'),
    path('hesabatim/', views.hesabat_sehifesi, name='hesabatim'), 
    
    # Rəhbərin öz komandasını gördüyü panel
    path('rehber-paneli/', views.rehber_paneli, name='rehber_paneli'),

    # Rəhbərin komanda üzvünün hesabatına baxması üçün
    path('hesabat/bax/<int:ishchi_id>/', views.hesabat_bax, name='hesabat_bax'),

    # YENİ URL
    path('hesabat/pdf/<int:ishchi_id>/', views.hesabat_pdf_yukle, name='hesabat_pdf_yukle'),
]