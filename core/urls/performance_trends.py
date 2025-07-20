"""
Performance Trends URL konfiqurasiyaları
"""
from django.urls import path
from core.views import performance_trends

app_name = 'performance_trends'

urlpatterns = [
    # Dashboard
    path('', performance_trends.performance_trends_dashboard, name='dashboard'),
    
    # API endpoints
    path('api/', performance_trends.performance_trends_api, name='api'),
    
    # Şöbələr müqayisəsi
    path('department-comparison/', performance_trends.department_trends_comparison, name='department_comparison'),
    
    # Fərdi kateqoriya trendi
    path('category/<int:category_id>/', 
         performance_trends.individual_category_trend, name='category_detail'),
]