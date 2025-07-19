# core/api_permissions.py

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Yalnız obyektin sahibi onu dəyişdirə bilər, qalanları yalnız oxuya bilər.
    """
    
    def has_object_permission(self, request, view, obj):
        # Oxuma icazələri bütün istifadəçilər üçün
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Yazma icazələri yalnız obyektin sahibi üçün
        return obj.owner == request.user


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Yalnız rəhbər və admin rolları bu əməliyyatı edə bilər.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']
        )


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Yalnız admin və superadmin rolları bu əməliyyatı edə bilər.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.rol in ['ADMIN', 'SUPERADMIN']
        )


class IsOwnerOrManager(permissions.BasePermission):
    """
    Obyektin sahibi və ya rəhbər bu əməliyyatı edə bilər.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin və superadmin həmişə icazəli
        if request.user.rol in ['ADMIN', 'SUPERADMIN']:
            return True
        
        # Obyektin sahibi
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # Əgər obyekt işçi modelidir və istifadəçi özüdür
        if hasattr(obj, 'username') and obj == request.user:
            return True
        
        # Əgər istifadəçi rəhbərdir və obyekt onun komandası üzərindədir
        if request.user.rol == 'REHBER':
            # Bu məntiq biznes qaydalarına görə dəyişə bilər
            return True
        
        return False


class CanEvaluatePermission(permissions.BasePermission):
    """
    Qiymətləndirmə üçün xüsusi icazə.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin və superadmin həmişə icazəli
        if request.user.rol in ['ADMIN', 'SUPERADMIN']:
            return True
        
        # Qiymətləndirmə obyekti üçün
        if hasattr(obj, 'qiymetlendiren'):
            return obj.qiymetlendiren == request.user
        
        return False


class CanViewEvaluationPermission(permissions.BasePermission):
    """
    Qiymətləndirmə nəticəsini görə bilmək üçün icazə.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin və superadmin həmişə icazəli
        if request.user.rol in ['ADMIN', 'SUPERADMIN']:
            return True
        
        # Qiymətləndirmə obyekti üçün
        if hasattr(obj, 'qiymetlendirilecek') and hasattr(obj, 'qiymetlendiren'):
            return (
                obj.qiymetlendirilecek == request.user or 
                obj.qiymetlendiren == request.user
            )
        
        # Rəhbər öz komandası üzərindəki qiymətləndirmələri görə bilər
        if request.user.rol == 'REHBER':
            # Bu məntiq biznes qaydalarına görə dəyişə bilər
            return True
        
        return False


class AnonymityAwarePermission(permissions.BasePermission):
    """
    Anonimlik səviyyəsinə uyğun icazə.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin və superadmin həmişə icazəli
        if request.user.rol in ['ADMIN', 'SUPERADMIN']:
            return True
        
        # Əgər obyektdə anonimlik səviyyəsi varsa
        if hasattr(obj, 'dovr') and hasattr(obj.dovr, 'anonymity_level'):
            # Tam anonim olarsa, heç kim adları görə bilməz
            if obj.dovr.anonymity_level == 'FULL_ANONYMOUS':
                return False
            
            # Yalnız rəhbər görə bilərsə
            elif obj.dovr.anonymity_level == 'MANAGER_ONLY':
                return request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']
            
            # Açıq olarsa hamı görə bilər
            elif obj.dovr.anonymity_level == 'OPEN':
                return True
        
        return True


class DepartmentBasedPermission(permissions.BasePermission):
    """
    Departamenta əsaslanan icazə sistemi.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin və superadmin həmişə icazəli
        if request.user.rol in ['ADMIN', 'SUPERADMIN']:
            return True
        
        # Əgər istifadəçi və obyekt eyni departamentdədir
        if hasattr(obj, 'organization_unit') and request.user.organization_unit:
            return obj.organization_unit == request.user.organization_unit
        
        # Əgər obyekt işçi modelidir
        if hasattr(obj, 'username') and hasattr(obj, 'organization_unit'):
            return obj.organization_unit == request.user.organization_unit
        
        return False