# core/utils.py

import json
from django.db.models import Avg
from .models import QiymetlendirmeDovru, Cavab, SualKateqoriyasi

def get_performance_trend(ishchi):
    """İşçinin bütün dövrlər üzrə performans trendini hesablayır."""
    dovrler = QiymetlendirmeDovru.objects.filter(
        qiymetlendirme__qiymetlendirilen=ishchi,
        qiymetlendirme__status='TAMAMLANDI'
    ).distinct().order_by('bashlama_tarixi')

    trend_data = {}
    for dovr in dovrler:
        ortalama_xal = Cavab.objects.filter(
            qiymetlendirme__qiymetlendirilen=ishchi,
            qiymetlendirme__dovr=dovr
        ).aggregate(ortalama=Avg('xal'))['ortalama']
        
        if ortalama_xal is not None:
            trend_data[dovr.ad] = round(ortalama_xal, 2)
            
    return trend_data, dovrler

def get_detailed_report_context(ishchi, dovr):
    """Verilən işçi və dövr üçün detallı hesabat məlumatlarını hazırlayır."""
    cavablar = Cavab.objects.filter(
        qiymetlendirme__qiymetlendirilen=ishchi,
        qiymetlendirme__dovr=dovr,
        qiymetlendirme__status='TAMAMLANDI'
    ).select_related('sual__kateqoriya') # ORM Optimizasiyası

    if not cavablar.exists():
        return {'error': f"'{dovr.ad}' dövrü üçün {ishchi.get_full_name()} haqqında heç bir tamamlanmış qiymətləndirmə tapılmadı."}

    kateqoriya_neticeleri = SualKateqoriyasi.objects.filter(
        sual__cavab__in=cavablar
    ).annotate(
        ortalama_xal=Avg('sual__cavab__xal')
    ).distinct().order_by('ad')

    yazili_reyler = cavablar.exclude(metnli_rey__isnull=True).exclude(metnli_rey__exact='').values_list('metnli_rey', flat=True)

    chart_labels = [k.ad for k in kateqoriya_neticeleri]
    chart_data = [round(k.ortalama_xal, 2) for k in kateqoriya_neticeleri]

    return {
        'ishchi': ishchi, 'dovr': dovr, 'kateqoriya_neticeleri': kateqoriya_neticeleri,
        'yazili_reyler': yazili_reyler, 'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data), 'error': None
    }