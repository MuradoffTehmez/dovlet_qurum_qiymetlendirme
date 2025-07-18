# core/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _

@shared_task
def send_activation_email_task(subject, message, recipient_list):
    """
    Asynchronous task to send an email.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return f"Successfully sent email to {recipient_list[0]}"
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error sending email to {recipient_list[0]}: {e}")
        # Optionally, you can retry the task
        # raise self.retry(exc=e, countdown=60)
        return f"Failed to send email to {recipient_list[0]}"