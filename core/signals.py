# core/signals.py

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from .models import Ishchi, Qiymetlendirme
from .tokens import account_activation_token
from .tasks import send_activation_email_task


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


@receiver(post_save, sender=Ishchi)
def send_activation_email(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        # Aktivasiya linki yaradırıq
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = account_activation_token.make_token(instance)
        activation_link = reverse('activate', kwargs={'uidb64': uid, 'token': token})
        
        # E-poçt məzmununu hazırlayırıq
        subject = _('Activate Your Account')
        message = _(
            'Hi {user_name},\n\nPlease click the link below to activate your account:\n\nhttp://127.0.0.1:8000{activation_link}'
        ).format(user_name=instance.get_full_name(), activation_link=activation_link)
        
        # Tapşırığı arxa planda işə salırıq (Redis mövcud olduqda)
        # Əgər Redis mövcud deyilsə, birbaşa e-poçt göndəririk
        try:
            send_activation_email_task.delay(subject, message, [instance.email])
        except Exception as e:
            # Redis bağlantısı olmadıqda birbaşa e-poçt göndəririk
            from django.core.mail import send_mail
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])
            except Exception as mail_error:
                print(f"E-poçt göndərilərkən xəta: {mail_error}")
