"""
Participation Monitoring URL konfiqurasiyaları
"""
from django.urls import path
from core.views import participation_monitoring

app_name = 'participation_monitoring'

urlpatterns = [
    # Dashboard
    path('', participation_monitoring.participation_dashboard, name='dashboard'),
    
    # Detallı məlumatlar
    path('cycle/<int:cycle_id>/details/', participation_monitoring.participation_details, name='details'),
    
    # Xatırlatma göndərmə
    path('cycle/<int:cycle_id>/send-reminders/', participation_monitoring.send_participation_reminders, name='send_reminders'),
    
    # API endpoints
    path('cycle/<int:cycle_id>/analytics/', participation_monitoring.participation_analytics_api, name='analytics_api'),
    
    # Export
    path('cycle/<int:cycle_id>/export/', participation_monitoring.participation_export, name='export'),
]