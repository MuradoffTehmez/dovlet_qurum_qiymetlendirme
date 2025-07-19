# core/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_activation_email_task(self, subject, message, recipient_list, html_message=None):
    """
    Asinxron e-poçt göndərmə tapşırığı
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"E-poçt uğurla göndərildi: {recipient_list[0]}")
        return f"Successfully sent email to {recipient_list[0]}"
    except Exception as e:
        logger.error(f"E-poçt göndərmə xətası {recipient_list[0]}: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Yenidən cəhd edilir {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        return f"Failed to send email to {recipient_list[0]} after {self.max_retries} retries"

@shared_task(bind=True)
def generate_report_task(self, report_type, user_id, filters=None):
    """
    Hesabat generasiya tapşırığı
    """
    try:
        from django.contrib.auth.models import User
        from .models import Ischiler, Qiymetlendirme
        
        user = User.objects.get(id=user_id)
        logger.info(f"Hesabat generasiyası başladı: {report_type} - İstifadəçi: {user.username}")
        
        # Sadə PDF hesabat yaradım
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        p.drawString(100, height - 100, f"Q360 Hesabatı - {report_type}")
        p.drawString(100, height - 130, f"Tarix: {filters.get('date', 'Hamısı') if filters else 'Hamısı'}")
        
        # Məlumatları əlavə et
        if report_type == 'ischiler':
            ischiler = Ischiler.objects.all()
            y_position = height - 180
            for ischi in ischiler:
                p.drawString(100, y_position, f"{ischi.ad} {ischi.soyad} - {ischi.vezife}")
                y_position -= 20
                if y_position < 100:
                    p.showPage()
                    y_position = height - 100
        
        p.save()
        buffer.seek(0)
        
        # Faylı saxla və ya e-poçtla göndər
        logger.info(f"Hesabat uğurla yaradıldı: {report_type}")
        return f"Report {report_type} generated successfully"
        
    except Exception as e:
        logger.error(f"Hesabat generasiya xətası: {e}")
        raise self.retry(exc=e, countdown=60)

@shared_task
def send_notification_email_task(user_email, notification_type, context):
    """
    Bildiriş e-poçtları göndərmə tapşırığı
    """
    try:
        template_map = {
            'new_task': 'emails/new_task_notification.html',
            'deadline_reminder': 'emails/deadline_reminder.html',
            'performance_review': 'emails/performance_review.html',
        }
        
        template_name = template_map.get(notification_type, 'emails/general_notification.html')
        
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        subject = context.get('subject', 'Q360 Bildirişi')
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Bildiriş e-poçtu göndərildi: {user_email} - {notification_type}")
        return f"Notification sent to {user_email}"
        
    except Exception as e:
        logger.error(f"Bildiriş göndərmə xətası: {e}")
        return f"Failed to send notification: {e}"


@shared_task
def create_automatic_evaluation_cycle():
    """
    Avtomatik qiymətləndirmə dövrü yaratma tapşırığı
    Hər rübün başında yeni qiymətləndirmə dövrü yaradır
    """
    from django.utils import timezone
    from .models import QiymetlendirmeDovru, Ishchi, Notification
    from datetime import datetime, timedelta
    import calendar
    
    try:
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month
        
        # Rübü müəyyən et
        if current_month in [1, 2, 3]:
            quarter = "Q1"
            start_date = datetime(current_year, 1, 1).date()
            end_date = datetime(current_year, 3, 31).date()
        elif current_month in [4, 5, 6]:
            quarter = "Q2"
            start_date = datetime(current_year, 4, 1).date()
            end_date = datetime(current_year, 6, 30).date()
        elif current_month in [7, 8, 9]:
            quarter = "Q3"
            start_date = datetime(current_year, 7, 1).date()
            end_date = datetime(current_year, 9, 30).date()
        else:
            quarter = "Q4"
            start_date = datetime(current_year, 10, 1).date()
            end_date = datetime(current_year, 12, 31).date()
        
        cycle_name = f"{current_year} {quarter} Qiymətləndirmə Dövrü"
        
        # Mövcud dövrü yoxla
        existing_cycle = QiymetlendirmeDovru.objects.filter(
            ad=cycle_name
        ).first()
        
        if existing_cycle:
            logger.info(f"Dövr artıq mövcuddur: {cycle_name}")
            return f"Cycle already exists: {cycle_name}"
        
        # Yeni dövr yarat
        new_cycle = QiymetlendirmeDovru.objects.create(
            ad=cycle_name,
            bashlama_tarixi=start_date,
            bitme_tarixi=end_date,
            aktivdir=True,
            anonymity_level=QiymetlendirmeDovru.AnonymityLevel.MANAGER_ONLY
        )
        
        logger.info(f"Yeni qiymətləndirmə dövrü yaradıldı: {cycle_name}")
        
        # Bütün adminləri və HR managerlərini xəbərdar et
        admins_and_hr = Ishchi.objects.filter(
            rol__in=['ADMIN', 'SUPERADMIN']
        )
        
        for admin in admins_and_hr:
            Notification.create_notification(
                recipient=admin,
                title="Yeni Qiymətləndirmə Dövrü Yaradıldı",
                message=f"Avtomatik olaraq yeni qiymətləndirmə dövrü yaradıldı: {cycle_name}",
                notification_type=Notification.NotificationType.SYSTEM_UPDATE,
                priority=Notification.Priority.HIGH,
                action_url=f"/admin/core/qiymetlendirmedovru/{new_cycle.id}/change/",
                action_text="Dövrü İdarə Et"
            )
        
        return f"Successfully created cycle: {cycle_name}"
        
    except Exception as e:
        logger.error(f"Avtomatik dövr yaratma xətası: {e}")
        return f"Failed to create automatic cycle: {e}"


@shared_task
def send_evaluation_deadline_reminders():
    """
    Qiymətləndirmə son tarix xatırlatmaları göndərir
    """
    from django.utils import timezone
    from .models import QiymetlendirmeDovru, Qiymetlendirme, Notification, Ishchi
    from datetime import timedelta
    
    try:
        today = timezone.now().date()
        warning_date = today + timedelta(days=7)  # 7 gün qabaq xəbərdarlıq
        
        # Aktiv dövrləri tap
        active_cycles = QiymetlendirmeDovru.objects.filter(
            aktivdir=True,
            bitme_tarixi__lte=warning_date,
            bitme_tarixi__gte=today
        )
        
        reminder_count = 0
        
        for cycle in active_cycles:
            # Tamamlanmamış qiymətləndirmələri tap
            incomplete_evaluations = Qiymetlendirme.objects.filter(
                dovr=cycle,
                status=Qiymetlendirme.Status.GOZLEMEDE
            )
            
            for evaluation in incomplete_evaluations:
                # Qiymətləndirənə xatırlatma göndər
                days_left = (cycle.bitme_tarixi - today).days
                
                Notification.create_notification(
                    recipient=evaluation.qiymetlendiren,
                    title=f"Qiymətləndirmə Son Tarixi: {days_left} gün qaldı",
                    message=f"{evaluation.qiymetlendirilen.get_full_name()} üçün qiymətləndirməni tamamlamalısınız. Son tarix: {cycle.bitme_tarixi.strftime('%d.%m.%Y')}",
                    notification_type=Notification.NotificationType.DEADLINE_REMINDER,
                    priority=Notification.Priority.HIGH if days_left <= 3 else Notification.Priority.MEDIUM,
                    action_url=f"/qiymetlendirme/{evaluation.id}/",
                    action_text="Qiymətləndirməni Tamamla",
                    expires_in_days=days_left
                )
                
                reminder_count += 1
        
        logger.info(f"Göndərilən xatırlatma sayı: {reminder_count}")
        return f"Sent {reminder_count} deadline reminders"
        
    except Exception as e:
        logger.error(f"Xatırlatma göndərmə xətası: {e}")
        return f"Failed to send reminders: {e}"


@shared_task  
def cleanup_old_notifications():
    """
    Köhnə bildirişləri təmizləyir
    """
    from django.utils import timezone
    from .models import Notification
    from datetime import timedelta
    
    try:
        # 30 gündən köhnə bildirişləri arxivləşdir
        cutoff_date = timezone.now() - timedelta(days=30)
        
        archived_count = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_archived=False
        ).update(is_archived=True)
        
        # 90 gündən köhnə arxivlənmiş bildirişləri sil
        delete_cutoff = timezone.now() - timedelta(days=90)
        deleted_count = Notification.objects.filter(
            created_at__lt=delete_cutoff,
            is_archived=True
        ).delete()[0]
        
        logger.info(f"Arxivlənən bildiriş sayı: {archived_count}, Silinən sayı: {deleted_count}")
        return f"Archived: {archived_count}, Deleted: {deleted_count} notifications"
        
    except Exception as e:
        logger.error(f"Bildiriş təmizləmə xətası: {e}")
        return f"Failed to cleanup notifications: {e}"