# config/urls.py - SON VƏ ƏN ETİBARLI VERSİYA

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Bizim xüsusi Login View-umuzu import edirik
from core.views import CustomLoginView

i18n_urlpatterns = [
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls")),
]

# Əsas urlpatterns siyahısını yaradırıq
urlpatterns = [
    
    path('admin/', admin.site.urls),

    *i18n_patterns(*i18n_urlpatterns, prefix_default_language=True),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Xəta handler-lərini təyin edirik
handler400 = "django.views.defaults.bad_request"
handler403 = "django.views.defaults.permission_denied"
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"
