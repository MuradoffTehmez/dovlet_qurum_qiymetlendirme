# core/audit.py
"""
Q360 Layihəsi üçün Genişləndirilmiş Audit Logging Sistemi
Bütün kritik əməliyyatları izləyir və qeydə alır
"""

import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
import json

from .models import Ishchi, Qiymetlendirme, InkishafPlani, Hedef, Feedback

# Audit logger
audit_logger = logging.getLogger('audit')

class AuditLogManager:
    """Audit log əməliyyatlarını idarə edir"""
    
    @staticmethod
    def log_action(user, action_type, object_type, object_id=None, 
                   details=None, ip_address=None, user_agent=None):
        """
        Hər hansı bir əməliyyatı audit loguna yazır
        """
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user': str(user) if user and not isinstance(user, AnonymousUser) else 'Anonymous',
            'user_id': getattr(user, 'id', None) if user and not isinstance(user, AnonymousUser) else None,
            'action_type': action_type,
            'object_type': object_type,
            'object_id': object_id,
            'details': details or {},
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        audit_logger.info(json.dumps(log_data, ensure_ascii=False))
        
        # Redis-də son aktivlikləri saxla (real-time monitoring üçün)
        cache_key = f"recent_activity:{user.id if user and hasattr(user, 'id') else 'anonymous'}"
        recent_activities = cache.get(cache_key, [])
        recent_activities.insert(0, log_data)
        recent_activities = recent_activities[:10]  # Son 10 aktivlik
        cache.set(cache_key, recent_activities, 3600)  # 1 saat saxla
    
    @staticmethod
    def get_user_recent_activities(user, limit=10):
        """İstifadəçinin son aktivliklərini qaytarır"""
        cache_key = f"recent_activity:{user.id}"
        return cache.get(cache_key, [])[:limit]
    
    @staticmethod
    def get_system_stats():
        """Sistem statistikalarını qaytarır"""
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'total_users': Ishchi.objects.count(),
            'active_users_today': Ishchi.objects.filter(last_login__date=today).count(),
            'new_feedbacks_week': Feedback.objects.filter(created_at__date__gte=week_ago).count(),
            'total_evaluations': Qiymetlendirme.objects.count(),
            'active_plans': InkishafPlani.objects.filter(
                hedefler__status__in=['BASHLANMAYIB', 'ICRADA']
            ).distinct().count(),
        }
        
        return stats


# === SIGNAL RECEİVER-LAR ===

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """İstifadəçi girişi audit log"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLogManager.log_action(
        user=user,
        action_type='USER_LOGIN',
        object_type='AUTH',
        details={
            'login_method': 'web',
            'session_key': request.session.session_key[:10] if request.session.session_key else None
        },
        ip_address=ip_address,
        user_agent=user_agent
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """İstifadəçi çıxışı audit log"""
    if user and not isinstance(user, AnonymousUser):
        ip_address = get_client_ip(request)
        
        AuditLogManager.log_action(
            user=user,
            action_type='USER_LOGOUT',
            object_type='AUTH',
            details={'logout_method': 'web'},
            ip_address=ip_address
        )

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Uğursuz giriş cəhdi audit log"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLogManager.log_action(
        user=None,
        action_type='LOGIN_FAILED',
        object_type='AUTH',
        details={
            'attempted_username': credentials.get('username', ''),
            'failure_reason': 'invalid_credentials'
        },
        ip_address=ip_address,
        user_agent=user_agent
    )

@receiver(post_save, sender=Qiymetlendirme)
def log_evaluation_changes(sender, instance, created, **kwargs):
    """Qiymətləndirmə dəyişikliklərini audit log"""
    action_type = 'EVALUATION_CREATED' if created else 'EVALUATION_UPDATED'
    
    details = {
        'evaluation_id': instance.id,
        'employee': str(instance.qiymetlendirilen),
        'period': str(instance.dovr),
        'evaluation_type': instance.qiymetlendirme_novu,
        'created': created
    }
    
    # Current user məlumatını context-dən al
    user = getattr(instance, '_history_user', None) or getattr(instance, '_current_user', None)
    
    AuditLogManager.log_action(
        user=user,
        action_type=action_type,
        object_type='EVALUATION',
        object_id=instance.id,
        details=details
    )

@receiver(post_save, sender=InkishafPlani)
def log_development_plan_changes(sender, instance, created, **kwargs):
    """İnkişaf planı dəyişikliklərini audit log"""
    action_type = 'PLAN_CREATED' if created else 'PLAN_UPDATED'
    
    details = {
        'plan_id': instance.id,
        'employee': str(instance.ishchi),
        'goals_count': instance.hedefler.count(),
        'created': created
    }
    
    user = getattr(instance, '_history_user', None) or getattr(instance, '_current_user', None)
    
    AuditLogManager.log_action(
        user=user,
        action_type=action_type,
        object_type='DEVELOPMENT_PLAN',
        object_id=instance.id,
        details=details
    )

@receiver(post_save, sender=Feedback)
def log_feedback_activity(sender, instance, created, **kwargs):
    """Geri bildirim aktivliklərini audit log"""
    action_type = 'FEEDBACK_CREATED' if created else 'FEEDBACK_UPDATED'
    
    details = {
        'feedback_id': instance.id,
        'title': instance.title,
        'type': instance.feedback_type,
        'priority': instance.priority,
        'status': instance.status,
        'created': created
    }
    
    # Feedback yaradan və ya yeniləyən istifadəçi
    user = getattr(instance, '_current_user', None) or instance.user
    
    AuditLogManager.log_action(
        user=user,
        action_type=action_type,
        object_type='FEEDBACK',
        object_id=instance.id,
        details=details
    )

@receiver(post_save, sender=Ishchi)
def log_user_profile_changes(sender, instance, created, **kwargs):
    """İstifadəçi profil dəyişikliklərini audit log"""
    if created:
        action_type = 'USER_CREATED'
        details = {
            'username': instance.username,
            'email': instance.email,
            'role': instance.rol,
            'organization_unit': str(instance.organization_unit) if instance.organization_unit else None
        }
    else:
        action_type = 'USER_UPDATED'
        details = {
            'user_id': instance.id,
            'username': instance.username,
            'role': instance.rol,
            'is_active': instance.is_active
        }
    
    user = getattr(instance, '_history_user', None) or getattr(instance, '_current_user', None)
    
    AuditLogManager.log_action(
        user=user or instance,  # Özü profil yeniləyirsə
        action_type=action_type,
        object_type='USER_PROFILE',
        object_id=instance.id,
        details=details
    )

# === KÖMƏKÇI FUNKSİYALAR ===

def get_client_ip(request):
    """İstifadəçinin IP ünvanını qaytarır"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_custom_action(user, action_type, description, object_type='CUSTOM', 
                     object_id=None, additional_data=None, request=None):
    """
    Xüsusi əməliyyatları log etmək üçün ümumi funksiya
    
    Usage:
    log_custom_action(
        user=request.user,
        action_type='REPORT_GENERATED',
        description='PDF hesabat yaradıldı',
        object_type='REPORT',
        additional_data={'report_type': 'employee_performance'}
    )
    """
    details = {
        'description': description,
        'additional_data': additional_data or {}
    }
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLogManager.log_action(
        user=user,
        action_type=action_type,
        object_type=object_type,
        object_id=object_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )

def track_model_changes(user):
    """
    Dekorator: Model dəyişikliklərini izləmək üçün istifadəçi məlumatını əlavə edir
    
    Usage:
    @track_model_changes(request.user)
    def update_employee_profile(request, employee_id):
        employee = Ishchi.objects.get(id=employee_id)
        employee._current_user = request.user  # Audit üçün
        employee.save()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator