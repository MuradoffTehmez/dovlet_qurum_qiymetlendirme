# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
import json
from datetime import datetime, timedelta

from .models import (
    Ishchi, Qiymetlendirme, QiymetlendirmeDovru, Sual, Cavab,
    InkishafPlani, Hedef, OrganizationUnit, Notification,
    RiskFlag, EmployeeRiskAnalysis
)
from .forms import ProfileUpdateForm, QeydiyyatFormu
from .decorators import user_passes_test_with_message


class CustomLoginView(LoginView):
    """Custom login view with additional functionality"""
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Xoş gəlmisiniz, {self.request.user.get_full_name()}!')
        return response


@login_required
def dashboard(request):
    """Ana dashboard səhifəsi"""
    user = request.user
    
    # Basic statistics
    stats = {
        'total_evaluations': 0,
        'completed_evaluations': 0,
        'pending_evaluations': 0,
        'development_plans': 0,
        'active_risk_flags': 0,
        'notifications_count': 0
    }
    
    try:
        # Get user-specific statistics
        if user.rol in ['superadmin', 'hr', 'manager']:
            # Manager/HR view - see all data
            stats['total_evaluations'] = Qiymetlendirme.objects.count()
            stats['completed_evaluations'] = Qiymetlendirme.objects.filter(status='COMPLETED').count()
            stats['pending_evaluations'] = Qiymetlendirme.objects.filter(status='PENDING').count()
            stats['development_plans'] = InkishafPlani.objects.count()
            stats['active_risk_flags'] = RiskFlag.objects.filter(status='ACTIVE').count()
        else:
            # Regular user view - see only their data
            stats['completed_evaluations'] = Qiymetlendirme.objects.filter(
                qiymetlendirilen=user, status='COMPLETED'
            ).count()
            stats['pending_evaluations'] = Qiymetlendirme.objects.filter(
                qiymetlendirilen=user, status='PENDING'
            ).count()
            stats['development_plans'] = InkishafPlani.objects.filter(ishchi=user).count()
        
        stats['notifications_count'] = Notification.objects.filter(
            recipient=user, is_read=False
        ).count()
        
    except Exception as e:
        # If there's an error, continue with default stats
        pass
    
    # Recent notifications
    recent_notifications = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_notifications': recent_notifications,
        'user_role': user.rol,
        'is_manager': user.rol in ['manager', 'hr', 'superadmin'],
        'page_title': 'Ana Səhifə'
    }
    
    return render(request, 'core/dashboard.html', context)


def qeydiyyat_sehifesi(request):
    """User registration page"""
    if request.method == 'POST':
        form = QeydiyyatFormu(request.POST)
        if form.is_valid():
            user = form.save()
            # Send activation email if configured
            messages.success(request, 'Qeydiyyat uğurla tamamlandı!')
            return redirect('login')
    else:
        form = QeydiyyatFormu()
    
    return render(request, 'registration/qeydiyyat.html', {'form': form})


@login_required
def qiymetlendirme_etmek(request, qiymetlendirme_id):
    """Evaluation form"""
    qiymetlendirme = get_object_or_404(Qiymetlendirme, id=qiymetlendirme_id)
    
    # Check permissions
    if request.user != qiymetlendirme.qiymetlendiren:
        messages.error(request, 'Bu qiymətləndirməni etmək icazəniz yoxdur.')
        return redirect('dashboard')
    
    context = {
        'qiymetlendirme': qiymetlendirme,
        'page_title': 'Qiymətləndirmə'
    }
    
    return render(request, 'core/qiymetlendirme.html', context)


@login_required
def hesabat_gorunumu(request, ishchi_id=None):
    """Report view"""
    if ishchi_id:
        ishchi = get_object_or_404(Ishchi, id=ishchi_id)
        # Check permissions
        if request.user.rol not in ['manager', 'hr', 'superadmin'] and request.user != ishchi:
            messages.error(request, 'Bu hesabata baxmaq icazəniz yoxdur.')
            return redirect('dashboard')
    else:
        ishchi = request.user
    
    context = {
        'ishchi': ishchi,
        'page_title': 'Hesabat'
    }
    
    return render(request, 'core/hesabat.html', context)


@login_required
def hesabat_pdf_yukle(request, ishchi_id):
    """Download PDF report"""
    ishchi = get_object_or_404(Ishchi, id=ishchi_id)
    
    # Check permissions
    if request.user.rol not in ['manager', 'hr', 'superadmin'] and request.user != ishchi:
        messages.error(request, 'Bu hesabatı yükləmək icazəniz yoxdur.')
        return redirect('dashboard')
    
    # Generate PDF (implement PDF generation logic here)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="hesabat_{ishchi.get_full_name()}.pdf"'
    
    # Add PDF content here
    response.write(b'PDF content placeholder')
    
    return response


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    """User profile view"""
    
    def get(self, request):
        form = ProfileUpdateForm(instance=request.user)
        context = {
            'form': form,
            'page_title': 'Profil'
        }
        return render(request, 'core/profil.html', context)
    
    def post(self, request):
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil məlumatları yeniləndi!')
            return redirect('profil')
        
        context = {
            'form': form,
            'page_title': 'Profil'
        }
        return render(request, 'core/profil.html', context)


@login_required
@user_passes_test_with_message(
    lambda u: u.rol in ['manager', 'hr', 'superadmin'],
    "Bu səhifəyə giriş yalnız rəhbər və HR istifadəçilərinə açıqdır."
)
def rehber_paneli(request):
    """Manager panel"""
    context = {
        'page_title': 'Rəhbər Paneli'
    }
    return render(request, 'core/rehber_paneli.html', context)


@login_required
@user_passes_test_with_message(
    lambda u: u.rol == 'superadmin',
    "Bu səhifəyə giriş yalnız superadmin istifadəçilərinə açıqdır."
)
def superadmin_paneli(request):
    """Superadmin panel"""
    context = {
        'page_title': 'Superadmin Paneli'
    }
    return render(request, 'core/superadmin_paneli.html', context)


@login_required
@user_passes_test_with_message(
    lambda u: u.rol == 'superadmin',
    "Bu əməliyyatı yalnız superadmin edə bilər."
)
def yeni_dovr_yarat(request):
    """Create new evaluation cycle"""
    if request.method == 'POST':
        # Implement cycle creation logic
        messages.success(request, 'Yeni dövr yaradıldı!')
        return redirect('superadmin_paneli')
    
    context = {
        'page_title': 'Yeni Dövr Yarat'
    }
    return render(request, 'core/yeni_dovr.html', context)


@login_required
@user_passes_test_with_message(
    lambda u: u.rol in ['manager', 'hr', 'superadmin'],
    "Bu əməliyyatı etmək icazəniz yoxdur."
)
def export_departments_excel(request):
    """Export departments to Excel"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="departmentler.xlsx"'
    
    # Implement Excel export logic here
    response.write(b'Excel content placeholder')
    
    return response


@login_required
@user_passes_test_with_message(
    lambda u: u.rol in ['manager', 'hr', 'superadmin'],
    "Bu əməliyyatı etmək icazəniz yoxdur."
)
def export_departments_pdf(request):
    """Export departments to PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="departmentler.pdf"'
    
    # Implement PDF export logic here
    response.write(b'PDF content placeholder')
    
    return response


@login_required
def plan_yarat_ve_redakte_et(request, ishchi_id, dovr_id):
    """Create or edit development plan"""
    ishchi = get_object_or_404(Ishchi, id=ishchi_id)
    dovr = get_object_or_404(QiymetlendirmeDovru, id=dovr_id)
    
    # Check permissions
    if request.user.rol not in ['manager', 'hr', 'superadmin'] and request.user != ishchi:
        messages.error(request, 'Bu plana dəyişiklik etmək icazəniz yoxdur.')
        return redirect('dashboard')
    
    context = {
        'ishchi': ishchi,
        'dovr': dovr,
        'page_title': 'İnkişaf Planı'
    }
    
    return render(request, 'core/plan_yarat.html', context)


@login_required
def plan_bax(request, plan_id):
    """View development plan"""
    plan = get_object_or_404(InkishafPlani, id=plan_id)
    
    # Check permissions
    if request.user.rol not in ['manager', 'hr', 'superadmin'] and request.user != plan.ishchi:
        messages.error(request, 'Bu plana baxmaq icazəniz yoxdur.')
        return redirect('dashboard')
    
    context = {
        'plan': plan,
        'page_title': 'İnkişaf Planı'
    }
    
    return render(request, 'core/plan_bax.html', context)


def activate(request, uidb64, token):
    """User account activation"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Ishchi.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Ishchi.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Hesabınız aktivləşdirildi! İndi giriş edə bilərsiniz.')
        return redirect('login')
    else:
        messages.error(request, 'Aktivləşdirmə linki yanlış və ya müddəti bitib.')
        return redirect('login')