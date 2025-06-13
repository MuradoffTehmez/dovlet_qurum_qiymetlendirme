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
            
            user = Ishchi.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except Ishchi.DoesNotExist:

            return None
        except Ishchi.MultipleObjectsReturned:
            user = Ishchi.objects.get(username__iexact=username)

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Ishchi.objects.get(pk=user_id)
        except Ishchi.DoesNotExist:
            return None