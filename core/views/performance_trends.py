"""
Performance Trends (İnkişaf Trendi) Views
İşçilərin zaman ərzində performans trendlərini analiz edir
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta, datetime
import json

from ..models import (
    Ishchi, Qiymetlendirme, Cavab, QiymetlendirmeDovru, 
    SualKateqoriyasi
)
from ..permissions import require_role


@login_required
def performance_trends_dashboard(request):
    """Performance trends ana səhifəsi"""
    
    user_id = request.GET.get('user_id')
    
    # Əgər user_id verilmişsə və icazə varsa, həmin istifadəçinin məlumatını göstər
    if user_id and (request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']):
        target_user = get_object_or_404(Ishchi, id=user_id)
    else:
        target_user = request.user
    
    # Son 2 illik dövrləri tap
    two_years_ago = timezone.now().date() - timedelta(days=730)
    cycles = QiymetlendirmeDovru.objects.filter(
        bashlama_tarixi__gte=two_years_ago
    ).order_by('bashlama_tarixi')
    
    # İstifadəçinin trend məlumatları
    trend_data = get_user_performance_trend(target_user, cycles)
    
    # Benchmark məlumatları
    benchmark_data = get_benchmark_data(target_user, cycles)
    
    context = {
        'target_user': target_user,
        'trend_data': trend_data,
        'benchmark_data': benchmark_data,
        'cycles': cycles,
        'page_title': f'İnkişaf Trendi: {target_user.get_full_name()}',
        'show_user_selector': request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']
    }
    
    return render(request, 'performance_trends/dashboard.html', context)


@login_required
def performance_trends_api(request):
    """Performance trends üçün AJAX API"""
    
    user_id = request.GET.get('user_id')
    period = request.GET.get('period', '2_years')  # 6_months, 1_year, 2_years
    
    if user_id and (request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']):
        target_user = get_object_or_404(Ishchi, id=user_id)
    else:
        target_user = request.user
    
    # Cache key
    cache_key = f"performance_trends_{target_user.id}_{period}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data)
    
    # Dövr müddəti
    if period == '6_months':
        start_date = timezone.now().date() - timedelta(days=180)
    elif period == '1_year':
        start_date = timezone.now().date() - timedelta(days=365)
    else:  # 2_years
        start_date = timezone.now().date() - timedelta(days=730)
    
    cycles = QiymetlendirmeDovru.objects.filter(
        bashlama_tarixi__gte=start_date
    ).order_by('bashlama_tarixi')
    
    # Trend məlumatları
    trend_data = get_user_performance_trend(target_user, cycles)
    
    # Chart.js üçün format
    api_data = {
        'user_name': target_user.get_full_name(),
        'period': period,
        'overall_trend': {
            'labels': [item['cycle_name'] for item in trend_data['overall']],
            'data': [item['average_score'] for item in trend_data['overall']],
            'trend_direction': calculate_trend_direction([item['average_score'] for item in trend_data['overall']])
        },
        'categories_trend': {}
    }
    
    # Kateqoriyalar üzrə trendlər
    for category_name, category_data in trend_data['categories'].items():
        api_data['categories_trend'][category_name] = {
            'labels': [item['cycle_name'] for item in category_data],
            'data': [item['average_score'] for item in category_data],
            'trend_direction': calculate_trend_direction([item['average_score'] for item in category_data])
        }
    
    # 10 dəqiqə cache
    cache.set(cache_key, api_data, 600)
    
    return JsonResponse(api_data)


@login_required
@require_role(['ADMIN', 'SUPERADMIN', 'REHBER'])
def department_trends_comparison(request):
    """Şöbələr arası trend müqayisəsi"""
    
    department_ids = request.GET.getlist('department_ids')
    period = request.GET.get('period', '1_year')
    
    if not department_ids:
        return JsonResponse({'error': 'Heç bir şöbə seçilməyib'})
    
    # Dövr müddəti
    if period == '6_months':
        start_date = timezone.now().date() - timedelta(days=180)
    elif period == '1_year':
        start_date = timezone.now().date() - timedelta(days=365)
    else:  # 2_years
        start_date = timezone.now().date() - timedelta(days=730)
    
    cycles = QiymetlendirmeDovru.objects.filter(
        bashlama_tarixi__gte=start_date
    ).order_by('bashlama_tarixi')
    
    departments_data = []
    
    for dept_id in department_ids:
        dept_trend = get_department_performance_trend(dept_id, cycles)
        departments_data.append(dept_trend)
    
    context = {
        'departments_data': departments_data,
        'cycles': cycles,
        'period': period,
        'page_title': 'Şöbələr Arası Trend Müqayisəsi'
    }
    
    return render(request, 'performance_trends/department_comparison.html', context)


@login_required
def individual_category_trend(request, user_id, category_id):
    """Fərdi kateqoriya trendi detaylı görünüş"""
    
    target_user = get_object_or_404(Ishchi, id=user_id)
    category = get_object_or_404(SualKateqoriyasi, id=category_id)
    
    # İcazə yoxlaması
    if target_user != request.user and request.user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']:
        return JsonResponse({'error': 'İcazəsiz giriş'}, status=403)
    
    # Son 2 illik dövrləri tap
    two_years_ago = timezone.now().date() - timedelta(days=730)
    cycles = QiymetlendirmeDovru.objects.filter(
        bashlama_tarixi__gte=two_years_ago
    ).order_by('bashlama_tarixi')
    
    # Bu kateqoriya üçün detallı trend
    category_trend = get_category_detailed_trend(target_user, category, cycles)
    
    context = {
        'target_user': target_user,
        'category': category,
        'category_trend': category_trend,
        'cycles': cycles,
        'page_title': f'{category.ad} Trendi - {target_user.get_full_name()}'
    }
    
    return render(request, 'performance_trends/category_detail.html', context)


def get_user_performance_trend(user, cycles):
    """
    İstifadəçinin performans trendini hesablayır
    """
    overall_trend = []
    categories_trend = {}
    
    for cycle in cycles:
        # Bu dövrdəki qiymətləndirmələr (self-review xaric)
        evaluations = Qiymetlendirme.objects.filter(
            qiymetlendirilen=user,
            dovr=cycle,
            status=Qiymetlendirme.Status.TAMAMLANDI
        ).exclude(
            qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
        )
        
        if not evaluations.exists():
            continue
        
        # Ümumi ortalama
        all_answers = Cavab.objects.filter(qiymetlendirme__in=evaluations)
        if all_answers.exists():
            overall_avg = all_answers.aggregate(Avg('xal'))['xal__avg']
            overall_trend.append({
                'cycle_name': cycle.ad,
                'cycle_date': cycle.bashlama_tarixi,
                'average_score': round(overall_avg, 2),
                'evaluations_count': evaluations.count()
            })
        
        # Kateqoriyalar üzrə ortalama
        for category in SualKateqoriyasi.objects.all():
            category_answers = Cavab.objects.filter(
                qiymetlendirme__in=evaluations,
                sual__kateqoriya=category
            )
            
            if category_answers.exists():
                category_avg = category_answers.aggregate(Avg('xal'))['xal__avg']
                
                if category.ad not in categories_trend:
                    categories_trend[category.ad] = []
                
                categories_trend[category.ad].append({
                    'cycle_name': cycle.ad,
                    'cycle_date': cycle.bashlama_tarixi,
                    'average_score': round(category_avg, 2),
                    'answers_count': category_answers.count()
                })
    
    return {
        'overall': overall_trend,
        'categories': categories_trend
    }


def get_department_performance_trend(department_id, cycles):
    """
    Şöbənin performans trendini hesablayır
    """
    from ..models import OrganizationUnit
    
    try:
        department = OrganizationUnit.objects.get(id=department_id)
    except OrganizationUnit.DoesNotExist:
        return None
    
    department_trend = []
    
    for cycle in cycles:
        # Şöbədəki işçilərin qiymətləndirmələri
        evaluations = Qiymetlendirme.objects.filter(
            qiymetlendirilen__organization_unit=department,
            dovr=cycle,
            status=Qiymetlendirme.Status.TAMAMLANDI
        ).exclude(
            qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
        )
        
        if evaluations.exists():
            all_answers = Cavab.objects.filter(qiymetlendirme__in=evaluations)
            if all_answers.exists():
                avg_score = all_answers.aggregate(Avg('xal'))['xal__avg']
                department_trend.append({
                    'cycle_name': cycle.ad,
                    'cycle_date': cycle.bashlama_tarixi,
                    'average_score': round(avg_score, 2),
                    'employees_count': evaluations.values('qiymetlendirilen').distinct().count()
                })
    
    return {
        'department_name': department.name,
        'trend_data': department_trend
    }


def get_category_detailed_trend(user, category, cycles):
    """
    Müəyyən kateqoriya üçün detallı trend analizi
    """
    detailed_trend = []
    
    for cycle in cycles:
        # Bu dövr və kateqoriya üçün qiymətləndirmələr
        evaluations = Qiymetlendirme.objects.filter(
            qiymetlendirilen=user,
            dovr=cycle,
            status=Qiymetlendirme.Status.TAMAMLANDI
        ).exclude(
            qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
        )
        
        if not evaluations.exists():
            continue
        
        category_answers = Cavab.objects.filter(
            qiymetlendirme__in=evaluations,
            sual__kateqoriya=category
        )
        
        if category_answers.exists():
            # Ortalama bal
            avg_score = category_answers.aggregate(Avg('xal'))['xal__avg']
            
            # Bu dövrün qiymətləndirənləri
            evaluators = evaluations.values_list('qiymetlendiren__first_name', 'qiymetlendiren__last_name')
            
            detailed_trend.append({
                'cycle_name': cycle.ad,
                'cycle_date': cycle.bashlama_tarixi,
                'average_score': round(avg_score, 2),
                'answers_count': category_answers.count(),
                'evaluators_count': evaluations.count(),
                'evaluators': [f"{first} {last}" for first, last in evaluators]
            })
    
    return detailed_trend


def get_benchmark_data(user, cycles):
    """
    İstifadəçi üçün benchmark məlumatları
    """
    benchmark = {
        'department_average': [],
        'company_average': []
    }
    
    for cycle in cycles:
        # Şöbə ortalaması
        if user.organization_unit:
            dept_evaluations = Qiymetlendirme.objects.filter(
                qiymetlendirilen__organization_unit=user.organization_unit,
                dovr=cycle,
                status=Qiymetlendirme.Status.TAMAMLANDI
            ).exclude(
                qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
            )
            
            if dept_evaluations.exists():
                dept_answers = Cavab.objects.filter(qiymetlendirme__in=dept_evaluations)
                if dept_answers.exists():
                    dept_avg = dept_answers.aggregate(Avg('xal'))['xal__avg']
                    benchmark['department_average'].append({
                        'cycle_name': cycle.ad,
                        'average_score': round(dept_avg, 2)
                    })
        
        # Şirkət ortalaması
        company_evaluations = Qiymetlendirme.objects.filter(
            dovr=cycle,
            status=Qiymetlendirme.Status.TAMAMLANDI
        ).exclude(
            qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
        )
        
        if company_evaluations.exists():
            company_answers = Cavab.objects.filter(qiymetlendirme__in=company_evaluations)
            if company_answers.exists():
                company_avg = company_answers.aggregate(Avg('xal'))['xal__avg']
                benchmark['company_average'].append({
                    'cycle_name': cycle.ad,
                    'average_score': round(company_avg, 2)
                })
    
    return benchmark


def calculate_trend_direction(scores):
    """
    Trend istiqamətini hesablayır (yüksələn, enən, sabit)
    """
    if len(scores) < 2:
        return 'insufficient_data'
    
    # Linear regression ilə trend hesabla
    n = len(scores)
    x_sum = sum(range(n))
    y_sum = sum(scores)
    xy_sum = sum(i * score for i, score in enumerate(scores))
    x2_sum = sum(i * i for i in range(n))
    
    # Slope hesabla
    slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
    
    if slope > 0.1:
        return 'increasing'
    elif slope < -0.1:
        return 'decreasing'
    else:
        return 'stable'