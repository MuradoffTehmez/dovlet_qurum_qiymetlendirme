"""
Idea Bank URL konfiqurasiyaları
"""
from django.urls import path
from core.views import idea_bank

app_name = 'idea_bank'

urlpatterns = [
    # Dashboard
    path('', idea_bank.idea_bank_dashboard, name='dashboard'),
    
    # İdeya əməliyyatları
    path('create/', idea_bank.create_idea, name='create'),
    path('<int:idea_id>/', idea_bank.idea_detail, name='detail'),
    path('<int:idea_id>/edit/', idea_bank.edit_idea, name='edit'),
    path('my-ideas/', idea_bank.my_ideas, name='my_ideas'),
    
    # Səs vermə və şərh
    path('<int:idea_id>/vote/', idea_bank.vote_idea, name='vote'),
    path('<int:idea_id>/comment/', idea_bank.add_comment, name='add_comment'),
    
    # Admin panel
    path('admin/review/', idea_bank.admin_review, name='admin_review'),
    path('admin/<int:idea_id>/review/', idea_bank.review_idea, name='review_idea'),
    
    # Analitika
    path('analytics/', idea_bank.idea_analytics, name='analytics'),
]