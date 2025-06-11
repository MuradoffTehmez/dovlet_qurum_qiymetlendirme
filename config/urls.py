from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from django.views.defaults import (
    bad_request,
    permission_denied,
    page_not_found,
    server_error,
)

urlpatterns = [
    path('admin/', admin.site.urls),
] + i18n_patterns(
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    prefix_default_language=False,
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- XƏTA SƏHİFƏLƏRİ ---

handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error