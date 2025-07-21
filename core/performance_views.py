# core/performance_views.py - Performans İdarəetmə Sistemi

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import (
    Ishchi, Qiymetlendirme, QiymetlendirmeDovru, 
    InkishafPlani, Hedef, RiskFlag, EmployeeRiskAnalysis
)
from .decorators import user_passes_test_with_message


def is_hr_or_manager(user):
    """HR və ya rəhbər olub-olmadığını yoxlayır"""
    return user.rol in ['HR', 'MANAGER', 'SUPERADMIN']


@login_required
def performance_dashboard(request):
    """Performans İdarəetmə Dashboard"""
    context = {
        'page_title': 'Performans İdarəetmə',
        'active_nav': 'performance_dashboard'
    }
    return render(request, 'core/performance/dashboard.html', context)


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def performance_analytics(request):
    """Performans Analitika"""
    context = {
        'page_title': 'Performans Analitika',
        'active_nav': 'performance_analytics'
    }
    return render(request, 'core/performance/analytics.html', context)


@login_required
def goal_management(request):
    """Hədəf İdarəetmə"""
    context = {
        'page_title': 'Hədəf İdarəetmə',
        'active_nav': 'goal_management'
    }
    return render(request, 'core/performance/goal_management.html', context)


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def talent_review(request):
    """Talent Review"""
    context = {
        'page_title': 'Talent Review',
        'active_nav': 'talent_review'
    }
    return render(request, 'core/performance/talent_review.html', context)


@login_required
def career_development(request):
    """Karyera İnkişafı"""
    context = {
        'page_title': 'Karyera İnkişafı',
        'active_nav': 'career_development'
    }
    return render(request, 'core/performance/career_development.html', context)


@login_required
def performance_api_stats(request):
    """Performans statistikaları API"""
    try:
        user = request.user
        
        # Basic statistics
        stats = {}
        
        if user.rol in ['HR', 'MANAGER', 'SUPERADMIN']:
            # Manager/HR view
            stats = {
                'total_evaluations': Qiymetlendirme.objects.count(),
                'completed_evaluations': Qiymetlendirme.objects.filter(status='COMPLETED').count(),
                'pending_evaluations': Qiymetlendirme.objects.filter(status='PENDING').count(),
                'avg_performance_score': Qiymetlendirme.objects.filter(
                    status='COMPLETED'
                ).aggregate(avg_score=Avg('cavablar__xal'))['avg_score'] or 0,
                'active_development_plans': InkishafPlani.objects.filter(status='ACTIVE').count(),
                'high_performers': Qiymetlendirme.objects.filter(
                    status='COMPLETED',
                    cavablar__xal__gte=8
                ).values('qiymetlendirilen').distinct().count(),
                'low_performers': RiskFlag.objects.filter(
                    status='ACTIVE',
                    flag_type='LOW_PERFORMANCE'
                ).count(),
                'talent_pipeline': Ishchi.objects.filter(
                    rol__in=['manager', 'senior']
                ).count()
            }
        else:
            # Employee view
            user_evaluations = Qiymetlendirme.objects.filter(qiymetlendirilen=user)
            user_plans = InkishafPlani.objects.filter(ishchi=user)
            
            stats = {
                'my_evaluations': user_evaluations.count(),
                'completed_evaluations': user_evaluations.filter(status='COMPLETED').count(),
                'my_avg_score': user_evaluations.filter(
                    status='COMPLETED'
                ).aggregate(avg_score=Avg('cavablar__xal'))['avg_score'] or 0,
                'active_goals': user_plans.filter(status='ACTIVE').count(),
                'completed_goals': user_plans.filter(status='COMPLETED').count(),
                'feedback_received': getattr(user, 'received_quick_feedbacks', []).count() if hasattr(user, 'received_quick_feedbacks') else 0,
                'development_activities': 0,  # Placeholder
                'career_progress': 75  # Placeholder percentage
            }
        
        # Performance trends (last 6 months)
        performance_trends = {
            'labels': ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'İyun'],
            'data': [78, 82, 85, 83, 87, 89]  # Placeholder data
        }
        
        # Goal progress data
        goal_progress = [
            {'category': 'Texniki Bacarıqlar', 'progress': 85, 'target': 90},
            {'category': 'Liderlik', 'progress': 70, 'target': 80},
            {'category': 'Kommunikasiya', 'progress': 88, 'target': 90},
            {'category': 'İnnovasiya', 'progress': 65, 'target': 75}
        ]
        
        # Recent activities
        recent_activities = [
            {
                'title': 'Quarterly Review tamamlandı',
                'type': 'evaluation',
                'date': timezone.now().isoformat(),
                'status': 'completed'
            },
            {
                'title': 'Yeni hədəf təyin edildi',
                'type': 'goal',
                'date': (timezone.now() - timedelta(hours=2)).isoformat(),
                'status': 'active'
            },
            {
                'title': 'Müsbət feedback alındı',
                'type': 'feedback',
                'date': (timezone.now() - timedelta(hours=4)).isoformat(),
                'status': 'received'
            }
        ]
        
        return JsonResponse({
            'stats': stats,
            'performance_trends': performance_trends,
            'goal_progress': goal_progress,
            'recent_activities': recent_activities
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def performance_matrix_api(request):
    """Performans Matrix API - 9-box grid data"""
    try:
        # Placeholder data for 9-box performance-potential matrix
        matrix_data = [
            {'name': 'Ayşe Məmmədova', 'performance': 9, 'potential': 8, 'position': 'Developer'},
            {'name': 'Məhəmməd Əliyev', 'performance': 8, 'potential': 9, 'position': 'Team Lead'},
            {'name': 'Günel Həsənli', 'performance': 7, 'potential': 7, 'position': 'QA Engineer'},
            {'name': 'Rəşad Quliyev', 'performance': 9, 'potential': 6, 'position': 'Senior Developer'},
            {'name': 'Leyla Nağıyeva', 'performance': 6, 'potential': 8, 'position': 'Junior Developer'},
            {'name': 'Elbrus Məmmədli', 'performance': 8, 'potential': 7, 'position': 'DevOps Engineer'},
        ]
        
        # Performance distribution
        distribution = {
            'high_performance_high_potential': 15,  # Stars
            'high_performance_medium_potential': 20,  # Core Players
            'high_performance_low_potential': 10,  # Specialists
            'medium_performance_high_potential': 25,  # Future Leaders
            'medium_performance_medium_potential': 20,  # Core Team
            'medium_performance_low_potential': 5,  # Steady Contributors
            'low_performance_high_potential': 3,  # Rough Diamonds
            'low_performance_medium_potential': 2,  # Dilemmas
            'low_performance_low_potential': 0   # Out
        }
        
        return JsonResponse({
            'matrix_data': matrix_data,
            'distribution': distribution
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def goals_api(request):
    """Hədəflər API"""
    try:
        user = request.user
        
        if request.method == 'GET':
            # Get user's goals
            goals = []
            if user.rol in ['HR', 'MANAGER', 'SUPERADMIN']:
                plans = InkishafPlani.objects.all()[:20]
            else:
                plans = InkishafPlani.objects.filter(ishchi=user)
            
            for plan in plans:
                owner_name = plan.ishchi.get_full_name() if getattr(plan, 'ishchi', None) and hasattr(plan.ishchi, 'get_full_name') else ''
                deadline = (plan.yaradilma_tarixi.date() + timedelta(days=365)) if getattr(plan, 'yaradilma_tarixi', None) else None
                goals.append({
                    'id': plan.id,
                    'title': f"{owner_name} - İnkişaf Planı",
                    'description': getattr(plan, 'description', 'İnkişaf planı'),
                    'progress': 75,  # Placeholder
                    'deadline': deadline,
                    'status': plan.status,
                    'owner': owner_name,
                    'priority': 'high'  # Placeholder
                })
            
            return JsonResponse({'goals': goals})
            
        elif request.method == 'POST':
            # Create new goal (placeholder)
            data = json.loads(request.body)
            return JsonResponse({
                'success': True,
                'message': 'Hədəf uğurla yaradıldı',
                'goal_id': 999  # Placeholder
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)