# core/notifications.py
"""
Q360 Bildiriş Sistemi Helper Funksiyaları
Bildiriş yaratma və göndərmə üçün avtomatlaşdırılmış funksiyalar
"""

from django.utils import timezone
from django.core.cache import cache
from .models import Notification, Ishchi, Qiymetlendirme, InkishafPlani, Hedef
from .tasks import send_notification_email_task
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    """Bildiriş idarəetmə meneceri"""
    
    @staticmethod
    def create_and_send(recipient, title, message, notification_type=None, 
                       priority=None, sender=None, action_url=None, 
                       action_text=None, send_email=False, expires_in_days=30):
        """
        Bildiriş yaradır və opsional olaraq e-poçt göndərir
        """
        try:
            # Bildiriş yarat
            notification = Notification.create_notification(
                recipient=recipient,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                sender=sender,
                action_url=action_url,
                action_text=action_text,
                expires_in_days=expires_in_days
            )
            
            # Cache-də unread count-u yenilə
            cache_key = f"unread_notifications:{recipient.id}"
            cache.delete(cache_key)
            
            # E-poçt göndər (əgər istənilirsə)
            if send_email and recipient.email:
                try:
                    send_notification_email_task.delay(
                        user_email=recipient.email,
                        notification_type='general_notification',
                        context={
                            'subject': title,
                            'title': title,
                        'message': message,
                        'action_url': action_url,
                        'action_text': action_text,
                        'user_name': recipient.get_full_name() or recipient.username
                    }
                    )
                except Exception as celery_error:
                    logger.error(f"Celery email xətası: {celery_error}")
                    # Redis problemi varsa, sync email göndər
                    from .tasks import send_notification_email_sync
                    send_notification_email_sync(
                        user_email=recipient.email,
                        notification_type='general_notification',
                        context={
                            'subject': title,
                            'title': title,
                            'message': message,
                            'action_url': action_url,
                            'action_text': action_text,
                            'user_name': recipient.get_full_name() or recipient.username
                        }
                    )
            
            logger.info(f"Bildiriş yaradıldı: {title} -> {recipient.username}")
            return notification
            
        except Exception as e:
            logger.error(f"Bildiriş yaradılma xətası: {e}")
            return None
    
    @staticmethod
    def bulk_notify(recipients, title, message, **kwargs):
        """
        Çoxlu istifadəçiyə eyni bildirişi göndər
        """
        notifications = []
        for recipient in recipients:
            notification = NotificationManager.create_and_send(
                recipient=recipient,
                title=title,
                message=message,
                **kwargs
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_managers(organization_unit, title, message, **kwargs):
        """
        Müəyyən təşkilati vahidin rəhbərlərinə bildiriş göndər
        """
        managers = Ishchi.objects.filter(
            organization_unit=organization_unit,
            rol__in=['REHBER', 'ADMIN', 'SUPERADMIN']
        )
        
        return NotificationManager.bulk_notify(managers, title, message, **kwargs)
    
    @staticmethod
    def notify_hr_team(title, message, **kwargs):
        """
        HR komandası üzvlərinə bildiriş göndər
        """
        hr_managers = Ishchi.objects.filter(
            groups__name__in=['HR Manager', 'Super Admin']
        )
        
        return NotificationManager.bulk_notify(hr_managers, title, message, **kwargs)
    
    @staticmethod
    def get_user_notifications(user, limit=20, unread_only=False):
        """
        İstifadəçinin bildirişlərini cache ilə gətir
        """
        cache_key = f"user_notifications:{user.id}:{limit}:{unread_only}"
        notifications = cache.get(cache_key)
        
        if notifications is None:
            query = Notification.objects.filter(
                recipient=user, 
                is_archived=False
            )
            
            if unread_only:
                query = query.filter(is_read=False)
            
            notifications = list(query[:limit])
            cache.set(cache_key, notifications, 300)  # 5 dəqiqə cache
        
        return notifications
    
    @staticmethod
    def mark_all_as_read(user):
        """
        İstifadəçinin bütün bildirişlərini oxunmuş kimi işarələ
        """
        updated_count = Notification.objects.filter(
            recipient=user,
            is_read=False,
            is_archived=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        # Cache-i təmizlə
        cache_keys = [
            f"unread_notifications:{user.id}",
            f"user_notifications:{user.id}:*"
        ]
        cache.delete_many(cache_keys)
        
        return updated_count


# === XÜSUSİ BİLDİRİŞ FUNKSİYALARI ===

def notify_task_assigned(employee, task_title, task_description, evaluator, due_date=None):
    """Yeni tapşırıq təyin ediləndə bildiriş"""
    action_url = f"/qiymetlendirmeler/"
    
    message = f"Sizə yeni tapşırıq təyin edildi: {task_description}"
    if due_date:
        message += f" Son tarix: {due_date.strftime('%d.%m.%Y')}"
    
    return NotificationManager.create_and_send(
        recipient=employee,
        title=f"Yeni Tapşırıq: {task_title}",
        message=message,
        notification_type=Notification.NotificationType.TASK_ASSIGNED,
        priority=Notification.Priority.HIGH,
        sender=evaluator,
        action_url=action_url,
        action_text="Tapşırığa Bax",
        send_email=True
    )

def notify_deadline_approaching(employee, task_title, days_remaining):
    """Son tarix yaxınlaşdığında xatırlatma"""
    priority = Notification.Priority.URGENT if days_remaining <= 2 else Notification.Priority.HIGH
    
    message = f"'{task_title}' tapşırığının son tarixi {days_remaining} gün qalıb."
    
    return NotificationManager.create_and_send(
        recipient=employee,
        title="⏰ Son Tarix Xatırlatması",
        message=message,
        notification_type=Notification.NotificationType.DEADLINE_REMINDER,
        priority=priority,
        action_url="/dashboard/",
        action_text="Tapşırıqlara Bax",
        send_email=True
    )

def notify_evaluation_completed(employee, evaluator, evaluation_score):
    """Qiymətləndirmə tamamlandığında bildiriş"""
    message = f"Performans qiymətləndirməniz tamamlandı. Ümumi bal: {evaluation_score}"
    
    return NotificationManager.create_and_send(
        recipient=employee,
        title="✅ Qiymətləndirmə Tamamlandı",
        message=message,
        notification_type=Notification.NotificationType.EVALUATION_COMPLETED,
        priority=Notification.Priority.MEDIUM,
        sender=evaluator,
        action_url="/qiymetlendirmelerim/",
        action_text="Qiymətləndirməni Gör",
        send_email=True
    )

def notify_plan_approved(employee, approver, plan_title):
    """İnkişaf planı təsdiqlənəndə bildiriş"""
    message = f"'{plan_title}' inkişaf planınız təsdiqləndi və icrasına başlaya bilərsiniz."
    
    return NotificationManager.create_and_send(
        recipient=employee,
        title="👍 İnkişaf Planı Təsdiqləndi",
        message=message,
        notification_type=Notification.NotificationType.PLAN_APPROVED,
        priority=Notification.Priority.MEDIUM,
        sender=approver,
        action_url="/inkishaf-planlari/",
        action_text="Planı Gör",
        send_email=True
    )

def notify_feedback_received(admin_user, feedback):
    """Yeni geri bildirim gəldiyində admin-lərə bildiriş"""
    message = f"Yeni geri bildirim alınıb: {feedback.title} (Növ: {feedback.get_feedback_type_display()})"
    
    return NotificationManager.create_and_send(
        recipient=admin_user,
        title="💬 Yeni Geri Bildirim",
        message=message,
        notification_type=Notification.NotificationType.FEEDBACK_RECEIVED,
        priority=Notification.Priority.MEDIUM,
        action_url=f"/admin/core/feedback/{feedback.id}/change/",
        action_text="Geri Bildirimi Gör",
        send_email=True
    )

def notify_goal_deadline(employee, goal_title, days_remaining):
    """Hədəfin son tarixi yaxınlaşdığında bildiriş"""
    priority = Notification.Priority.URGENT if days_remaining <= 3 else Notification.Priority.HIGH
    
    message = f"'{goal_title}' hədəfinizin son tarixi {days_remaining} gün qalıb."
    
    return NotificationManager.create_and_send(
        recipient=employee,
        title="🎯 Hədəf Son Tarix Xatırlatması", 
        message=message,
        notification_type=Notification.NotificationType.DEADLINE_REMINDER,
        priority=priority,
        action_url="/inkishaf-planlari/",
        action_text="Hədəflərə Bax",
        send_email=True
    )

def notify_system_update(title, message, importance="medium"):
    """Sistem yeniləməsi haqqında bütün istifadəçilərə bildiriş"""
    priority_map = {
        "low": Notification.Priority.LOW,
        "medium": Notification.Priority.MEDIUM, 
        "high": Notification.Priority.HIGH,
        "urgent": Notification.Priority.URGENT
    }
    
    # Aktiv istifadəçilərə göndər
    active_users = Ishchi.objects.filter(is_active=True)
    
    return NotificationManager.bulk_notify(
        recipients=active_users,
        title=f"🔄 {title}",
        message=message,
        notification_type=Notification.NotificationType.SYSTEM_UPDATE,
        priority=priority_map.get(importance, Notification.Priority.MEDIUM),
        expires_in_days=7
    )

def notify_new_employee_joined(new_employee, hr_managers):
    """Yeni işçi qoşulduğunda HR-a bildiriş"""
    message = f"Yeni işçi qeydiyyatdan keçdi: {new_employee.get_full_name()} ({new_employee.username})"
    if hr_managers:
        return NotificationManager.bulk_notify(
            recipients=hr_managers,
            title="👋 Yeni İşçi Qoşuldu",
            message=message,
            notification_type=Notification.NotificationType.INFO,
            priority=Notification.Priority.MEDIUM,
            action_url=f"/admin/core/ishchi/{new_employee.id}/change/",
            action_text="Profilə Bax"
        )
    return []


# === AVTOMATİK XATİRLATMA SİSTEMİ ===

def send_weekly_reminders():
    """
    Həftəlik avtomatik xatırlatmalar göndər
    Celery beat tapşırığı kimi işləyə bilər
    """
    from datetime import date, timedelta
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    # 1. Son tarixi yaxın olan hədəflər
    upcoming_goals = Hedef.objects.filter(
        son_tarix__lte=week_later,
        son_tarix__gte=today,
        status__in=['BASHLANMAYIB', 'ICRADA']
    )
    
    for goal in upcoming_goals:
        days_remaining = (goal.son_tarix - today).days
        if days_remaining <= 7 and hasattr(goal, 'plan') and getattr(goal.plan, 'ishchi', None):
            notify_goal_deadline(
                employee=goal.plan.ishchi,
                goal_title=goal.tesvir[:50],
                days_remaining=days_remaining
            )
    
    # 2. Tamamlanmamış qiymətləndirmələr xatırlatması
    # Bu hissəni gələcəkdə əlavə edə bilərik
    
    logger.info("Həftəlik xatırlatmalar göndərildi")

def cleanup_old_notifications():
    """
    Köhnə bildirişləri təmizlə
    Celery beat tapşırığı kimi işləyə bilər
    """
    # 30 gündən köhnə oxunmuş bildirişləri arxivləşdir
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    archived_count = Notification.objects.filter(
        created_at__lt=cutoff_date,
        is_read=True,
        is_archived=False
    ).update(is_archived=True)
    
    # Müddəti bitmiş bildirişləri arxivləşdir
    expired_count = 0
    if hasattr(Notification, 'cleanup_expired'):
        expired_count = Notification.cleanup_expired()
    
    logger.info(f"Bildiriş təmizliyi: {archived_count} köhnə, {expired_count} müddəti bitmiş")
    
    return archived_count + expired_count