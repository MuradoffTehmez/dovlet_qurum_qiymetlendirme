# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Qiymetlendirme, Sual, Cavab

@login_required
def dashboard(request):
    # İstifadəçinin qiymətləndirməli olduğu və hələ tamamlanmamış tapşırıqları tapırıq
    qiymetlendirmeler = Qiymetlendirme.objects.filter(
        qiymetlendiren=request.user,
        status='GOZLEMEDE'
    ).select_related('qiymetlendirilen', 'dovr') # Performans üçün optimizasiya
    
    context = {
        'qiymetlendirmeler': qiymetlendirmeler
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def qiymetlendirme_etmek(request, qiymetlendirme_id):
    qiymetlendirme = get_object_or_404(Qiymetlendirme, id=qiymetlendirme_id)

    # Yoxlayırıq ki, bu qiymətləndirmə həqiqətən bu istifadəçiyə aiddirmi
    if qiymetlendirme.qiymetlendiren != request.user:
        return HttpResponseForbidden("Bu səhifəyə giriş icazəniz yoxdur.")
    
    # Yoxlayırıq ki, bu qiymətləndirmə artıq tamamlanıbmı
    if qiymetlendirme.status == 'TAMAMLANDI':
        messages.warning(request, "Bu qiymətləndirmə artıq tamamlanıb.")
        return redirect('dashboard')

    # Qiymətləndirilən şəxsin strukturuna uyğun sualları seçirik
    ishchi = qiymetlendirme.qiymetlendirilen
    suallar = Sual.objects.filter(
        Q(departament__isnull=True, shobe__isnull=True, sektor__isnull=True) | # Ümumi suallar
        Q(departament=ishchi.sektor.shobe.departament) | # Departament sualları
        Q(shobe=ishchi.sektor.shobe) | # Şöbə sualları
        Q(sektor=ishchi.sektor) # Sektor sualları
    ).distinct()

    if request.method == 'POST':
        for sual in suallar:
            xal_key = f'xal_{sual.id}'
            rey_key = f'rey_{sual.id}'
            
            xal = request.POST.get(xal_key)
            rey = request.POST.get(rey_key, '') # Rəy boş ola bilər

            if xal: # Xal verilibsə cavabı yaradırıq
                Cavab.objects.create(
                    qiymetlendirme=qiymetlendirme,
                    sual=sual,
                    xal=int(xal),
                    metnli_rey=rey
                )
        
        # Bütün cavablar yaradıldıqdan sonra qiymətləndirmənin statusunu dəyişirik
        qiymetlendirme.status = 'TAMAMLANDI'
        qiymetlendirme.save()

        messages.success(request, f"{ishchi.get_full_name()} üçün qiymətləndirmə uğurla tamamlandı.")
        return redirect('dashboard')

    context = {
        'qiymetlendirme': qiymetlendirme,
        'suallar': suallar,
    }
    return render(request, 'core/qiymetlendirme_form.html', context)



# ... digər importların yanına "json" əlavə edin
import json
from django.db.models import Avg
from .models import QiymetlendirmeDovru, Cavab, SualKateqoriyasi # Model importlarına əlavə edin

# ... mövcud view-ların altında yeni funksiyanı yaradın

# core/views.py faylında hesabat_sehifesi funksiyasını bununla əvəz edin:

@login_required
def hesabat_sehifesi(request):
    ishchi = request.user
    dovr = None # Başlanğıcda dövrü boş təyin edirik

    try:
        # Ən son aktiv və ya bitmiş qiymətləndirmə dövrünü tapırıq
        dovr = QiymetlendirmeDovru.objects.order_by('-bitme_tarixi').first()
        if not dovr:
            # Əgər sistemdə heç bir dövr yoxdursa
            raise QiymetlendirmeDovru.DoesNotExist
    except QiymetlendirmeDovru.DoesNotExist:
        messages.error(request, "Sistemdə heç bir qiymətləndirmə dövrü tapılmadı.")
        return redirect('dashboard')

    # Həmin dövrdə bu işçi haqqında verilmiş bütün cavabları tapırıq
    cavablar = Cavab.objects.filter(
        qiymetlendirme__qiymetlendirilen=ishchi,
        qiymetlendirme__dovr=dovr
    )
    
    if not cavablar.exists():
        messages.warning(request, f"'{dovr.ad}' dövrü üçün sizin haqqınızda hələ heç bir qiymətləndirmə tamamlanmayıb.")
        return redirect('dashboard')

    # Kateqoriyalar üzrə ortalama xalların hesablanması
    kateqoriya_neticeleri = SualKateqoriyasi.objects.filter(
        sual__cavab__in=cavablar
    ).annotate(
        ortalama_xal=Avg('sual__cavab__xal')
    ).distinct().order_by('ad') # Səliqəli görünüş üçün əlifba sırası ilə

    # Yazılı rəylərin toplanması
    yazili_reyler = cavablar.exclude(metnli_rey__isnull=True).exclude(metnli_rey__exact='').values_list('metnli_rey', flat=True)

    # Diaqram üçün məlumatların hazırlanması
    chart_labels = [k.ad for k in kateqoriya_neticeleri]
    chart_data = [round(k.ortalama_xal, 2) for k in kateqoriya_neticeleri]

    context = {
        'ishchi': ishchi,
        'dovr': dovr,
        'kateqoriya_neticeleri': kateqoriya_neticeleri,
        'yazili_reyler': yazili_reyler,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'core/hesabat.html', context)