# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from core.views import CustomLoginView

# Dilə həssas olan URL-lər
i18n_urlpatterns = i18n_patterns(
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    prefix_default_language=True,
)

# Dilə həssas olmayan URL-lər
urlpatterns = [
    path('admin/', admin.site.urls),
]
urlpatterns += i18n_urlpatterns

# --- YENİ VƏ VACİB HİSSƏ ---
# Yalnız DEVELOPMENT rejimində (DEBUG=True) statik və media faylları üçün URL-lər
if settings.DEBUG:
    # `collectstatic` ilə 'staticfiles' qovluğuna yığılan faylları göstərmək üçün
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
    
    # İstifadəçilərin yüklədiyi şəkilləri və faylları 'media' qovluğundan göstərmək üçün
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Static faylları STATICFILES_DIRS-dən də serve et
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()


# Xəta handler-ləri
handler400 = 'django.views.defaults.bad_request'
handler403 = 'django.views.defaults.permission_denied'
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'