# core/utils.py

import json

from django.db.models import Avg

from .models import Cavab, QiymetlendirmeDovru, SualKateqoriyasi


def generate_recommendations(yazili_reyler):
    """
    Yazılı rəylər əsasında sadə açar sözlərə görə inkişaf tövsiyələri yaradır.
    """
    if not yazili_reyler:
        return ""

    recommendations = set() # Təkrarların qarşısını almaq üçün set istifadə edirik

    for rey in yazili_reyler:
        rey_lower = rey.lower()

        if "gecikmə" in rey_lower or "vaxtında" in rey_lower or "gecikir" in rey_lower:
            recommendations.add("- **Zamanın idarə edilməsi:** Tapşırıqların vaxtında təhvil verilməsi üçün Pomodoro və ya Kanban kimi planlaşdırma texnikalarını araşdırmaq tövsiyə olunur.")
        if "ünsiyyət" in rey_lower or "əlaqə" in rey_lower or "dinlə" in rey_lower:
            recommendations.add("- **Komanda ilə ünsiyyət:** Fikirləri daha aydın ifadə etmək və komanda yoldaşlarını aktiv dinləmək üçün effektiv kommunikasiya təlimlərində iştirak etmək faydalı olardı.")
        if "keyfiyyət" in rey_lower or "dəqiqlik" in rey_lower or "səhv" in rey_lower:
            recommendations.add("- **Dəqiqlik və keyfiyyət:** Təhvil verilən işlərdə detallara daha çox diqqət yetirmək və yoxlama siyahılarından (checklists) istifadə etmək tövsiyə olunur.")
        if "liderlik" in rey_lower or "təşəbbüs" in rey_lower or "təşəbbüskar" in rey_lower:
            recommendations.add("- **Liderlik və təşəbbüskarlıq:** Komanda daxilində daha çox məsuliyyət götürmək və yeni ideyalarla çıxış etmək üçün imkanlar axtarmaq lazımdır.")
        if "innovasiya" in rey_lower or "yaradıcı" in rey_lower or "yeni fikir" in rey_lower:
            recommendations.add("- **Yaradıcılıq və innovasiya:** Mövcud proseslərin təkmilləşdirilməsi üçün təkliflər vermək və beyin fırtınası sessiyalarına aktiv qatılmaq faydalı ola bilər.")
        if "məsuliyyət" in rey_lower:
            recommendations.add("- **Məsuliyyət:** Tapşırıqların icrasına tam sahiblənmək və nəticələr üçün cavabdehliyi dərk etmək vacibdir.")

    if not recommendations:
        return "- Ümumi peşəkar inkişaf üçün müntəzəm olaraq rəhbərdən geribildirim almaq və fərdi inkişaf planı üzərində işləmək tövsiyə olunur."

    return "\n".join(recommendations)



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