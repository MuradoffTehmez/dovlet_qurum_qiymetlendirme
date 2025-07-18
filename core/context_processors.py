# core/context_processors.py

from django.utils.translation import get_language
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from .models import Qiymetlendirme, QiymetlendirmeDovru, Ishchi

# dil dəyişdirmə menyusu üçün kontekst prosessoru
def language_switcher_context(request):
    """
    Bütün şablonlara dil dəyişdirmə menyusu üçün
    hazır məlumat ötürən kontekst prosessoru.
    """
    current_lang_code = get_language()

    languages = [
        {"code": "az", "name": "Azərbaycan"},
        {"code": "en", "name": "English"},
    ]

    processed_languages = []
    for lang in languages:
        processed_languages.append(
            {
                "code": lang["code"],
                "name": lang["name"],
                "is_current": lang["code"] == current_lang_code,
            }
        )

    return {"language_switcher_data": processed_languages}


def global_context(request):
    """
    Bütün səhifələr üçün ümumi kontekst məlumatları
    """
    context = {
        'site_name': 'Qiymətləndirmə Sistemi',
        'site_version': '2.0',
        'current_year': timezone.now().year,
        'debug': settings.DEBUG,
    }
    
    # İstifadəçi giriş etmişsə, onun statistikasını əlavə et
    if request.user.is_authenticated:
        try:
            # Aktiv qiymətləndirmələr
            pending_evaluations = Qiymetlendirme.objects.filter(
                qiymetlendiren=request.user,
                status='GOZLEMEDE'
            ).count()
            
            # Tamamlanmış qiymətləndirmələr
            completed_evaluations = Qiymetlendirme.objects.filter(
                qiymetlendiren=request.user,
                status='TAMAMLANDI'
            ).count()
            
            # Ümumi statistika
            context.update({
                'pending_evaluations_count': pending_evaluations,
                'completed_evaluations_count': completed_evaluations,
                'total_evaluations_count': pending_evaluations + completed_evaluations,
                'user_has_pending_tasks': pending_evaluations > 0,
            })
            
            # Rəhbər və ya admin üçün əlavə statistika
            if request.user.rol == 'REHBER' or request.user.is_superuser:
                if request.user.organization_unit:
                    team_members = Ishchi.objects.filter(
                        organization_unit=request.user.organization_unit
                    ).exclude(id=request.user.id).count()
                    
                    context.update({
                        'team_members_count': team_members,
                        'is_manager': True,
                    })
                    
            # Superadmin üçün sistem statistikası
            if request.user.is_superuser:
                active_dovr = QiymetlendirmeDovru.objects.filter(
                    baslama_tarixi__lte=timezone.now().date(),
                    bitme_tarixi__gte=timezone.now().date()
                ).first()
                
                if active_dovr:
                    total_system_evaluations = Qiymetlendirme.objects.filter(
                        dovr=active_dovr
                    ).count()
                    
                    completed_system_evaluations = Qiymetlendirme.objects.filter(
                        dovr=active_dovr,
                        status='TAMAMLANDI'
                    ).count()
                    
                    completion_rate = 0
                    if total_system_evaluations > 0:
                        completion_rate = (completed_system_evaluations / total_system_evaluations) * 100
                    
                    context.update({
                        'system_completion_rate': round(completion_rate, 1),
                        'system_total_evaluations': total_system_evaluations,
                        'system_completed_evaluations': completed_system_evaluations,
                        'active_cycle': active_dovr,
                    })
                    
        except Exception as e:
            # Xəta baş verərsə, sadə kontekst qaytar
            pass
    
    return context


def notification_context(request):
    """
    Bildiriş konteksti
    """
    if not request.user.is_authenticated:
        return {}
    
    notifications = []
    
    try:
        # Gözləməkdə olan qiymətləndirmələr
        pending_evaluations = Qiymetlendirme.objects.filter(
            qiymetlendiren=request.user,
            status='GOZLEMEDE'
        ).select_related('qiymetlendirilen', 'dovr')
        
        for evaluation in pending_evaluations:
            notifications.append({
                'type': 'evaluation_pending',
                'message': f'{evaluation.qiymetlendirilen.get_full_name()} üçün qiymətləndirmə gözləyir',
                'url': f'/qiymetlendirme/{evaluation.id}/',
                'icon': 'bi-clipboard-check',
                'priority': 'high' if evaluation.dovr.bitme_tarixi <= timezone.now().date() else 'medium'
            })
        
        # Müddəti bitməyə yaxın olan qiymətləndirmələr
        upcoming_deadlines = Qiymetlendirme.objects.filter(
            qiymetlendiren=request.user,
            status='GOZLEMEDE',
            dovr__bitme_tarixi__lte=timezone.now().date() + timezone.timedelta(days=7)
        ).select_related('dovr')
        
        for evaluation in upcoming_deadlines:
            days_left = (evaluation.dovr.bitme_tarixi - timezone.now().date()).days
            if days_left <= 3:
                notifications.append({
                    'type': 'deadline_warning',
                    'message': f'Qiymətləndirmə müddəti {days_left} gün sonra bitir',
                    'url': f'/qiymetlendirme/{evaluation.id}/',
                    'icon': 'bi-exclamation-triangle',
                    'priority': 'high'
                })
        
    except Exception as e:
        # Xəta baş verərsə, boş bildiriş qaytarırıq
        pass
    
    return {
        'notifications': notifications,
        'notification_count': len(notifications)
    }
