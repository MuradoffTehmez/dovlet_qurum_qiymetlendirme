# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# Xəta səhifələri üçün standart view-ları import edirik
from django.views.defaults import (
    bad_request,
    permission_denied,
    page_not_found,
    server_error,
)

# --- URL BÖLGÜSÜ ---

# Dil prefiksi olmayan URL-lər (admin paneli kimi)
urlpatterns = [
    path('admin/', admin.site.urls),
]

# Dil prefiksi olan URL-lər (/az/, /en/)
# Bütün istifadəçi tərəfindən görünən səhifələr burada olmalıdır
urlpatterns += i18n_patterns(
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    
    # prefix_default_language=False parametiri əlavə etsəniz,
    # standart dil (az) üçün /az/ prefiksi görünməyəcək.
)

# --- MEDIA FAYLLARININ GÖSTƏRİLMƏSİ (YALNIZ DEVELOPMENT ÜÇÜN) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# --- XƏTA HANDLER-LƏRİNİN TƏYİN EDİLMƏSİ ---
# Django-ya hansı xətada hansı standart view-ı işə salacağını deyirik.
# Bu view-lar isə avtomatik olaraq templates qovluğundakı
# 400.html, 403.html, 404.html və 500.html fayllarını axtarıb göstərəcək.

handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error