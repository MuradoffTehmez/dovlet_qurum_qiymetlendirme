"""
Gap Analysis URL konfiqurasiyaları
"""
from django.urls import path
from core.views import gap_analysis

app_name = 'gap_analysis'

urlpatterns = [
    # Dashboard
    path('', gap_analysis.gap_analysis_dashboard, name='dashboard'),
    
    # Detallı analiz
    path('cycle/<int:cycle_id>/', gap_analysis.gap_analysis_detail, name='detail'),
    
    # API endpoints
    path('api/cycle/<int:cycle_id>/', gap_analysis.gap_analysis_api, name='api'),
    
    # Komanda analizi
    path('team/', gap_analysis.team_gap_analysis, name='team'),
]