# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

# Xəta səhifələri üçün standart view-ları import edirik
from django.views.defaults import (
    page_not_found,
    server_error,
    permission_denied,
    bad_request,
)

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += i18n_patterns(
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Xəta handler-lərini təyin edirik
handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error