# config/urls.py - SON VƏ ƏN ETİBARLI VERSİYA

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# Bizim xüsusi Login View-umuzu import edirik
from core.views import CustomLoginView

# Dilə həssas olan URL-ləri bir siyahıya yığırıq
i18n_urlpatterns = [
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
]

# Əsas urlpatterns siyahısını yaradırıq
urlpatterns = [
    # Dil prefiksi olmayan admin panelini əlavə edirik
    path('admin/', admin.site.urls),
    
    # Dilə həssas olan URL-ləri i18n_patterns ilə əlavə edirik
    # prefix_default_language=True standart dil üçün də /az/ prefiksini təmin edir
    *i18n_patterns(*i18n_urlpatterns, prefix_default_language=True),
]

# Development rejimində (DEBUG=True) statik və media fayllarını əlavə edirik
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Xəta handler-lərini təyin edirik
handler400 = 'django.views.defaults.bad_request'
handler403 = 'django.views.defaults.permission_denied'
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'