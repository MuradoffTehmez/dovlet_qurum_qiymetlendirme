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