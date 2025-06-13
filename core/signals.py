# core/signals.py

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Qiymetlendirme


@receiver(post_save, sender=Qiymetlendirme)
def send_notification_on_new_assignment(sender, instance, created, **kwargs):
    """
    Yeni bir Qiymetlendirme obyekti yaradıldıqda bu funksiya avtomatik işə düşür.
    """
    # Yalnız obyekt YENİ YARADILDIQDA e-poçt göndəririk (update olduqda yox)
    if created:
        qiymetlendiren = instance.qiymetlendiren
        qiymetlendirilen = instance.qiymetlendirilen

        subject = "Yeni Qiymətləndirmə Tapşırığı"

        message = f"""
Salam, {qiymetlendiren.get_full_name()},

Sizin üçün yeni bir qiymətləndirmə tapşırığı təyin edildi.

Qiymətləndiriləcək şəxs: {qiymetlendirilen.get_full_name()}
Son tarix: {instance.dovr.bitme_tarixi.strftime('%d-%m-%Y')}

Xahiş edirik sistemə daxil olub tapşırığı vaxtında yerinə yetirəsiniz.

URL: http://127.0.0.1:8000/

Hörmətlə,
Qiymətləndirmə Sistemi
"""

        # E-poçtu göndəririk
        if qiymetlendiren.email:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [qiymetlendiren.email],
                    fail_silently=False,
                )
            except Exception as e:
                # E-poçt göndərilərkən xəta baş verərsə, terminalda göstəririk
                print(f"E-poçt göndərilərkən xəta baş verdi: {e}")
