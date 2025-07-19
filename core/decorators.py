# core/decorators.py

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps


def role_required(allowed_roles=[]):
    """İstifadəçinin rolunun icazə verilən rollardan biri olmasını yoxlayan dekorator."""

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser or request.user.rol in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied

        return wrapper

    return decorator


def user_passes_test_with_message(test_func, message="Bu səhifəyə giriş icazəniz yoxdur.", redirect_url='dashboard'):
    """
    İstifadəçinin test funksiyasını keçib-keçmədiyini yoxlayan dekorator.
    Əgər test uğursuz olarsa, mesaj göstərib yönləndirir.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and test_func(request.user):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, message)
                return redirect(redirect_url)
        return wrapper
    return decorator


rehber_required = role_required(allowed_roles=["REHBER"])
superadmin_required = role_required(allowed_roles=["SUPERADMIN"])
