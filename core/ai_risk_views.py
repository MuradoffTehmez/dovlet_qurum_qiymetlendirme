# core/ai_risk_views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    RiskFlag, EmployeeRiskAnalysis, PsychologicalRiskSurvey, 
    PsychologicalRiskResponse, QiymetlendirmeDovru
)
from .decorators import user_passes_test_with_message

User = get_user_model()


def is_hr_or_manager(user):
    """HR və ya rəhbər olub-olmadığını yoxlayır"""
    return user.rol in ['hr', 'manager', 'superadmin']


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def ai_risk_dashboard(request):
    """AI Risk Detection Dashboard"""
    context = {
        'page_title': 'AI Risk Detection Dashboard',
        'active_nav': 'ai_risk_dashboard'
    }
    return render(request, 'core/ai_risk/dashboard.html', context)


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def risk_flags_management(request):
    """Risk Flags Management Interface"""
    context = {
        'page_title': 'Risk Flags Management',
        'active_nav': 'risk_flags'
    }
    return render(request, 'core/ai_risk/risk_flags.html', context)


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def psychological_surveys(request):
    """Psychological Surveys Management Interface"""
    context = {
        'page_title': 'Psychological Risk Surveys',
        'active_nav': 'psychological_surveys'
    }
    return render(request, 'core/ai_risk/psychological_surveys.html', context)


@login_required
@user_passes_test_with_message(is_hr_or_manager, "Bu səhifəyə giriş yalnız HR və rəhbər istifadəçilərinə açıqdır.")
def strategic_hr_planning(request):
    """Strategic HR Planning Interface"""
    context = {
        'page_title': 'Strategic HR Planning',
        'active_nav': 'strategic_hr_planning'
    }
    return render(request, 'core/ai_risk/strategic_hr_planning.html', context)


@login_required
def ai_risk_dashboard_api(request):
    """AI Risk Dashboard API endpoint"""
    try:
        # Get statistics
        stats = {
            'active_flags': RiskFlag.objects.filter(status='ACTIVE').count(),
            'high_risk': RiskFlag.objects.filter(
                status='ACTIVE', 
                severity__in=['HIGH', 'CRITICAL']
            ).count(),
            'resolved': RiskFlag.objects.filter(status='RESOLVED').count(),
            'avg_risk_score': RiskFlag.objects.filter(
                status='ACTIVE'
            ).aggregate(avg_score=Avg('risk_score'))['avg_score'] or 0
        }
        
        # Get recent risk flags
        risk_flags = RiskFlag.objects.filter(
            status='ACTIVE'
        ).select_related('employee', 'cycle').order_by('-detected_at')[:10]
        
        risk_flags_data = []
        for flag in risk_flags:
            risk_flags_data.append({
                'id': flag.id,
                'employee': {
                    'full_name': flag.employee.get_full_name(),
                    'department': getattr(flag.employee.organization_unit, 'name', ''),
                    'profile_image': flag.employee.profil_sekli.url if flag.employee.profil_sekli else None
                },
                'flag_type_display': flag.get_flag_type_display(),
                'severity': flag.severity,
                'risk_score': flag.risk_score,
                'created_at': flag.detected_at.isoformat()
            })
        
        # Get risk distribution
        distribution = {
            'LOW': RiskFlag.objects.filter(status='ACTIVE', severity='LOW').count(),
            'MEDIUM': RiskFlag.objects.filter(status='ACTIVE', severity='MEDIUM').count(),
            'HIGH': RiskFlag.objects.filter(status='ACTIVE', severity='HIGH').count(),
            'CRITICAL': RiskFlag.objects.filter(status='ACTIVE', severity='CRITICAL').count(),
        }
        
        # Get trends (last 7 days)
        trends_data = []
        trends_labels = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            daily_avg = RiskFlag.objects.filter(
                detected_at__date=date,
                status='ACTIVE'
            ).aggregate(avg_score=Avg('risk_score'))['avg_score'] or 0
            
            trends_data.insert(0, round(daily_avg, 1))
            trends_labels.insert(0, date.strftime('%m/%d'))
        
        trends = {
            'labels': trends_labels,
            'data': trends_data
        }
        
        # Recent activity
        recent_activity = []
        recent_flags = RiskFlag.objects.order_by('-detected_at')[:5]
        for flag in recent_flags:
            activity_type = 'danger' if flag.severity in ['HIGH', 'CRITICAL'] else 'warning'
            recent_activity.append({
                'title': f'New {flag.get_flag_type_display()} Risk Flag',
                'description': f'{flag.employee.get_full_name()} - {flag.severity} severity',
                'timestamp': flag.detected_at.isoformat(),
                'type': activity_type
            })
        
        return JsonResponse({
            'stats': stats,
            'risk_flags': risk_flags_data,
            'distribution': distribution,
            'trends': trends,
            'recent_activity': recent_activity
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ai_risk_trends_api(request):
    """AI Risk Trends API endpoint"""
    try:
        period = request.GET.get('period', 'week')
        
        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        elif period == 'quarter':
            days = 90
        else:
            days = 7
        
        trends_data = []
        trends_labels = []
        
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            daily_avg = RiskFlag.objects.filter(
                detected_at__date=date,
                status='ACTIVE'
            ).aggregate(avg_score=Avg('risk_score'))['avg_score'] or 0
            
            trends_data.insert(0, round(daily_avg, 1))
            
            if period == 'week':
                trends_labels.insert(0, date.strftime('%m/%d'))
            else:
                trends_labels.insert(0, date.strftime('%m/%d'))
        
        return JsonResponse({
            'labels': trends_labels,
            'data': trends_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)