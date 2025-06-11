# core/views.py - SON VƏ DÜZGÜN VERSİYA

import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg  # <-- DÜZƏLİŞ BURADADIR: Avg import edildi
from django.http import HttpResponse
from django.contrib import messages
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

# Lokal importlar
from .models import (
    Qiymetlendirme, Sual, Cavab, QiymetlendirmeDovru,
    Ishchi, Departament, SualKateqoriyasi
)
from .forms import YeniDovrForm, IshchiCreationForm
from .decorators import rehber_required, superadmin_required
from .utils import get_performance_trend, get_detailed_report_context


# --- ÜMUMİ VƏ QEYDİYYAT GÖRÜNÜŞLƏRİ ---

@login_required
def dashboard(request):
    """İstifadəçinin aktiv qiymətləndirmə tapşırıqlarını göstərir."""
    qiymetlendirmeler = Qiymetlendirme.objects.filter(
        qiymetlendiren=request.user,
        status='GOZLEMEDE'
    ).select_related('qiymetlendirilen', 'dovr') # ORM Optimizasiyası
    
    return render(request, 'core/dashboard.html', {'qiymetlendirmeler': qiymetlendirmeler})


def qeydiyyat_sehifesi(request):
    """Yeni istifadəçilərin qeydiyyatdan keçməsini təmin edir."""
    if request.method == 'POST':
        form = IshchiCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Qeydiyyat uğurla tamamlandı. Xoş gəlmisiniz!")
            return redirect('dashboard')
    else:
        form = IshchiCreationForm()
    return render(request, 'registration/qeydiyyat_form.html', {'form': form})


@login_required
def qiymetlendirme_etmek(request, qiymetlendirme_id):
    """Qiymətləndirmə formasını göstərir və POST sorğularını emal edir."""
    qiymetlendirme = get_object_or_404(
        Qiymetlendirme.objects.select_related('qiymetlendirilen__sektor__shobe__departament'),
        id=qiymetlendirme_id
    )

    if qiymetlendirme.qiymetlendiren != request.user:
        raise PermissionDenied
    
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
            try:
                xal = int(request.POST.get(f'xal_{sual.id}'))
                rey = request.POST.get(f'rey_{sual.id}', '')
                Cavab.objects.create(qiymetlendirme=qiymetlendirme, sual=sual, xal=xal, metnli_rey=rey)
            except (ValueError, TypeError):
                continue
        
        qiymetlendirme.status = 'TAMAMLANDI'
        qiymetlendirme.save()
        messages.success(request, f"{ishchi.get_full_name()} üçün qiymətləndirmə uğurla tamamlandı.")
        return redirect('dashboard')

    return render(request, 'core/qiymetlendirme_form.html', {'qiymetlendirme': qiymetlendirme, 'suallar': suallar})


# --- HESABAT GÖRÜNÜŞLƏRİ ---

@login_required
def hesabat_gorunumu(request, ishchi_id=None):
    """Həm işçinin öz hesabatı, həm də rəhbərin işçinin hesabatına baxması üçün ortaq view."""
    if ishchi_id:
        hedef_ishchi = get_object_or_404(Ishchi, id=ishchi_id)
        if not (request.user.is_superuser or (request.user.rol == 'REHBER' and request.user.sektor == hedef_ishchi.sektor)):
            raise PermissionDenied
    else:
        hedef_ishchi = request.user

    trend_data, all_user_cycles = get_performance_trend(hedef_ishchi)
    
    if not all_user_cycles:
        messages.warning(request, f"{hedef_ishchi.get_full_name()} üçün heç bir tamamlanmış qiymətləndirmə tapılmadı.")
        return redirect('dashboard' if not ishchi_id else 'rehber_paneli')
        
    selected_dovr_id = request.GET.get('dovr_id')
    if selected_dovr_id:
        selected_dovr = get_object_or_404(QiymetlendirmeDovru, id=selected_dovr_id)
    else:
        selected_dovr = all_user_cycles.last()

    detailed_context = get_detailed_report_context(hedef_ishchi, selected_dovr)

    cycles_for_template = [{'id': dovr.id, 'ad': dovr.ad} for dovr in all_user_cycles]

    context = {
        'detailed_context': detailed_context,
        'cycles_for_template': cycles_for_template,
        'selected_dovr_id': selected_dovr.id if selected_dovr else None,
        'trend_chart_labels': json.dumps(list(trend_data.keys())),
        'trend_chart_data': json.dumps(list(trend_data.values())),
    }
    return render(request, 'core/hesabat.html', context)


# --- RƏHBƏR VƏ SUPERADMIN GÖRÜNÜŞLƏRİ ---

@login_required
@rehber_required
def rehber_paneli(request):
    """Rəhbərin öz komandasını gördüyü panel."""
    tabe_olan_ishchiler = []
    if request.user.sektor:
        tabe_olan_ishchiler = Ishchi.objects.filter(sektor=request.user.sektor).exclude(id=request.user.id)
    return render(request, 'core/rehber_paneli.html', {'tabe_olan_ishchiler': tabe_olan_ishchiler})


@login_required
@superadmin_required
def superadmin_paneli(request):
    """Bütün təşkilat üzrə ümumi statistikaları göstərən panel."""
    dovr = QiymetlendirmeDovru.objects.order_by('-bitme_tarixi').first()
    context = {'dovr': dovr}
    if dovr:
        total_qiymetlendirmeler = Qiymetlendirme.objects.filter(dovr=dovr)
        tamamlanmish_sayi = total_qiymetlendirmeler.filter(status='TAMAMLANDI').count()
        total_sayi = total_qiymetlendirmeler.count()
        tamamlama_faizi = (tamamlanmish_sayi / total_sayi) * 100 if total_sayi > 0 else 0
        context.update({'tamamlanmish_sayi': tamamlanmish_sayi, 'total_sayi': total_sayi, 'tamamlama_faizi': round(tamamlama_faizi, 2)})
        
        departamentler = Departament.objects.all()
        departament_stat = []
        for dep in departamentler:
            ortalama_bal = Cavab.objects.filter(qiymetlendirme__dovr=dovr, qiymetlendirme__qiymetlendirilen__sektor__shobe__departament=dep).aggregate(ortalama=Avg('xal'))['ortalama']
            departament_stat.append({'ad': dep.ad, 'ortalama_bal': round(ortalama_bal, 2) if ortalama_bal else 0})
        
        context['departament_stat'] = departament_stat
        context['chart_labels'] = json.dumps([item['ad'] for item in departament_stat])
        context['chart_data'] = json.dumps([item['ortalama_bal'] for item in departament_stat])
    return render(request, 'core/superadmin_paneli.html', context)


@login_required
@superadmin_required
def yeni_dovr_yarat(request):
    """Yeni qiymətləndirmə dövrünü və təyinatları avtomatik yaradır."""
    if request.method == 'POST':
        form = YeniDovrForm(request.POST)
        if form.is_valid():
            yeni_dovr = form.save()
            secilmish_departamentler = form.cleaned_data['departamentler']
            butun_ishchiler = Ishchi.objects.filter(is_active=True, sektor__shobe__departament__in=secilmish_departamentler).select_related('sektor')
            yeni_qiymetlendirmeler = []

            for ishchi in butun_ishchiler:
                # Özünüqiymətləndirmə
                yeni_qiymetlendirmeler.append(Qiymetlendirme(dovr=yeni_dovr, qiymetlendirilen=ishchi, qiymetlendiren=ishchi))
                
                # Rəhbər tərəfindən qiymətləndirmə
                try:
                    rehber = Ishchi.objects.get(sektor=ishchi.sektor, rol='REHBER')
                    if rehber != ishchi:
                        yeni_qiymetlendirmeler.append(Qiymetlendirme(dovr=yeni_dovr, qiymetlendirilen=ishchi, qiymetlendiren=rehber))
                except (Ishchi.DoesNotExist, Ishchi.MultipleObjectsReturned):
                    pass # Rəhbər yoxdursa və ya birdən çoxdursa, bu addımı ötürürük

                # Komanda yoldaşları tərəfindən qiymətləndirmə
                komanda_yoldashlari = list(butun_ishchiler.filter(sektor=ishchi.sektor).exclude(id=ishchi.id).exclude(rol='REHBER'))
                peer_sayi = min(len(komanda_yoldashlari), 2)
                secilmish_peerler = random.sample(komanda_yoldashlari, peer_sayi)
                for peer in secilmish_peerler:
                    yeni_qiymetlendirmeler.append(Qiymetlendirme(dovr=yeni_dovr, qiymetlendirilen=ishchi, qiymetlendiren=peer))

            Qiymetlendirme.objects.bulk_create(yeni_qiymetlendirmeler, ignore_conflicts=True)
            messages.success(request, f"'{yeni_dovr.ad}' dövrü yaradıldı və təyinatlar avtomatik generasiya edildi.")
            return redirect('superadmin_paneli')
    else:
        form = YeniDovrForm()
    return render(request, 'core/yeni_dovr_form.html', {'form': form})


# --- PDF YÜKLƏMƏ GÖRÜNÜŞÜ ---
@login_required
def hesabat_pdf_yukle(request, ishchi_id):
    ishchi = get_object_or_404(Ishchi, id=ishchi_id)
    is_rehber = (request.user.rol == 'REHBER' and request.user.sektor == ishchi.sektor)
    is_self = (request.user.id == ishchi.id)
    if not (request.user.is_superuser or is_rehber or is_self):
        raise PermissionDenied
    
    dovr_id = request.GET.get('dovr_id')
    if dovr_id:
        dovr = get_object_or_404(QiymetlendirmeDovru, id=dovr_id)
    else:
        dovr = QiymetlendirmeDovru.objects.filter(qiymetlendirme__qiymetlendirilen=ishchi, qiymetlendirme__status='TAMAMLANDI').distinct().order_by('-bitme_tarixi').first()
    
    if not dovr:
        messages.error(request, "Hesabat yaratmaq üçün heç bir qiymətləndirmə dövrü tapılmadı.")
        return redirect('dashboard')

    context = get_detailed_report_context(ishchi, dovr)
    if context.get('error'):
        messages.error(request, context['error'])
        return redirect('dashboard')
    
    html_string = render_to_string('core/hesabat_pdf.html', context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="hesabat_{ishchi.username}_{dovr.ad}.pdf"'
    return response


# --- EXCEL İXRAÇLARI ---

@login_required
@superadmin_required
def export_departments_excel(request):
    """Superadmin paneli üçün departament statistikasını Excel faylı olaraq ixrac edir."""
    
    # Ən son qiymətləndirmə dövrünü tapırıq
    dovr = QiymetlendirmeDovru.objects.order_by('-bitme_tarixi').first()
    if not dovr:
        messages.error(request, "Hesabat yaratmaq üçün heç bir qiymətləndirmə dövrü tapılmadı.")
        return redirect('superadmin_paneli')

    # Məlumatları yenidən hesablayırıq (superadmin_paneli view-undakı məntiqin təkrarı)
    departamentler = Departament.objects.all()
    departament_stat = []
    for dep in departamentler:
        ortalama_bal = Cavab.objects.filter(
            qiymetlendirme__dovr=dovr,
            qiymetlendirme__qiymetlendirilen__sektor__shobe__departament=dep
        ).aggregate(ortalama=Avg('xal'))['ortalama']
        departament_stat.append({
            'ad': dep.ad,
            'ortalama_bal': round(ortalama_bal, 2) if ortalama_bal else 0,
        })
        
    # --- Excel Faylının Yaradılması ---
    
    # Yeni bir Excel kitabı yaradırıq
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = f"{dovr.ad} - Departament Hesabatı"

    # Başlıq sətrini yaradırıq və stilləndiririk
    headers = ["Departament Adı", "Ortalama Bal"]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Məlumatları sətirlərə əlavə edirik
    for stat in departament_stat:
        sheet.append([stat['ad'], stat['ortalama_bal']])
    
    # Sütunların enini avtomatik tənzimləyirik
    sheet.column_dimensions['A'].width = 40
    sheet.column_dimensions['B'].width = 20

    # HTTP cavabını hazırlayırıq
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="departament_hesabati_{dovr.ad}.xlsx"'
    
    # Excel kitabını cavaba yazırıq
    workbook.save(response)
    
    return response