# core/training_views.py - Təhsil və İnkişaf Modulu

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import Ishchi, OrganizationUnit
from .decorators import user_passes_test_with_message


def is_hr_or_manager(user):
    """HR və ya rəhbər olub-olmadığını yoxlayır"""
    return user.rol in ['hr', 'manager', 'superadmin']


@login_required
def training_dashboard(request):
    """Təhsil və İnkişaf Dashboard"""
    context = {
        'page_title': 'Təhsil və İnkişaf',
        'active_nav': 'training_dashboard'
    }
    return render(request, 'core/training/dashboard.html', context)


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def training_programs(request):
    """Təhsil Proqramları İdarəetmə"""
    context = {
        'page_title': 'Təhsil Proqramları',
        'active_nav': 'training_programs'
    }
    return render(request, 'core/training/programs.html', context)


@login_required
def employee_learning_path(request):
    """İşçinin Öyrənmə Yolu"""
    context = {
        'page_title': 'Mənim Öyrənmə Yolum',
        'active_nav': 'learning_path'
    }
    return render(request, 'core/training/learning_path.html', context)


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def skills_matrix(request):
    """Bacarıqlar Matrisi"""
    context = {
        'page_title': 'Bacarıqlar Matrisi',
        'active_nav': 'skills_matrix'
    }
    return render(request, 'core/training/skills_matrix.html', context)


@login_required
def certifications(request):
    """Sertifikatlaşdırma"""
    context = {
        'page_title': 'Sertifikatlar',
        'active_nav': 'certifications'
    }
    return render(request, 'core/training/certifications.html', context)


@login_required
def training_api_stats(request):
    """Təhsil statistikaları API"""
    try:
        # Dummy data for now - implement real logic later
        stats = {
            'total_programs': 15,
            'active_programs': 8,
            'completed_trainings': 42,
            'upcoming_sessions': 6,
            'avg_completion_rate': 78.5,
            'skills_assessed': 12,
            'certifications_earned': 23,
            'learning_hours': 156
        }
        
        # Recent training activities
        recent_activities = [
            {
                'title': 'JavaScript Əsasları kursu tamamlandı',
                'participant': 'Ayşe Məmmədova',
                'type': 'completion',
                'date': timezone.now().isoformat()
            },
            {
                'title': 'Liderlik bacarıqları təlimi başladı',
                'participant': 'Məhəmməd Əliyev',
                'type': 'enrollment',
                'date': (timezone.now() - timedelta(hours=2)).isoformat()
            },
            {
                'title': 'Python sertifikatı alındı',
                'participant': 'Günel Həsənli',
                'type': 'certification',
                'date': (timezone.now() - timedelta(hours=4)).isoformat()
            }
        ]
        
        # Skill development trends
        skill_trends = {
            'labels': ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'İyun'],
            'technical_skills': [65, 68, 72, 75, 78, 82],
            'soft_skills': [58, 62, 65, 69, 72, 75],
            'leadership_skills': [45, 48, 52, 55, 58, 62]
        }
        
        # Popular training programs
        popular_programs = [
            {'name': 'JavaScript Əsasları', 'participants': 25, 'completion_rate': 85},
            {'name': 'Liderlik İnkişafı', 'participants': 18, 'completion_rate': 92},
            {'name': 'Agile Metodları', 'participants': 22, 'completion_rate': 78},
            {'name': 'Kommunikasiya Bacarıqları', 'participants': 30, 'completion_rate': 88}
        ]
        
        return JsonResponse({
            'stats': stats,
            'recent_activities': recent_activities,
            'skill_trends': skill_trends,
            'popular_programs': popular_programs
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def skills_assessment_api(request):
    """Bacarıqlar qiymətləndirmə API"""
    try:
        # Dummy data for skills assessment
        skills_data = {
            'technical_skills': [
                {'name': 'Python', 'current_level': 7, 'target_level': 9, 'priority': 'high'},
                {'name': 'JavaScript', 'current_level': 6, 'target_level': 8, 'priority': 'medium'},
                {'name': 'SQL', 'current_level': 8, 'target_level': 9, 'priority': 'low'},
                {'name': 'React', 'current_level': 5, 'target_level': 8, 'priority': 'high'},
            ],
            'soft_skills': [
                {'name': 'Liderlik', 'current_level': 6, 'target_level': 9, 'priority': 'high'},
                {'name': 'Kommunikasiya', 'current_level': 8, 'target_level': 9, 'priority': 'medium'},
                {'name': 'Komanda işi', 'current_level': 7, 'target_level': 8, 'priority': 'medium'},
                {'name': 'Problem həlli', 'current_level': 7, 'target_level': 9, 'priority': 'high'},
            ],
            'certifications': [
                {'name': 'AWS Cloud Practitioner', 'status': 'planned', 'deadline': '2025-06-01'},
                {'name': 'Scrum Master', 'status': 'in_progress', 'progress': 60},
                {'name': 'Python Institute PCAP', 'status': 'completed', 'date_earned': '2024-12-15'},
            ]
        }
        
        return JsonResponse(skills_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)