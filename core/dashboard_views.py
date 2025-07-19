# core/dashboard_views.py
"""
İnteraktiv Dashboard Views
Real-time statistikalar, interactive charts və widgets
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Avg, Q, Max, Min, Sum
from django.core.cache import cache
from datetime import datetime, timedelta, date
import json

from .models import (
    Ishchi, Qiymetlendirme, InkishafPlani, Hedef, 
    OrganizationUnit, QiymetlendirmeDovru, Notification
)
from .permissions import permission_required
# utils import dashboard_views.py-də lazım olmayacaq, çünki funksiya orada təyin edilib


@login_required
def interactive_dashboard(request):
    """İnteraktiv dashboard ana səhifəsi"""
    context = {
        'title': 'İnteraktiv İdarə Paneli',
        'user_role': request.user.rol,
        'is_manager': request.user.rol in ['REHBER', 'ADMIN', 'SUPERADMIN'],
        'current_date': timezone.now().date()
    }
    return render(request, 'core/dashboard/interactive_dashboard.html', context)


@login_required
def dashboard_stats_api(request):
    """Dashboard üçün real-time statistikalar API"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    # Cache key
    cache_key = f'dashboard_stats_{request.user.id}_{request.user.rol}'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = _generate_dashboard_stats(request.user)
        cache.set(cache_key, stats, 180)  # 3 dəqiqə cache
    
    return JsonResponse(stats)


def _generate_dashboard_stats(user):
    """Dashboard statistikalarını generasiya edir"""
    today = timezone.now().date()
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # Əsas statistikalar
    stats = {
        'personal': {
            'pending_evaluations': Qiymetlendirme.objects.filter(
                qiymetlendirilen=user,
                umumi_qiymet__isnull=True
            ).count(),
            'completed_evaluations': Qiymetlendirme.objects.filter(
                qiymetlendirilen=user,
                umumi_qiymet__isnull=False
            ).count(),
            'active_goals': Hedef.objects.filter(
                plan__ishchi=user,
                status__in=['BASHLANMAYIB', 'ICRADA']
            ).count(),
            'completed_goals': Hedef.objects.filter(
                plan__ishchi=user,
                status='TAMAMLANIB'
            ).count(),
            'unread_notifications': Notification.objects.filter(
                recipient=user,
                is_read=False
            ).count(),
            'avg_performance': Qiymetlendirme.objects.filter(
                qiymetlendirilen=user
            ).aggregate(avg_score=Avg('umumi_qiymet'))['avg_score'] or 0
        },
        'trends': {
            'this_month_evaluations': Qiymetlendirme.objects.filter(
                qiymetlendirilen=user,
                tarix__gte=this_month
            ).count(),
            'last_month_evaluations': Qiymetlendirme.objects.filter(
                qiymetlendirilen=user,
                tarix__gte=last_month,
                tarix__lt=this_month
            ).count(),
            'goals_completion_rate': _calculate_goal_completion_rate(user),
            'performance_trend': _get_performance_trend(user)
        }
    }
    
    # Manager statistikaları
    if user.rol in ['REHBER', 'ADMIN', 'SUPERADMIN']:
        stats['team'] = _get_team_statistics(user)
        stats['organization'] = _get_organization_statistics(user)
    
    return stats


def _calculate_goal_completion_rate(user):
    """Hədəf tamamlanma faizini hesablayır"""
    total_goals = Hedef.objects.filter(plan__ishchi=user).count()
    completed_goals = Hedef.objects.filter(
        plan__ishchi=user,
        status='TAMAMLANIB'
    ).count()
    
    if total_goals == 0:
        return 0
    
    return round((completed_goals / total_goals) * 100, 1)


def _get_performance_trend(user):
    """Son 6 ayın performans trendini qaytarır"""
    trends = []
    for i in range(6):
        month_start = (timezone.now().date().replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        avg_score = Qiymetlendirme.objects.filter(
            qiymetlendirilen=user,
            tarix__range=[month_start, month_end]
        ).aggregate(avg=Avg('umumi_qiymet'))['avg'] or 0
        
        trends.append({
            'month': month_start.strftime('%Y-%m'),
            'score': round(avg_score, 1)
        })
    
    return list(reversed(trends))


def _get_team_statistics(user):
    """Komanda statistikalarını qaytarır"""
    if not user.organization_unit:
        return {}
    
    team_members = Ishchi.objects.filter(
        organization_unit=user.organization_unit,
        is_active=True
    ).exclude(id=user.id)
    
    return {
        'total_members': team_members.count(),
        'avg_team_performance': team_members.aggregate(
            avg=Avg('qiymetlendirme_qiymetlendirilen__umumi_qiymet')
        )['avg'] or 0,
        'pending_team_evaluations': Qiymetlendirme.objects.filter(
            qiymetlendirilen__in=team_members,
            umumi_qiymet__isnull=True
        ).count(),
        'active_team_goals': Hedef.objects.filter(
            plan__ishchi__in=team_members,
            status__in=['BASHLANMAYIB', 'ICRADA']
        ).count()
    }


def _get_organization_statistics(user):
    """Təşkilat statistikalarını qaytarır"""
    return {
        'total_employees': Ishchi.objects.filter(is_active=True).count(),
        'total_departments': OrganizationUnit.objects.count(),
        'active_evaluation_periods': QiymetlendirmeDovru.objects.filter(
            bashlama_tarixi__lte=timezone.now().date(),
            bitme_tarixi__gte=timezone.now().date()
        ).count(),
        'monthly_evaluations': Qiymetlendirme.objects.filter(
            tarix__month=timezone.now().month
        ).count()
    }


@login_required
def performance_chart_api(request):
    """Performans chart məlumatları API"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    chart_type = request.GET.get('type', 'performance_trend')
    period = request.GET.get('period', '6_months')
    
    if chart_type == 'performance_trend':
        data = _get_performance_chart_data(request.user, period)
    elif chart_type == 'goal_progress':
        data = _get_goal_progress_data(request.user)
    elif chart_type == 'department_comparison' and request.user.rol in ['ADMIN', 'SUPERADMIN']:
        data = _get_department_comparison_data()
    else:
        return JsonResponse({'error': 'Naməlum chart növü'}, status=400)
    
    return JsonResponse(data)


def _get_performance_chart_data(user, period):
    """Performans chart məlumatlarını hazırlayır"""
    if period == '6_months':
        months = 6
    elif period == '12_months':
        months = 12
    else:
        months = 6
    
    chart_data = {
        'labels': [],
        'datasets': [{
            'label': 'Performans Balı',
            'data': [],
            'borderColor': 'rgb(102, 126, 234)',
            'backgroundColor': 'rgba(102, 126, 234, 0.1)',
            'tension': 0.4
        }]
    }
    
    for i in range(months):
        month_start = (timezone.now().date().replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        avg_score = Qiymetlendirme.objects.filter(
            qiymetlendirilen=user,
            tarix__range=[month_start, month_end]
        ).aggregate(avg=Avg('umumi_qiymet'))['avg'] or 0
        
        chart_data['labels'].insert(0, month_start.strftime('%b %Y'))
        chart_data['datasets'][0]['data'].insert(0, round(avg_score, 1))
    
    return chart_data


def _get_goal_progress_data(user):
    """Hədəf irəliləyiş məlumatlarını hazırlayır"""
    goals = Hedef.objects.filter(plan__ishchi=user)
    
    status_counts = goals.values('status').annotate(count=Count('id'))
    
    chart_data = {
        'labels': [],
        'datasets': [{
            'data': [],
            'backgroundColor': [
                '#28a745',  # Tamamlanıb - yaşıl
                '#ffc107',  # İcrada - sarı  
                '#6c757d',  # Başlanmayıb - boz
                '#dc3545'   # Ləğv edilib - qırmızı
            ]
        }]
    }
    
    status_map = {
        'TAMAMLANIB': 'Tamamlanıb',
        'ICRADA': 'İcrada',
        'BASHLANMAYIB': 'Başlanmayıb',
        'LEGV_EDILIB': 'Ləğv edilib'
    }
    
    for status_count in status_counts:
        status = status_count['status']
        count = status_count['count']
        
        chart_data['labels'].append(status_map.get(status, status))
        chart_data['datasets'][0]['data'].append(count)
    
    return chart_data


def _get_department_comparison_data():
    """Şöbələr müqayisə məlumatlarını hazırlayır"""
    departments = OrganizationUnit.objects.annotate(
        avg_performance=Avg('ishchiler__qiymetlendirme_qiymetlendirilen__umumi_qiymet'),
        employee_count=Count('ishchiler', filter=Q(ishchiler__is_active=True))
    ).filter(employee_count__gt=0)
    
    chart_data = {
        'labels': [],
        'datasets': [{
            'label': 'Orta Performans',
            'data': [],
            'backgroundColor': 'rgba(102, 126, 234, 0.8)'
        }]
    }
    
    for dept in departments:
        chart_data['labels'].append(dept.name)
        chart_data['datasets'][0]['data'].append(
            round(dept.avg_performance or 0, 1)
        )
    
    return chart_data


@login_required
@require_http_methods(["POST"])
def dashboard_widget_preferences(request):
    """Dashboard widget preferences API"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    try:
        data = json.loads(request.body)
        widget_id = data.get('widget_id')
        preferences = data.get('preferences', {})
        
        # Cache-də user preferences saxla
        cache_key = f'dashboard_widgets_{request.user.id}'
        user_widgets = cache.get(cache_key, {})
        user_widgets[widget_id] = preferences
        cache.set(cache_key, user_widgets, 86400)  # 24 saat
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Yanlış JSON formatı'}, status=400)


@login_required
def dashboard_widget_data(request, widget_type):
    """Specific widget məlumatları API"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    if widget_type == 'recent_activities':
        data = _get_recent_activities_data(request.user)
    elif widget_type == 'upcoming_deadlines':
        data = _get_upcoming_deadlines_data(request.user)
    elif widget_type == 'team_performance' and request.user.rol in ['REHBER', 'ADMIN', 'SUPERADMIN']:
        data = _get_team_performance_data(request.user)
    elif widget_type == 'quick_stats':
        data = _get_quick_stats_data(request.user)
    else:
        return JsonResponse({'error': 'Naməlum widget növü'}, status=400)
    
    return JsonResponse(data)


def _get_recent_activities_data(user):
    """Son fəaliyyətlər məlumatlarını qaytarır"""
    activities = []
    
    # Son qiymətləndirmələr
    recent_evaluations = Qiymetlendirme.objects.filter(
        Q(qiymetlendirilen=user) | Q(qiymetlendiren=user)
    ).order_by('-tarix')[:5]
    
    for evaluation in recent_evaluations:
        if evaluation.qiymetlendirilen == user:
            activities.append({
                'type': 'evaluation_received',
                'title': f'Qiymətləndirmə alındı',
                'description': f'{evaluation.qiymetlendiren.get_full_name()} tərəfindən',
                'date': evaluation.tarix.strftime('%d.%m.%Y'),
                'icon': 'fas fa-star',
                'color': 'primary'
            })
        else:
            activities.append({
                'type': 'evaluation_given',
                'title': f'Qiymətləndirmə verildi',
                'description': f'{evaluation.qiymetlendirilen.get_full_name()} üçün',
                'date': evaluation.tarix.strftime('%d.%m.%Y'),
                'icon': 'fas fa-clipboard-check',
                'color': 'success'
            })
    
    # Son bildirişlər
    recent_notifications = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:3]
    
    for notification in recent_notifications:
        activities.append({
            'type': 'notification',
            'title': notification.title,
            'description': notification.message[:50] + '...' if len(notification.message) > 50 else notification.message,
            'date': notification.created_at.strftime('%d.%m.%Y'),
            'icon': 'fas fa-bell',
            'color': 'info'
        })
    
    # Tarixə görə sırala
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    return {'activities': activities[:8]}


def _get_upcoming_deadlines_data(user):
    """Yaxınlaşan son tarixlər məlumatlarını qaytarır"""
    today = timezone.now().date()
    next_month = today + timedelta(days=30)
    
    upcoming_goals = Hedef.objects.filter(
        plan__ishchi=user,
        son_tarix__range=[today, next_month],
        status__in=['BASHLANMAYIB', 'ICRADA']
    ).order_by('son_tarix')
    
    deadlines = []
    for goal in upcoming_goals:
        days_left = (goal.son_tarix - today).days
        
        if days_left < 0:
            urgency = 'overdue'
            color = 'danger'
        elif days_left <= 3:
            urgency = 'critical'
            color = 'danger'
        elif days_left <= 7:
            urgency = 'urgent'
            color = 'warning'
        else:
            urgency = 'normal'
            color = 'primary'
        
        deadlines.append({
            'title': goal.tesvir,
            'deadline': goal.son_tarix.strftime('%d.%m.%Y'),
            'days_left': days_left,
            'urgency': urgency,
            'color': color,
            'plan_id': goal.plan.id
        })
    
    return {'deadlines': deadlines}


def _get_team_performance_data(user):
    """Komanda performans məlumatlarını qaytarır"""
    if not user.organization_unit:
        return {'team_members': []}
    
    team_members = Ishchi.objects.filter(
        organization_unit=user.organization_unit,
        is_active=True
    ).exclude(id=user.id)
    
    team_data = []
    for member in team_members:
        avg_performance = Qiymetlendirme.objects.filter(
            qiymetlendirilen=member
        ).aggregate(avg=Avg('umumi_qiymet'))['avg'] or 0
        
        team_data.append({
            'name': member.get_full_name(),
            'role': member.get_rol_display(),
            'avg_performance': round(avg_performance, 1),
            'active_goals': Hedef.objects.filter(
                plan__ishchi=member,
                status__in=['BASHLANMAYIB', 'ICRADA']
            ).count()
        })
    
    return {'team_members': team_data}


def _get_quick_stats_data(user):
    """Tez statistika məlumatlarını qaytarır"""
    today = timezone.now().date()
    this_week = today - timedelta(days=today.weekday())
    
    return {
        'this_week_evaluations': Qiymetlendirme.objects.filter(
            Q(qiymetlendirilen=user) | Q(qiymetlendiren=user),
            tarix__gte=this_week
        ).count(),
        'pending_tasks': Qiymetlendirme.objects.filter(
            qiymetlendirilen=user,
            umumi_qiymet__isnull=True
        ).count(),
        'completion_rate': _calculate_goal_completion_rate(user),
        'notification_count': Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    }