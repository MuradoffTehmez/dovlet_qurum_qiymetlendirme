# core/utils.py

import json

from django.db.models import Avg

from .models import Cavab, QiymetlendirmeDovru, SualKateqoriyasi


def get_performance_trend(ishchi):
    """İşçinin bütün dövrlər üzrə performans trendini hesablayır."""
    dovrler = (
        QiymetlendirmeDovru.objects.filter(
            qiymetlendirme__qiymetlendirilen=ishchi, qiymetlendirme__status="TAMAMLANDI"
        )
        .distinct()
        .order_by("bashlama_tarixi")
    )

    trend_data = {}
    for dovr in dovrler:
        ortalama_xal = Cavab.objects.filter(
            qiymetlendirme__qiymetlendirilen=ishchi, qiymetlendirme__dovr=dovr
        ).aggregate(ortalama=Avg("xal"))["ortalama"]

        if ortalama_xal is not None:
            trend_data[dovr.ad] = round(ortalama_xal, 2)

    return trend_data, dovrler



def get_detailed_report_context(ishchi, dovr):
    """Verilən işçi və dövr üçün detallı hesabat məlumatlarını hazırlayır."""
    qiymetlendirmeler = Qiymetlendirme.objects.filter(
        qiymetlendirilen=ishchi,
        dovr=dovr,
        status='TAMAMLANDI'
    ).select_related('qiymetlendiren')

    if not qiymetlendirmeler.exists():
        return {'error': f"'{dovr.ad}' dövrü üçün {ishchi.get_full_name()} haqqında heç bir tamamlanmış qiymətləndirmə tapılmadı."}

    # Bütün kateqoriyaları əvvəlcədən alırıq
    kateqoriyalar = SualKateqoriyasi.objects.all()
    gap_analysis_data = []
    
    for cat in kateqoriyalar:
        # Həmin kateqoriyadakı cavabları tapırıq
        cavablar = Cavab.objects.filter(
            qiymetlendirme__in=qiymetlendirmeler,
            sual__kateqoriya=cat
        )

        if not cavablar.exists():
            continue

        # Özünüqiymətləndirmə balı
        self_avg = cavablar.filter(
            qiymetlendirme__qiymetlendiren=ishchi
        ).aggregate(ortalama=Avg('xal'))['ortalama'] or 0

        # Başqalarının verdiyi ortalama bal
        others_avg = cavablar.exclude(
            qiymetlendirme__qiymetlendiren=ishchi
        ).aggregate(ortalama=Avg('xal'))['ortalama'] or 0
        
        gap_analysis_data.append({
            'kateqoriya': cat.ad,
            'oz_qiymeti': round(self_avg, 2),
            'bashqalarinin_qiymeti': round(others_avg, 2),
            'ferq': round(self_avg - others_avg, 2)
        })

    yazili_reyler = Cavab.objects.filter(qiymetlendirme__in=qiymetlendirmeler).exclude(metnli_rey__isnull=True).exclude(metnli_rey__exact='').values_list('metnli_rey', flat=True)

    # Radar Chart üçün ümumi ortalamanı hesablayırıq
    radar_chart_data = [{'ad': item['kateqoriya'], 'ortalama_xal': item['bashqalarinin_qiymeti']} for item in gap_analysis_data if item['bashqalarinin_qiymeti'] > 0]

    return {
        'ishchi': ishchi, 'dovr': dovr, 
        'gap_analysis_data': gap_analysis_data,
        'yazili_reyler': yazili_reyler, 
        'chart_labels': json.dumps([item['ad'] for item in radar_chart_data]),
        'chart_data': json.dumps([item['ortalama_xal'] for item in radar_chart_data]),
        'error': None
    }