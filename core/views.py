# core/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import (
    Qiymetlendirme, Sual, Cavab, QiymetlendirmeDovru, 
    Ishchi, SualKateqoriyasi
)

# --- KÖMƏKÇİ FUNKSİYA ---
# Kod təkrarının qarşısını almaq üçün hesabat məlumatlarını hazırlayan funksiya

def _generate_report_context(ishchi):
    """Verilən işçi üçün hesabat məlumatlarını hazırlayan köməkçi funksiya."""
    dovr = QiymetlendirmeDovru.objects.order_by('-bitme_tarixi').first()
    if not dovr:
        return {'error': "Sistemdə heç bir qiymətləndirmə dövrü tapılmadı."}

    cavablar = Cavab.objects.filter(
        qiymetlendirme__qiymetlendirilen=ishchi,
        qiymetlendirme__dovr=dovr
    )
    
    if not cavablar.exists():
        return {'error': f"'{dovr.ad}' dövrü üçün {ishchi.get_full_name()} haqqında qiymətləndirmə tamamlanmayıb."}

    kateqoriya_neticeleri = SualKateqoriyasi.objects.filter(
        sual__cavab__in=cavablar
    ).annotate(
        ortalama_xal=Avg('sual__cavab__xal')
    ).distinct().order_by('ad')

    yazili_reyler = cavablar.exclude(metnli_rey__isnull=True).exclude(metnli_rey__exact='').values_list('metnli_rey', flat=True)

    chart_labels = [k.ad for k in kateqoriya_neticeleri]
    chart_data = [round(k.ortalama_xal, 2) for k in kateqoriya_neticeleri]

    return {
        'ishchi': ishchi,
        'dovr': dovr,
        'kateqoriya_neticeleri': kateqoriya_neticeleri,
        'yazili_reyler': yazili_reyler,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'error': None
    }


# --- ÜMUMİ İSTİFADƏÇİ GÖRÜNÜŞLƏRİ (VIEW-LARI) ---

@login_required
def dashboard(request):
    """İstifadəçinin qiymətləndirmə tapşırıqlarını göstərən ana səhifə."""
    qiymetlendirmeler = Qiymetlendirme.objects.filter(
        qiymetlendiren=request.user,
        status='GOZLEMEDE'
    ).select_related('qiymetlendirilen', 'dovr')
    
    context = {
        'qiymetlendirmeler': qiymetlendirmeler
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def qiymetlendirme_etmek(request, qiymetlendirme_id):
    """Qiymətləndirmə formunun göstərilməsi və təsdiqlənməsi."""
    qiymetlendirme = get_object_or_404(Qiymetlendirme, id=qiymetlendirme_id)

    if qiymetlendirme.qiymetlendiren != request.user:
        return HttpResponseForbidden("Bu səhifəyə giriş icazəniz yoxdur.")
    
    if qiymetlendirme.status == 'TAMAMLANDI':
        messages.warning(request, "Bu qiymətləndirmə artıq tamamlanıb.")
        return redirect('dashboard')

    ishchi = qiymetlendirme.qiymetlendirilen
    suallar = Sual.objects.filter(
        Q(departament__isnull=True, shobe__isnull=True, sektor__isnull=True) |
        Q(departament=ishchi.sektor.shobe.departament) |
        Q(shobe=ishchi.sektor.shobe) |
        Q(sektor=ishchi.sektor)
    ).distinct()

    if request.method == 'POST':
        for sual in suallar:
            xal_key = f'xal_{sual.id}'
            rey_key = f'rey_{sual.id}'
            
            xal = request.POST.get(xal_key)
            rey = request.POST.get(rey_key, '')

            if xal:
                Cavab.objects.create(
                    qiymetlendirme=qiymetlendirme,
                    sual=sual,
                    xal=int(xal),
                    metnli_rey=rey
                )
        
        qiymetlendirme.status = 'TAMAMLANDI'
        qiymetlendirme.save()

        messages.success(request, f"{ishchi.get_full_name()} üçün qiymətləndirmə uğurla tamamlandı.")
        return redirect('dashboard')

    context = {
        'qiymetlendirme': qiymetlendirme,
        'suallar': suallar,
    }
    return render(request, 'core/qiymetlendirme_form.html', context)


@login_required
def hesabat_sehifesi(request):
    """İstifadəçinin öz hesabatına baxması üçün."""
    context = _generate_report_context(request.user)
    
    if context.get('error'):
        messages.warning(request, context['error'])
        return redirect('dashboard')
        
    return render(request, 'core/hesabat.html', context)


# --- RƏHBƏR ÜÇÜN XÜSUSİ GÖRÜNÜŞLƏR (VIEW-LAR) ---

@login_required
def rehber_paneli(request):
    """Rəhbərin öz komanda üzvlərini gördüyü panel."""
    if request.user.rol != 'REHBER':
        return HttpResponseForbidden("Bu səhifəyə yalnız rəhbərlər daxil ola bilər.")

    tabe_olan_ishchiler = []
    if request.user.sektor:
        tabe_olan_ishchiler = Ishchi.objects.filter(
            sektor=request.user.sektor
        ).exclude(id=request.user.id)

    context = {
        'tabe_olan_ishchiler': tabe_olan_ishchiler
    }
    return render(request, 'core/rehber_paneli.html', context)


@login_required
def hesabat_bax(request, ishchi_id):
    """Rəhbərin tabeliyində olan işçinin hesabatına baxması."""
    if request.user.rol != 'REHBER':
        return HttpResponseForbidden("Bu səhifəyə yalnız rəhbərlər daxil ola bilər.")

    hedef_ishchi = get_object_or_404(Ishchi, id=ishchi_id)

    if hedef_ishchi.sektor != request.user.sektor:
        return HttpResponseForbidden("Siz yalnız öz komandanızdakı işçilərin hesabatına baxa bilərsiniz.")

    context = _generate_report_context(hedef_ishchi)
    
    if context.get('error'):
        messages.warning(request, context['error'])
        return redirect('rehber_paneli')
        
    return render(request, 'core/hesabat.html', context)


@login_required
def hesabat_pdf_yukle(request, ishchi_id):
    """Hesabatı PDF formatında generasiya edib yükləməni təmin edir."""
    
    # Hesabatına baxılan işçini tapırıq
    ishchi = get_object_or_404(Ishchi, id=ishchi_id)

    # Səlahiyyət yoxlanışı: Yalnız işçinin özü və ya onun rəhbəri baxa bilər
    is_rehber = (request.user.rol == 'REHBER' and request.user.sektor == ishchi.sektor)
    is_self = (request.user.id == ishchi.id)

    if not (is_rehber or is_self):
        return HttpResponseForbidden("Bu hesabatı yükləmək üçün icazəniz yoxdur.")

    # Daha əvvəl yaratdığımız köməkçi funksiya ilə hesabat məlumatlarını alırıq
    context = _generate_report_context(ishchi)

    if context.get('error'):
        messages.error(request, context['error'])
        return redirect('dashboard')
    
    # HTML şablonunu məlumatlarla birlikdə render edib string-ə çeviririk
    html_string = render_to_string('core/hesabat_pdf.html', context)
    
    # WeasyPrint ilə HTML string-dən PDF yaradırıq
    pdf_file = HTML(string=html_string).write_pdf()
    
    # Brauzerə PDF faylı olaraq göndəririk
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="hesabat_{ishchi.username}.pdf"'
    
    return response