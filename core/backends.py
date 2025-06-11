# core/backends.py

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import Ishchi

class EmailOrUsernameBackend(ModelBackend):
    """
    İstifadəçiyə həm istifadəçi adı, həm də e-poçt ünvanı ilə
    sistemə daxil olmaq imkanı verən xüsusi autentifikasiya arxa tərəfi.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # İstifadəçini həm istifadəçi adı, həm də e-poçt (hərf həssaslığı olmadan) ilə axtarırıq
            user = Ishchi.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except Ishchi.DoesNotExist:
            # Əgər heç bir istifadəçi tapılmazsa, autentifikasiya baş tutmur
            return None
        except Ishchi.MultipleObjectsReturned:
             # Eyni email ilə bir neçə istifadəçi varsa, istifadəçi adı ilə dəqiq axtarış edirik
            user = Ishchi.objects.get(username__iexact=username)

        # Şifrəni yoxlayırıq və istifadəçinin sistemə daxil olmasına icazə verilibmi deyə baxırıq
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Ishchi.objects.get(pk=user_id)
        except Ishchi.DoesNotExist:
            return None