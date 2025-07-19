"""
Private Notes URL konfiqurasiyaları
"""
from django.urls import path
from core.views import private_notes

app_name = 'private_notes'

urlpatterns = [
    # Dashboard
    path('', private_notes.private_notes_dashboard, name='dashboard'),
    
    # İşçi üzrə qeydlər
    path('employee/<int:employee_id>/', private_notes.employee_notes, name='employee_notes'),
    
    # Qeyd əməliyyatları
    path('create/', private_notes.create_note, name='create'),
    path('create/<int:employee_id>/', private_notes.create_note, name='create_for_employee'),
    path('edit/<int:note_id>/', private_notes.edit_note, name='edit'),
    path('view/<int:note_id>/', private_notes.view_note, name='view'),
    path('delete/<int:note_id>/', private_notes.delete_note, name='delete'),
    
    # Axtarış və analitika
    path('search/', private_notes.search_notes, name='search'),
    path('analytics/', private_notes.notes_analytics, name='analytics'),
]