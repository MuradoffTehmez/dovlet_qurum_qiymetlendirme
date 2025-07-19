"""
Quick Feedback URL konfiqurasiyaları
"""
from django.urls import path
from core.views import quick_feedback

app_name = 'quick_feedback'

urlpatterns = [
    # Dashboard
    path('', quick_feedback.quick_feedback_dashboard, name='dashboard'),
    
    # Geri bildirim göndərmə
    path('send/', quick_feedback.send_quick_feedback, name='send'),
    
    # Geri bildirimlər
    path('inbox/', quick_feedback.quick_feedback_inbox, name='inbox'),
    path('sent/', quick_feedback.quick_feedback_sent, name='sent'),
    path('<int:feedback_id>/', quick_feedback.view_quick_feedback, name='view'),
    
    # AJAX əməliyyatları
    path('<int:feedback_id>/mark-read/', quick_feedback.mark_feedback_read, name='mark_read'),
    path('<int:feedback_id>/archive/', quick_feedback.archive_feedback, name='archive'),
    
    # API endpoints
    path('api/', quick_feedback.quick_feedback_api, name='api'),
    
    # Analitika
    path('analytics/', quick_feedback.quick_feedback_analytics, name='analytics'),
]