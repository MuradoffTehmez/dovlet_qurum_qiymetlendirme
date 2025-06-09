# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Ana səhifə (dashboard)
    path('', views.dashboard, name='dashboard'),
    
    # Konkret qiymətləndirməni etmək üçün səhifə
    path('qiymetlendir/<int:qiymetlendirme_id>/', views.qiymetlendirme_etmek, name='qiymetlendirme_etmek'),
]