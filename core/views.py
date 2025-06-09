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