# core/permissions.py
"""
Q360 Layihəsi üçün Genişləndirilmiş İcazə Sistemi
Django-nun Group və Permission sistemi ilə modern RBAC (Role-Based Access Control)
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

# Sistem rolları və onların icazələri
ROLE_PERMISSIONS = {
    'Super Admin': [
        # Bütün icazələr
        'add_user', 'change_user', 'delete_user', 'view_user',
        'add_ishchi', 'change_ishchi', 'delete_ishchi', 'view_ishchi',
        'add_qiymetlendirme', 'change_qiymetlendirme', 'delete_qiymetlendirme', 'view_qiymetlendirme',
        'add_organizationunit', 'change_organizationunit', 'delete_organizationunit', 'view_organizationunit',
        'add_inki shafplani', 'change_inkishafplani', 'delete_inkishafplani', 'view_inkishafplani',
        'view_all_reports', 'generate_reports', 'manage_system_settings',
        'view_audit_logs', 'manage_users', 'manage_roles'
    ],
    
    'HR Manager': [
        # İnsan resursları idarəetməsi
        'add_ishchi', 'change_ishchi', 'view_ishchi',
        'add_qiymetlendirme', 'change_qiymetlendirme', 'view_qiymetlendirme',
        'view_inkishafplani', 'change_inkishafplani',
        'view_organization_reports', 'generate_hr_reports',
        'manage_performance_reviews'
    ],
    
    'Department Manager': [
        # Şöbə rəhbəri icazələri
        'view_ishchi', 'change_ishchi',  # Yalnız öz şöbəsindəki işçilər
        'add_qiymetlendirme', 'change_qiymetlendirme', 'view_qiymetlendirme',
        'add_inkishafplani', 'change_inkishafplani', 'view_inkishafplani',
        'view_department_reports', 'manage_team_performance'
    ],
    
    'Team Lead': [
        # Komanda lideri icazələri
        'view_ishchi',  # Yalnız komanda üzvləri
        'add_qiymetlendirme', 'view_qiymetlendirme',
        'add_inkishafplani', 'view_inkishafplani',
        'view_team_reports'
    ],
    
    'Employee': [
        # Sadə işçi icazələri
        'view_ishchi',  # Yalnız özü
        'view_qiymetlendirme',  # Yalnız öz qiymətləndirmələri
        'view_inkishafplani',  # Yalnız öz planları
        'change_own_profile'
    ]
}

def create_role_groups():
    """
    Sistem rollarını və onların icazələrini yaradır
    """
    for role_name, permissions in ROLE_PERMISSIONS.items():
        group, created = Group.objects.get_or_create(name=role_name)
        
        if created:
            print(f"Rol yaradıldı: {role_name}")
        
        # İcazələri əlavə et
        for perm_code in permissions:
            try:
                # Mövcud icazələri tap
                if '.' in perm_code:
                    app_label, codename = perm_code.split('.', 1)
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                else:
                    # Xüsusi icazələr yarad
                    content_type, created = ContentType.objects.get_or_create(
                        app_label='core',
                        model='custom_permission'
                    )
                    permission, created = Permission.objects.get_or_create(
                        codename=perm_code,
                        name=perm_code.replace('_', ' ').title(),
                        content_type=content_type
                    )
                
                group.permissions.add(permission)
                
            except Permission.DoesNotExist:
                print(f"İcazə tapılmadı: {perm_code}")
                continue
        
        group.save()

def has_permission(user, permission_code):
    """
    İstifadəçinin müəyyən icazəyə sahib olub-olmadığını yoxlayır
    """
    if user.is_superuser:
        return True
    
    return user.has_perm(f'core.{permission_code}') or \
           user.groups.filter(permissions__codename=permission_code).exists()

def permission_required(permission_code, raise_exception=True):
    """
    Dekorator: İstifadəçinin müəyyən icazəyə sahib olmasını tələb edir
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and has_permission(request.user, permission_code):
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                if not request.user.is_authenticated:
                    return redirect('login')
                else:
                    messages.error(request, _('Bu əməliyyat üçün icazəniz yoxdur.'))
                    raise PermissionDenied
            
            return redirect('dashboard')
        
        return wrapper
    return decorator


def require_role(allowed_roles):
    """
    Self-review üçün rol əsaslı icazə dekoratoru
    allowed_roles: icazə verilən rolların siyahısı ['ISHCHI', 'REHBER', 'ADMIN', 'SUPERADMIN']
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request.user, 'rol', None)
            
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'Bu səhifəyə giriş icazəniz yoxdur.')
            return HttpResponseForbidden("Bu səhifəyə giriş icazəniz yoxdur.")
        
        return wrapper
    return decorator

def user_can_manage_employee(manager, employee):
    """
    Rəhbərin işçini idarə edə biləcəyini yoxlayır
    """
    if manager.is_superuser:
        return True
    
    # HR Manager hər kəsi idarə edə bilər
    if manager.groups.filter(name='HR Manager').exists():
        return True
    
    # Department Manager yalnız öz şöbəsindəki işçiləri
    if manager.groups.filter(name='Department Manager').exists():
        return manager.organization_unit == employee.organization_unit
    
    # Team Lead yalnız birbaşa hesabat verən işçiləri
    if manager.groups.filter(name='Team Lead').exists():
        # Bu məntiq daha mürəkkəb ola bilər - ata-övlad əlaqəsi
        return manager.organization_unit == employee.organization_unit
    
    return False

def get_user_role(user):
    """
    İstifadəçinin əsas rolunu qaytarır
    """
    if user.is_superuser:
        return "Super Admin"
    
    # İlk qrupun adını qaytar
    group = user.groups.first()
    return group.name if group else "Employee"

def assign_user_to_role(user, role_name):
    """
    İstifadəçini müəyyən rola təyin edir
    """
    try:
        # Köhnə qrupları sil
        user.groups.clear()
        
        # Yeni qrupu əlavə et
        group = Group.objects.get(name=role_name)
        user.groups.add(group)
        
        # Köhnə rol sahəsini yenilə
        if hasattr(user, 'rol'):
            role_mapping = {
                'Super Admin': 'SUPERADMIN',
                'HR Manager': 'ADMIN',
                'Department Manager': 'REHBER',
                'Team Lead': 'REHBER',
                'Employee': 'ISHCHI'
            }
            user.rol = role_mapping.get(role_name, 'ISHCHI')
            user.save()
        
        return True
        
    except Group.DoesNotExist:
        return False

# Səriştəli dekoratorlar
super_admin_required = permission_required('manage_system_settings')
hr_manager_required = permission_required('manage_users')
manager_required = permission_required('manage_team_performance')
can_view_reports = permission_required('view_organization_reports')