# core/decorators.py

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden

def role_required(allowed_roles=[]):
    """
    İstifadəçinin rolunun icazə verilən rollardan biri olmasını yoxlayan dekorator.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.rol in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return wrapper
    return decorator

# Konkret rollar üçün hazır dekoratorlar
rehber_required = role_required(allowed_roles=['REHBER'])
superadmin_required = role_required(allowed_roles=['SUPERADMIN'])