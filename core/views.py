# core/views.py - TAM VƏ SON VERSİYA
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import (
    Qiymetlendirme, Sual, Cavab, QiymetlendirmeDovru, 
    Ishchi, SualKateqoriyasi
)

# --- KÖMƏKÇİ FUNKSİYALAR ---

def _get_performance_trend(ishchi):
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


def _get_detailed_report_context(ishchi, dovr):
    cavablar = Cavab.objects.filter(
        qiymetlendirme__qiymetlendirilen=ishchi,
        qiymetlendirme__dovr=dovr,
        qiymetlendirme__status='TAMAMLANDI' # Yalnız tamamlanmışları hesaba alırıq
    )
    
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
        'ishchi': ishchi,
        'dovr': dovr,
        'kateqoriya_neticeleri': kateqoriya_neticeleri,
        'yazili_reyler': yazili_reyler,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'error': None
    }


# --- ÜMUMİ İSTİFADƏÇİ GÖRÜNÜŞLƏRİ ---

@login_required
def dashboard(request):
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
    ishchi = request.user
    trend_data, all_user_cycles = _get_performance_trend(ishchi)
    
    # Başlanğıcda heç bir hesabat yoxdursa
    if not all_user_cycles:
        messages.warning(request, "Haqqınızda heç bir tamamlanmış qiymətləndirmə tapılmadı.")
        return redirect('dashboard')
        
    selected_dovr_id = request.GET.get('dovr_id')
    if selected_dovr_id:
        selected_dovr = get_object_or_404(QiymetlendirmeDovru, id=selected_dovr_id)
    else:
        selected_dovr = all_user_cycles.last()

    detailed_context = _get_detailed_report_context(ishchi, selected_dovr)

    context = {
        'detailed_context': detailed_context,
        'all_user_cycles': all_user_cycles,
        'selected_dovr_id': selected_dovr.id if selected_dovr else None,
        'trend_chart_labels': json.dumps(list(trend_data.keys())),
        'trend_chart_data': json.dumps(list(trend_data.values())),
    }
    
    return render(request, 'core/hesabat.html', context)


# --- RƏHBƏR GÖRÜNÜŞLƏRİ ---

@login_required
def rehber_paneli(request):
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
    if request.user.rol != 'REHBER':
        return HttpResponseForbidden("Bu səhifəyə yalnız rəhbərlər daxil ola bilər.")

    hedef_ishchi = get_object_or_404(Ishchi, id=ishchi_id)

    if hedef_ishchi.sektor != request.user.sektor:
        return HttpResponseForbidden("Siz yalnız öz komandanızdakı işçilərin hesabatına baxa bilərsiniz.")

    trend_data, all_user_cycles = _get_performance_trend(hedef_ishchi)
    
    if not all_user_cycles:
        messages.warning(request, f"{hedef_ishchi.get_full_name()} üçün heç bir tamamlanmış qiymətləndirmə tapılmadı.")
        return redirect('rehber_paneli')

    selected_dovr_id = request.GET.get('dovr_id')
    if selected_dovr_id:
        selected_dovr = get_object_or_404(QiymetlendirmeDovru, id=selected_dovr_id)
    else:
        selected_dovr = all_user_cycles.last()

    detailed_context = _get_detailed_report_context(hedef_ishchi, selected_dovr)

    context = {
        'detailed_context': detailed_context,
        'all_user_cycles': all_user_cycles,
        'selected_dovr_id': selected_dovr.id if selected_dovr else None,
        'trend_chart_labels': json.dumps(list(trend_data.keys())),
        'trend_chart_data': json.dumps(list(trend_data.values())),
    }
    
    return render(request, 'core/hesabat.html', context)


# --- YARDIMÇI GÖRÜNÜŞ (PDF YÜKLƏMƏ) ---

@login_required
def hesabat_pdf_yukle(request, ishchi_id):
    ishchi = get_object_or_404(Ishchi, id=ishchi_id)

    is_rehber = (request.user.rol == 'REHBER' and request.user.sektor == ishchi.sektor)
    is_self = (request.user.id == ishchi.id)

    if not (is_rehber or is_self):
        return HttpResponseForbidden("Bu hesabatı yükləmək üçün icazəniz yoxdur.")

    dovr_id = request.GET.get('dovr_id')
    if dovr_id:
        dovr = get_object_or_404(QiymetlendirmeDovru, id=dovr_id)
    else:
        dovr = QiymetlendirmeDovru.objects.filter(qiymetlendirme__qiymetlendirilen=ishchi, qiymetlendirme__status='TAMAMLANDI').distinct().order_by('-bitme_tarixi').first()
    
    if not dovr:
        messages.error(request, "Hesabat yaratmaq üçün heç bir qiymətləndirmə dövrü tapılmadı.")
        return redirect('dashboard')

    context = _get_detailed_report_context(ishchi, dovr)

    if context.get('error'):
        messages.error(request, context['error'])
        return redirect('dashboard')
    
    html_string = render_to_string('core/hesabat_pdf.html', context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="hesabat_{ishchi.username}_{dovr.ad}.pdf"'
    
    return response