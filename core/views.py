# core/views.py 

import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg  
from django.http import HttpResponse
from django.contrib import messages
from weasyprint import HTML
from django.contrib.auth import login, authenticate
from django.core.exceptions import PermissionDenied
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from .forms import YeniDovrForm, IshchiCreationForm, HedefFormSet
from .models import InkishafPlani
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin



# Lokal importlar
from .models import (
    Qiymetlendirme, Sual, Cavab, QiymetlendirmeDovru,
    Ishchi, Departament, SualKateqoriyasi, Hedef 
)
from .forms import YeniDovrForm, IshchiCreationForm
from .decorators import rehber_required, superadmin_required
from .utils import get_performance_trend, get_detailed_report_context


# --- ÜMUMİ VƏ QEYDİYYAT GÖRÜNÜŞLƏRİ ---

@login_required
def dashboard(request):
    """İstifadəçinin aktiv qiymətləndirmə tapşırıqlarını və inkişaf planını göstərir."""
    
    # Aktiv qiymətləndirmə tapşırıqları
    qiymetlendirmeler = Qiymetlendirme.objects.filter(
        qiymetlendiren=request.user, status='GOZLEMEDE'
    ).select_related('qiymetlendirilen', 'dovr')
    
    # İstifadəçinin aktiv inkişaf planını tapırıq
    aktiv_plan = InkishafPlani.objects.filter(ishchi=request.user, status='AKTIV').select_related('dovr').first()
    
    context = {
        'qiymetlendirmeler': qiymetlendirmeler,
        'aktiv_plan': aktiv_plan,
    }
    return render(request, 'core/dashboard.html', context)

# core/views.py

def qeydiyyat_sehifesi(request):
    """Yeni istifadəçiləri qeydiyyatdan keçirir və aktivasiya e-poçtu göndərir."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = IshchiCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Hesabı qeyri-aktiv edirik
            user.save()

            # Aktivasiya e-poçtunu hazırlayırıq
            mail_subject = 'Hesabınızı aktivləşdirin'
            
            # Mesajı HTML şablonundan render edirik
            message = render_to_string('registration/activation_email.html', {
                'user': user,
                'domain': request.META['HTTP_HOST'],
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.generate_token(user),
            })
            
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            
            try:
                email.send()
                messages.success(request, 'Qeydiyyat uğurla tamamlandı! Zəhmət olmasa, hesabınızı aktivləşdirmək üçün e-poçtunuzu yoxlayın.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f"E-poçt göndərilərkən xəta baş verdi: {e}")

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

# core/views.py

@login_required
def hesabat_gorunumu(request, ishchi_id=None):
    """
    Həm işçinin öz hesabatı, həm də rəhbərin işçinin hesabatına baxması üçün ortaq,
    təkmilləşdirilmiş view.
    """
    # 1. Hədəf işçini və icazələri müəyyən edirik
    if ishchi_id:
        hedef_ishchi = get_object_or_404(Ishchi, id=ishchi_id)
        # Rəhbər və ya Superuser-in icazəsini yoxlayırıq
        is_allowed_to_view = request.user.is_superuser or \
                             (request.user.rol == 'REHBER' and request.user.sektor == hedef_ishchi.sektor)
        if not is_allowed_to_view:
            raise PermissionDenied
    else:
        # İstifadəçi öz hesabatına baxır
        hedef_ishchi = request.user

    # 2. Performans trendini və mövcud dövrləri alırıq
    trend_data, all_user_cycles = get_performance_trend(hedef_ishchi)
    
    if not all_user_cycles:
        messages.warning(request, f"{hedef_ishchi.get_full_name()} üçün heç bir tamamlanmış qiymətləndirmə tapılmadı.")
        return redirect('dashboard' if not ishchi_id else 'rehber_paneli')
        
    # 3. Hansı dövrün hesabatının göstəriləcəyini təhlükəsiz şəkildə təyin edirik
    selected_dovr_id = request.GET.get('dovr_id', all_user_cycles.last().id)
    try:
        selected_dovr = get_object_or_404(QiymetlendirmeDovru, id=int(selected_dovr_id))
    except (ValueError, TypeError):
        selected_dovr = all_user_cycles.last()

    # 4. Detallı hesabat məlumatlarını alırıq
    detailed_context = get_detailed_report_context(hedef_ishchi, selected_dovr)

    # 5. Şablon üçün əlavə məntiqi dəyərləri hazırlayırıq
    # Rəhbər və ya superuser İnkişaf Planı yarada bilər
    can_manage_idp = (request.user.is_superuser or (request.user.rol == 'REHBER' and request.user.sektor == hedef_ishchi.sektor))
    # Bu işçi və dövr üçün planın olub-olmadığını yoxlayırıq
    movcud_plan = InkishafPlani.objects.filter(ishchi=hedef_ishchi, dovr=selected_dovr).first()
    
    cycles_for_template = [{'id': dovr.id, 'ad': dovr.ad, 'is_selected': dovr.id == selected_dovr.id} for dovr in all_user_cycles]

    # 6. Bütün məlumatları şablona göndəririk
    context = {
        'detailed_context': detailed_context,
        'cycles_for_template': cycles_for_template,
        'can_manage_idp': can_manage_idp,
        'movcud_plan': movcud_plan, # Planın olub-olmadığı barədə məlumat
        'trend_chart_labels': json.dumps(list(trend_data.keys())),
        'trend_chart_data': json.dumps(list(trend_data.values())),
    }
    
    return render(request, 'core/hesabat.html', context)

# --- RƏHBƏR VƏ SUPERADMIN GÖRÜNÜŞLƏRİ ---

@login_required
@rehber_required
def rehber_paneli(request):
    """Rəhbərin öz komandasını və komandanın ümumi statistikasını gördüyü panel."""
    
    tabe_olan_ishchiler = Ishchi.objects.none()
    team_competency_stats = {}
    
    # Rəhbərin sektoru varsa, tabeliyindəki işçiləri tapırıq
    if request.user.sektor:
        tabe_olan_ishchiler = Ishchi.objects.filter(
            sektor=request.user.sektor
        ).exclude(id=request.user.id)

    # Ən son qiymətləndirmə dövrünü tapırıq
    latest_dovr = QiymetlendirmeDovru.objects.order_by('-bitme_tarixi').first()

    if tabe_olan_ishchiler.exists() and latest_dovr:
        # Komandanın kompetensiyalar üzrə ortalama ballarını hesablayırıq
        categories = SualKateqoriyasi.objects.all()
        for cat in categories:
            avg_score = Cavab.objects.filter(
                qiymetlendirme__dovr=latest_dovr,
                qiymetlendirme__qiymetlendirilen__in=tabe_olan_ishchiler,
                sual__kateqoriya=cat
            ).aggregate(ortalama=Avg('xal'))['ortalama']
            
            if avg_score is not None:
                team_competency_stats[cat.ad] = round(avg_score, 2)
    
    context = {
        'tabe_olan_ishchiler': tabe_olan_ishchiler,
        'team_competency_stats': team_competency_stats,
        'chart_labels': json.dumps(list(team_competency_stats.keys())),
        'chart_data': json.dumps(list(team_competency_stats.values())),
    }
    return render(request, 'core/rehber_paneli.html', context)



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


# --- PDF İXRAÇLARI ---

@login_required
@superadmin_required
def export_departments_pdf(request):
    """Superadmin paneli üçün departament statistikasını PDF faylı olaraq ixrac edir."""
    
    dovr = QiymetlendirmeDovru.objects.order_by('-bitme_tarixi').first()
    if not dovr:
        messages.error(request, "Hesabat yaratmaq üçün heç bir qiymətləndirmə dövrü tapılmadı.")
        return redirect('superadmin_paneli')

    # Məlumatları alırıq (bu kod Excel ixracı ilə eynidir)
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

    # --- PDF Faylının Yaradılması ---
    context = {
        'departament_stat': departament_stat,
        'dovr': dovr,
    }

    # PDF üçün xüsusi bir HTML şablonu render edirik
    html_string = render_to_string('reports/summary_departments_pdf.html', context)
    
    # WeasyPrint ilə HTML-dən PDF yaradırıq
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    # Brauzerə PDF faylı olaraq göndəririk
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="departament_hesabati_{dovr.ad}.pdf"'
    
    return response

# --- FƏRDİ İNKİŞAF PLANI YARATMA VƏ REDAKTE ETMƏ ---

@login_required
@rehber_required
def plan_yarat_ve_redakte_et(request, ishchi_id, dovr_id):
    """
    Rəhbərin, işçi üçün verilmiş dövrə əsasən yeni bir İnkişaf Planı
    yaratması və ya mövcud olanı redaktə etməsi üçün.
    """
    ishchi = get_object_or_404(Ishchi, id=ishchi_id)
    dovr = get_object_or_404(QiymetlendirmeDovru, id=dovr_id)

    # Rəhbərin yalnız öz komandasına plan yaza bilməsini təmin edirik
    if not (request.user.is_superuser or (request.user.rol == 'REHBER' and request.user.sektor == ishchi.sektor)):
        raise PermissionDenied

    # Əgər bu işçi və dövr üçün plan artıq varsa, onu tapırıq. Yoxdursa, yenisini yaradırıq.
    plan, created = InkishafPlani.objects.get_or_create(ishchi=ishchi, dovr=dovr)
    
    formset = HedefFormSet(request.POST or None, instance=plan)

    if request.method == 'POST':
        if formset.is_valid():
            formset.save()
            messages.success(request, f"{ishchi.get_full_name()} üçün İnkişaf Planı uğurla yadda saxlanıldı.")
            # Rəhbəri həmin işçinin hesabat səhifəsinə geri yönləndiririk
            return redirect('hesabat_bax', ishchi_id=ishchi.id)

    context = {
        'formset': formset,
        'ishchi': ishchi,
        'dovr': dovr,
    }
    return render(request, 'core/plan_form.html', context)


# --- MÖVCUD FƏRDİ İNKİŞAF PLANINA BAXMA VƏ STATUS YENİLƏMƏ ---


@login_required
def plan_bax(request, plan_id):
    """Mövcud inkişaf planına baxmaq və statusları yeniləmək üçün."""
    plan = get_object_or_404(
        InkishafPlani.objects.select_related('ishchi', 'dovr').prefetch_related('hedefler'),
        id=plan_id
    )
    # Rəhbərin və ya işçinin planı görmək icazəsini yoxlayırıq
    try:
        rehber = Ishchi.objects.get(sektor=plan.ishchi.sektor, rol='REHBER')
    except (Ishchi.DoesNotExist, Ishchi.MultipleObjectsReturned):
        rehber = None

    is_allowed = (request.user == plan.ishchi or request.user == rehber or request.user.is_superuser)
    if not is_allowed:
        raise PermissionDenied

    is_plan_owner = (request.user == plan.ishchi)

    if request.method == 'POST' and is_plan_owner:
        hedef_id = request.POST.get('hedef_id')
        yeni_status = request.POST.get('status')
        if hedef_id and yeni_status and yeni_status in Hedef.Status.values:
            try:
                hedef = get_object_or_404(Hedef, id=int(hedef_id), plan=plan)
                hedef.status = yeni_status
                hedef.save(update_fields=['status'])
                messages.success(request, "Hədəfin statusu uğurla yeniləndi.")
            except (ValueError, TypeError):
                messages.error(request, "Xətalı sorğu.")
            return redirect('plan_bax', plan_id=plan.id)

    # Bütün məntiqi burada hazırlayırıq
    hedefler_with_choices = []
    for hedef in plan.hedefler.all():
        choices = []
        for key, value in Hedef.Status.choices:
            choices.append({
                'key': key,
                'value': value,
                'is_selected': hedef.status == key
            })
        hedefler_with_choices.append({
            'hedef_obj': hedef,
            'status_choices': choices
        })

    context = {
        'plan': plan,
        'is_plan_owner': is_plan_owner,
        'hedefler_with_choices': hedefler_with_choices,
    }
    return render(request, 'core/plan_detail.html', context)

# --- XÜSUSİ GİRİŞ VƏ "MƏNİ XATIRLA" FUNKSİYASI ---

# core/views.py
class CustomLoginView(LoginView):
    """ "Məni xatırla" funksionallığını əlavə edən xüsusi LoginView. """
    template_name = 'registration/login.html'
    authentication_form = AuthenticationForm

    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if not remember_me:
            # Əgər seçilməyibsə, sessiya brauzer bağlananda bitsin
            self.request.session.set_expiry(0)
        else:
            # Əgər seçilibsə, sessiya 30 gün aktiv qalsın (saniyə ilə)
            self.request.session.set_expiry(30 * 24 * 60 * 60)
        return super().form_valid(form)

# --- HESAB AKTİVLƏŞDİRMƏ ---
def activate(request, uidb64, token):
    """E-poçtdakı link vasitəsilə hesabı aktivləşdirir."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Ishchi.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Ishchi.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Təşəkkürlər! Hesabınız uğurla aktivləşdirildi. İndi daxil ola bilərsiniz.')
        return redirect('login')
    else:
        messages.error(request, 'Aktivasiya linki etibarsızdır!')
        return redirect('dashboard')



class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'core/profil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # GET sorğusu üçün formaları hazırlayırıq
        if 'info_form' not in context:
            context['info_form'] = IshchiUpdateForm(instance=self.request.user)
        if 'password_form' not in context:
            context['password_form'] = IshchiPasswordChangeForm(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        context = {}
        # Hansı formanın göndərildiyini düymənin adına görə yoxlayırıq
        if 'update_info' in request.POST:
            info_form = IshchiUpdateForm(request.POST, request.FILES, instance=request.user)
            if info_form.is_valid():
                info_form.save()
                messages.success(request, 'Profil məlumatlarınız uğurla yeniləndi!')
                return redirect('profil')
            else:
                context['info_form'] = info_form
        
        elif 'change_password' in request.POST:
            password_form = IshchiPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Şifrəniz uğurla dəyişdirildi!')
                return redirect('profil')
            else:
                context['password_form'] = password_form
        
        return self.render_to_response(self.get_context_data(**context))