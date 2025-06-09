# config/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Daxilolma/Çıxış üçün
    path('', include('core.urls')), # Core tətbiqinin URL-ləri
]