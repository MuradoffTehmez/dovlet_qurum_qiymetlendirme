"""
Self-review URL konfigurasyaları
"""
from django.urls import path
from core.views import self_review

app_name = 'self_review'

urlpatterns = [
    # Dashboard
    path('', self_review.self_review_dashboard, name='dashboard'),
    
    # CRUD əməliyyatları
    path('cycle/<int:cycle_id>/create/', self_review.create_self_review, name='create'),
    path('<int:review_id>/edit/', self_review.edit_self_review, name='edit'),
    path('<int:review_id>/view/', self_review.view_self_review, name='view'),
    
    # AJAX əməliyyatları
    path('<int:review_id>/save-answer/', self_review.save_answer, name='save_answer'),
    path('<int:review_id>/complete/', self_review.complete_self_review, name='complete'),
    
    # Analitika
    path('analytics/', self_review.self_review_analytics, name='analytics'),
]