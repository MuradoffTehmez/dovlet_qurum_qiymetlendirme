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
    
    # Template üçün əlavə məlumatlar
    current_score = 0
    score_trend = 0
    average_growth = 0
    predicted_next_score = 0
    consistency_score = 0
    six_month_prediction = 0
    performance_level = 'needs-improvement'
    total_evaluations = 0
    evaluation_frequency = 0
    department_rank = 1
    
    if trend_data['overall']:
        scores = [item['average_score'] for item in trend_data['overall']]
        if scores:
            current_score = scores[-1]
            
            # Score trend (comparing last two periods)
            if len(scores) >= 2:
                score_trend = scores[-1] - scores[-2]
            
            # Average growth calculation
            if len(scores) >= 2:
                total_change = scores[-1] - scores[0]
                periods = len(scores) - 1
                average_growth = (total_change / periods) * 100 / 10  # Percentage
            
            # Consistency score (inverse of standard deviation)
            if len(scores) > 1:
                import statistics
                std_dev = statistics.stdev(scores)
                consistency_score = max(0, 100 - (std_dev * 10))
            
            # Performance level
            if current_score >= 8.5:
                performance_level = 'excellent'
            elif current_score >= 7.0:
                performance_level = 'good'
            else:
                performance_level = 'needs-improvement'
            
            # Simple prediction (linear trend)
            if len(scores) >= 3:
                recent_trend = (scores[-1] - scores[-3]) / 2
                predicted_next_score = min(10, max(0, current_score + recent_trend))
                six_month_prediction = min(10, max(0, current_score + recent_trend * 2))
            else:
                predicted_next_score = current_score
                six_month_prediction = current_score
        
        # Total evaluations
        total_evaluations = sum(item['evaluations_count'] for item in trend_data['overall'])
        
        # Evaluation frequency (per month)
        if cycles.exists():
            months_span = len(trend_data['overall'])
            if months_span > 0:
                evaluation_frequency = total_evaluations / months_span
    
    # Category trends with direction analysis
    category_trends = []
    if trend_data['categories']:
        for category_name, category_data in trend_data['categories'].items():
            if category_data:
                scores = [item['average_score'] for item in category_data]
                current_cat_score = scores[-1] if scores else 0
                
                # Trend direction
                trend_direction = 'stable'
                change = 0
                if len(scores) >= 2:
                    change = scores[-1] - scores[-2]
                    if change > 0.3:
                        trend_direction = 'improving'
                    elif change < -0.3:
                        trend_direction = 'declining'
                
                category_trends.append({
                    'id': category_name.replace(' ', '_').lower(),
                    'name': category_name,
                    'current_score': current_cat_score,
                    'change': change,
                    'trend_direction': trend_direction,
                    'question_count': len(category_data)
                })
    
    # Top performing and improvement areas
    top_performing_areas = []
    improvement_areas = []
    
    if category_trends:
        sorted_categories = sorted(category_trends, key=lambda x: x['current_score'], reverse=True)
        top_performing_areas = sorted_categories[:3]
        improvement_areas = sorted_categories[-3:]
    
    # Chart data preparation
    trend_chart_data = {
        'labels': [item['cycle_name'] for item in trend_data['overall']],
        'user_scores': [item['average_score'] for item in trend_data['overall']],
        'predictions': []  # Will be filled with ML predictions
    }
    
    # Add simple predictions to chart
    if trend_chart_data['user_scores']:
        last_score = trend_chart_data['user_scores'][-1]
        trend_chart_data['predictions'] = [None] * len(trend_chart_data['user_scores'])
        trend_chart_data['predictions'].append(predicted_next_score)
        trend_chart_data['labels'].append('Proqnoz')
    
    # Comparative chart data
    comparative_chart_data = {
        'labels': [item['cycle_name'] for item in trend_data['overall']],
        'user_scores': [item['average_score'] for item in trend_data['overall']],
        'department_averages': [],
        'company_averages': []
    }
    
    # Fill benchmark data if available
    if benchmark_data:
        for dept_item in benchmark_data.get('department_average', []):
            comparative_chart_data['department_averages'].append(dept_item['average_score'])
        
        for comp_item in benchmark_data.get('company_average', []):
            comparative_chart_data['company_averages'].append(comp_item['average_score'])
    
    # Ensure arrays are same length
    labels_count = len(comparative_chart_data['labels'])
    while len(comparative_chart_data['department_averages']) < labels_count:
        comparative_chart_data['department_averages'].append(0)
    while len(comparative_chart_data['company_averages']) < labels_count:
        comparative_chart_data['company_averages'].append(0)
    
    context = {
        'target_user': target_user,
        'trend_data': trend_data,
        'benchmark_data': benchmark_data,
        'cycles': cycles,
        'current_score': current_score,
        'score_trend': score_trend,
        'average_growth': average_growth,
        'predicted_next_score': predicted_next_score,
        'consistency_score': consistency_score,
        'six_month_prediction': six_month_prediction,
        'performance_level': performance_level,
        'total_evaluations': total_evaluations,
        'evaluation_frequency': evaluation_frequency,
        'department_rank': department_rank,
        'category_trends': category_trends,
        'top_performing_areas': top_performing_areas,
        'improvement_areas': improvement_areas,
        'trend_chart_data': json.dumps(trend_chart_data),
        'comparative_chart_data': json.dumps(comparative_chart_data),
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
def individual_category_trend(request, category_id):
    """Fərdi kateqoriya trendi detaylı görünüş"""
    
    # User ID parametrini al (GET parametri ilə)
    user_id = request.GET.get('user_id')
    
    # Əgər user_id verilmişsə və icazə varsa, həmin istifadəçinin məlumatını göstər
    if user_id and (request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']):
        target_user = get_object_or_404(Ishchi, id=user_id)
    else:
        target_user = request.user
    
    category = get_object_or_404(SualKateqoriyasi, id=category_id)
    
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
        
        # Kateqoriyalar üzrə ortalama - Optimized to avoid N+1 queries
        category_averages = Cavab.objects.filter(
            qiymetlendirme__in=evaluations
        ).values('sual__kateqoriya__id', 'sual__kateqoriya__ad').annotate(
            avg_score=Avg('xal')
        ).order_by('sual__kateqoriya__id')
        
        for category_data in category_averages:
            category_name = category_data['sual__kateqoriya__ad']
            category_avg = category_data['avg_score']
            
            if category_name and category_avg is not None:
                if category_name not in categories_trend:
                    categories_trend[category_name] = []
                
                categories_trend[category_name].append({
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
    
    # Optimized query to avoid N+1 - get all department trend data in one query
    department_trend_data = Cavab.objects.filter(
        qiymetlendirme__qiymetlendirilen__organization_unit=department,
        qiymetlendirme__dovr__in=cycles,
        qiymetlendirme__status=Qiymetlendirme.Status.TAMAMLANDI
    ).exclude(
        qiymetlendirme__qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
    ).values(
        'qiymetlendirme__dovr__id',
        'qiymetlendirme__dovr__ad',
        'qiymetlendirme__dovr__bashlama_tarixi'
    ).annotate(
        avg_score=Avg('xal'),
        employees_count=Count('qiymetlendirme__qiymetlendirilen', distinct=True)
    ).order_by('qiymetlendirme__dovr__bashlama_tarixi')
    
    department_trend = []
    for data in department_trend_data:
        if data['avg_score'] is not None:
            department_trend.append({
                'cycle_name': data['qiymetlendirme__dovr__ad'],
                'cycle_date': data['qiymetlendirme__dovr__bashlama_tarixi'],
                'average_score': round(data['avg_score'], 2),
                'employees_count': data['employees_count']
            })
    
    return {
        'department_name': department.name,
        'trend_data': department_trend
    }


def get_category_detailed_trend(user, category, cycles):
    """
    Müəyyən kateqoriya üçün detallı trend analizi - Optimized to avoid N+1 queries
    """
    # Get all category trend data in one optimized query
    category_trend_data = Cavab.objects.filter(
        qiymetlendirme__qiymetlendirilen=user,
        qiymetlendirme__dovr__in=cycles,
        qiymetlendirme__status=Qiymetlendirme.Status.TAMAMLANDI,
        sual__kateqoriya=category
    ).exclude(
        qiymetlendirme__qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
    ).values(
        'qiymetlendirme__dovr__id',
        'qiymetlendirme__dovr__ad',
        'qiymetlendirme__dovr__bashlama_tarixi'
    ).annotate(
        avg_score=Avg('xal'),
        answers_count=Count('id'),
        evaluators_count=Count('qiymetlendirme__qiymetlendiren', distinct=True)
    ).order_by('qiymetlendirme__dovr__bashlama_tarixi')
    
    # Get evaluators info separately for each cycle that has data
    cycle_ids_with_data = [item['qiymetlendirme__dovr__id'] for item in category_trend_data]
    evaluators_by_cycle = {}
    
    if cycle_ids_with_data:
        evaluator_data = Qiymetlendirme.objects.filter(
            qiymetlendirilen=user,
            dovr__id__in=cycle_ids_with_data,
            status=Qiymetlendirme.Status.TAMAMLANDI
        ).exclude(
            qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
        ).values(
            'dovr__id',
            'qiymetlendiren__first_name',
            'qiymetlendiren__last_name'
        )
        
        for item in evaluator_data:
            cycle_id = item['dovr__id']
            if cycle_id not in evaluators_by_cycle:
                evaluators_by_cycle[cycle_id] = []
            evaluators_by_cycle[cycle_id].append(
                f"{item['qiymetlendiren__first_name']} {item['qiymetlendiren__last_name']}"
            )
    
    # Build the detailed trend data
    detailed_trend = []
    for data in category_trend_data:
        cycle_id = data['qiymetlendirme__dovr__id']
        if data['avg_score'] is not None:
            detailed_trend.append({
                'cycle_name': data['qiymetlendirme__dovr__ad'],
                'cycle_date': data['qiymetlendirme__dovr__bashlama_tarixi'],
                'average_score': round(data['avg_score'], 2),
                'answers_count': data['answers_count'],
                'evaluators_count': data['evaluators_count'],
                'evaluators': evaluators_by_cycle.get(cycle_id, [])
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