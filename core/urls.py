# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('qiymetlendir/<int:qiymetlendirme_id>/', views.qiymetlendirme_etmek, name='qiymetlendirme_etmek'),
    
    # Yeni URL: İstifadəçinin öz hesabatını görməsi üçün
    path('hesabatim/', views.hesabat_sehifesi, name='hesabatim'),
]