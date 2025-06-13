# core/decorators.py

from django.core.exceptions import PermissionDenied


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

rehber_required = role_required(allowed_roles=['REHBER'])
superadmin_required = role_required(allowed_roles=['SUPERADMIN'])