# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('qeydiyyat/', views.qeydiyyat_sehifesi, name='qeydiyyat'), 
    
    path('qiymetlendir/<int:qiymetlendirme_id>/', views.qiymetlendirme_etmek, name='qiymetlendirme_etmek'),
    
    # Yeni ortaq hesabat URL-ləri
    path('hesabatim/', views.hesabat_gorunumu, name='hesabatim'),
    path('hesabat/bax/<int:ishchi_id>/', views.hesabat_gorunumu, name='hesabat_bax'), 
    path('hesabat/pdf/<int:ishchi_id>/', views.hesabat_pdf_yukle, name='hesabat_pdf_yukle'),

    # Rəhbər və Superadmin panelləri
    path('rehber-paneli/', views.rehber_paneli, name='rehber_paneli'),
    path('superadmin/', views.superadmin_paneli, name='superadmin_paneli'),
    path('superadmin/yeni-dovr/', views.yeni_dovr_yarat, name='yeni_dovr_yarat'),
    path('superadmin/export-excel/', views.export_departments_excel, name='export_departments_excel'),
    path('superadmin/export-pdf/', views.export_departments_pdf, name='export_departments_pdf'),
    path('plan/yarat/<int:ishchi_id>/<int:dovr_id>/', views.plan_yarat_ve_redakte_et, name='plan_yarat'),
    path('plan/bax/<int:plan_id>/', views.plan_bax, name='plan_bax'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
]
    # Uncomment the following lines if you want to enable these views
    # path('superadmin/dovrlar/', views.dovrlar_siyahisi, name='dovrlar_siyahisi'),
    # path('superadmin/dovrlar/sil/<int:dovr_id>/', views.dovr_sil, name='dovr_sil'),
    # path('superadmin/dovrlar/duzenle/<int:dovr_id>/', views.dovr_duzenle, name='dovr_duzenle'),
    # path('superadmin/ishciler/', views.ishciler_siyahisi, name='ishciler_siyahisi'),
    # path('superadmin/ishciler/sil/<int:ishchi_id>/', views.ishci_sil, name='ishci_sil'),
    # path('superadmin/ishciler/duzenle/<int:ishchi_id>/', views.ishci_duzenle, name='ishci_duzenle'),
    # path('superadmin/ishciler/yeni/', views.yeni_ishci_yarat, name='yeni_ishci_yarat'),
    # path('superadmin/hesabatlar/', views.hesabatlar_siyahisi, name='hesabatlar_siyahisi'),
    # path('superadmin/hesabatlar/sil/<int:hesabat_id>/', views.hesabat_sil, name='hesabat_sil'),
    # path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/', views.hesabat_duzenle, name='hesabat_duzenle'),
    # path('superadmin/hesabatlar/yeni/', views.yeni_hesabat_yarat, name='yeni_hesabat_yarat'),
    # path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/', views.hesabat_pdf_duzenle, name='hesabat_pdf_duzenle'),
    # path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/sil/', views.hesabat_pdf_sil, name='hesabat_pdf_sil'),
    # path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/yukle/', views.hesabat_pdf_yukle, name='hesabat_pdf_yukle'),
    # path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/duzenle/', views.hesabat_pdf_duzenle, name='hesabat_pdf_duzenle'),
    # path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/yukle/', views.hesabat_pdf_yukle, name='hesabat_pdf_yukle'),
    # path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/sil/', views.hesabat_pdf_sil, name='hesabat_pdf_sil'),