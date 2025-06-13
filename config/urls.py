# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls.i18n import i18n_patterns
from core.views import CustomLoginView

# 1. Dil prefiksi TƏLƏB EDƏN URL-ləri ayrıca təyin edirik
i18n_urlpatterns = i18n_patterns(
    # Bizim xüsusi login səhifəmizi birinci qeyd edirik
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    
    # Sonra Django-nun qalan autentifikasiya URL-lərini əlavə edirik
    # (logout, password_reset, password_change və s.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Əsas tətbiqimizin URL-ləri
    path('', include('core.urls')),
    
    # Standart dil üçün də /az/ prefiksinin görünməsini təmin edir
    prefix_default_language=True,
)

# 2. Əsas urlpatterns siyahısını yaradırıq və dilə həssas olmayanları əlavə edirik
urlpatterns = [
    # Dil prefiksi olmayan URL (yalnız admin paneli)
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