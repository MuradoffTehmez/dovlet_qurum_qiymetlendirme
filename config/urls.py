from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

# Dil prefiksi olmayan URL-lər (məsələn: admin paneli üçün)
urlpatterns = [
    path('admin/', admin.site.urls),
]

# Dil prefiksi olan URL-lər (/az/, /en/ və s.)
urlpatterns += i18n_patterns(
    path('accounts/', include('django.contrib.auth.urls')),  # Daxil olma / çıxış üçün URL-lər
    path('', include('core.urls')),                          # Əsas tətbiqə aid URL-lər

    # Gələcəkdə dilə uyğun başqa URL-lər də bura əlavə edilə bilər
    # Məsələn: path('hesabatlar/', include('reports.urls'))
    
    # Əgər prefix_default_language=False yazsanız,
    # əsas dil (məs: azərbaycan dili) üçün "/az/" prefiksi göstərilməyəcək.
    # Yəni, saytınız azərbaycanca olanda URL-lər birbaşa / olacaq,
    # ingiliscə olduqda isə /en/ prefiksi ilə açılacaq.
    # prefix_default_language=False
)
