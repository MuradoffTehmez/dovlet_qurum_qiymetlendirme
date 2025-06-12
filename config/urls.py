# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# 1. Dil prefiksi TƏLƏB EDƏN URL-ləri ayrıca təyin edirik
# Bütün istifadəçi tərəfindən görünən səhifələr burada olmalıdır
i18n_urlpatterns = i18n_patterns(
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    # core.urls faylında olan URL-lər burada daxil edilir
    # core.urls faylında olan URL-lər dilə həssas olacaq
    # prefix_default_language=False parametiri standart dil üçün ('az') 
    
    # Məsələn: /hesabatim/ (az) və /en/my-report/ (en)
    # prefix_default_language=True olarsa, URL-lər belə olacaq: /az/hesabatim/ və /en/my-report/

    # prefix_default_language=True,  # Bu parametr True olaraq saxlanılırsa,
    # prefix_default_language=False,
)

# 2. Əsas urlpatterns siyahısını yaradırıq və dilə həssas olmayanları əlavə edirik
urlpatterns = [
    # Dil prefiksi olmayan URL-lər (yalnız admin paneli kimi)
    path('admin/', admin.site.urls),
]

# 3. Dilə həssas URL-ləri əsas siyahıya əlavə edirik
urlpatterns += i18n_urlpatterns

# 4. Yalnız DEVELOPMENT rejimində statik və media faylları üçün URL-lər əlavə edirik
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# 5. Xəta səhifələrini təyin edirik (string formatında daha stabildir)
handler400 = 'django.views.defaults.bad_request'
handler403 = 'django.views.defaults.permission_denied'
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'