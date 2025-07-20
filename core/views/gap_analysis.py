"""
Gap Analysis (Fərq Təhlili) Views
İşçinin özünə verdiyi bal ilə başqalarının verdiyi ballar arasındakı fərqi analiz edir
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import json

from ..models import (
    Ishchi, Qiymetlendirme, Cavab, QiymetlendirmeDovru, 
    SualKateqoriyasi, Sual
)
from ..permissions import require_role


@login_required
def gap_analysis_dashboard(request):
    """Gap Analysis ana səhifəsi"""
    
    # Son aktiv dövrü tap
    active_cycle = QiymetlendirmeDovru.objects.filter(
        aktivdir=True
    ).order_by('-bashlama_tarixi').first()
    
    # İstifadəçinin gap analysis məlumatları
    user_gap_data = None
    comparison_chart_data = {'categories': [], 'self_scores': [], 'others_scores': []}
    historical_chart_data = {'labels': [], 'gaps': []}
    overall_gap = 0
    overall_gap_direction = 'neutral'
    self_average = 0
    others_average = 0
    evaluators_count = 0
    significant_gaps_count = 0
    category_gaps = []
    overestimated_areas = []
    underestimated_areas = []
    historical_data = False
    
    if active_cycle:
        user_gap_data = get_user_gap_analysis(request.user, active_cycle)
        
        if user_gap_data and user_gap_data['has_self_review']:
            # Overall metrics
            overall_gap = user_gap_data['overall_gap']
            if overall_gap > 0.5:
                overall_gap_direction = 'positive'
            elif overall_gap < -0.5:
                overall_gap_direction = 'negative'
            else:
                overall_gap_direction = 'neutral'
            
            # Calculate averages
            if user_gap_data['categories']:
                self_scores = [cat['self_score'] for cat in user_gap_data['categories']]
                others_scores = [cat['others_score'] for cat in user_gap_data['categories']]
                self_average = sum(self_scores) / len(self_scores)
                others_average = sum(others_scores) / len(others_scores)
                
                # Count significant gaps (>1.5)
                significant_gaps_count = len([cat for cat in user_gap_data['categories'] if abs(cat['gap']) > 1.5])
                
                # Prepare chart data
                for cat in user_gap_data['categories']:
                    comparison_chart_data['categories'].append(cat['category'].ad)
                    comparison_chart_data['self_scores'].append(cat['self_score'])
                    comparison_chart_data['others_scores'].append(cat['others_score'])
                    
                    # Category gaps for summary
                    direction = 'positive' if cat['gap'] > 0.5 else ('negative' if cat['gap'] < -0.5 else 'neutral')
                    category_gaps.append({
                        'category': cat['category'].ad,
                        'gap': cat['gap'],
                        'self_score': cat['self_score'],
                        'others_score': cat['others_score'],
                        'direction': direction
                    })
                    
                    # Overestimated and underestimated areas
                    if cat['gap'] > 1.5:
                        overestimated_areas.append({
                            'category': cat['category'].ad,
                            'self_score': cat['self_score'],
                            'others_score': cat['others_score'],
                            'gap': cat['gap'],
                            'description': f"Bu sahədə özünüzü {cat['gap']:.1f} bal yüksək qiymətləndirirsiniz"
                        })
                    elif cat['gap'] < -1.5:
                        underestimated_areas.append({
                            'category': cat['category'].ad,
                            'self_score': cat['self_score'],
                            'others_score': cat['others_score'],
                            'gap': cat['gap'],
                            'description': f"Bu sahədə özünüzü {abs(cat['gap']):.1f} bal aşağı qiymətləndirirsiniz"
                        })
                
                # Get evaluators count
                if active_cycle:
                    evaluators_count = Qiymetlendirme.objects.filter(
                        qiymetlendirilen=request.user,
                        dovr=active_cycle,
                        status=Qiymetlendirme.Status.TAMAMLANDI
                    ).exclude(
                        qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
                    ).count()
        
        # Historical data for trend analysis
        historical_cycles = QiymetlendirmeDovru.objects.filter(
            bashlama_tarixi__lt=active_cycle.bashlama_tarixi
        ).order_by('-bashlama_tarixi')[:5]
        
        if historical_cycles.exists():
            historical_data = True
            for cycle in reversed(historical_cycles):
                cycle_gap_data = get_user_gap_analysis(request.user, cycle)
                if cycle_gap_data and cycle_gap_data['has_self_review']:
                    historical_chart_data['labels'].append(cycle.ad)
                    historical_chart_data['gaps'].append(cycle_gap_data['overall_gap'])
    
    # Bütün dövrləri göstər
    all_cycles = QiymetlendirmeDovru.objects.filter(
        bashlama_tarixi__lte=timezone.now().date()
    ).order_by('-bashlama_tarixi')[:5]
    
    context = {
        'active_cycle': active_cycle,
        'user_gap_data': user_gap_data,
        'all_cycles': all_cycles,
        'overall_gap': overall_gap,
        'overall_gap_direction': overall_gap_direction,
        'self_average': self_average,
        'others_average': others_average,
        'evaluators_count': evaluators_count,
        'significant_gaps_count': significant_gaps_count,
        'category_gaps': category_gaps,
        'overestimated_areas': overestimated_areas,
        'underestimated_areas': underestimated_areas,
        'comparison_chart_data': json.dumps(comparison_chart_data),
        'historical_data': historical_data,
        'historical_chart_data': json.dumps(historical_chart_data),
        'page_title': 'Fərq Təhlili (Gap Analysis)'
    }
    
    return render(request, 'gap_analysis/dashboard.html', context)


@login_required
def gap_analysis_detail(request, cycle_id):
    """Müəyyən dövr üçün detallı gap analysis"""
    
    cycle = get_object_or_404(QiymetlendirmeDovru, id=cycle_id)
    user_id = request.GET.get('user_id')
    
    # Əgər user_id verilmişsə və icazə varsa, həmin istifadəçinin məlumatını göstər
    if user_id and (request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']):
        target_user = get_object_or_404(Ishchi, id=user_id)
    else:
        target_user = request.user
    
    # Gap analysis məlumatlarını topla
    gap_data = get_user_gap_analysis(target_user, cycle)
    
    # Həmçinin bu istifadəçi ilə müqayisə üçün ortalama məlumatlar
    department_avg = None
    if target_user.organization_unit:
        department_avg = get_department_average(target_user.organization_unit, cycle)
    
    company_avg = get_company_average(cycle)
    
    context = {
        'cycle': cycle,
        'target_user': target_user,
        'gap_data': gap_data,
        'department_avg': department_avg,
        'company_avg': company_avg,
        'page_title': f'Fərq Təhlili: {target_user.get_full_name()} - {cycle.ad}',
        'show_user_selector': request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']
    }
    
    return render(request, 'gap_analysis/detail.html', context)


@login_required
def gap_analysis_api(request, cycle_id):
    """Gap Analysis üçün AJAX API"""
    
    cycle = get_object_or_404(QiymetlendirmeDovru, id=cycle_id)
    user_id = request.GET.get('user_id')
    
    if user_id and (request.user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']):
        target_user = get_object_or_404(Ishchi, id=user_id)
    else:
        target_user = request.user
    
    # Cache key
    cache_key = f"gap_analysis_{target_user.id}_{cycle.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data)
    
    gap_data = get_user_gap_analysis(target_user, cycle)
    
    # API üçün format
    api_data = {
        'user_name': target_user.get_full_name(),
        'cycle_name': cycle.ad,
        'has_self_review': gap_data['has_self_review'],
        'categories': []
    }
    
    for category_data in gap_data['categories']:
        api_data['categories'].append({
            'name': category_data['category'].ad,
            'self_score': category_data['self_score'],
            'others_score': category_data['others_score'],
            'gap': category_data['gap'],
            'gap_percentage': category_data['gap_percentage'],
            'recommendations': category_data['recommendations']
        })
    
    # 5 dəqiqə cache
    cache.set(cache_key, api_data, 300)
    
    return JsonResponse(api_data)


@login_required
@require_role(['ADMIN', 'SUPERADMIN', 'REHBER'])
def team_gap_analysis(request):
    """Komanda/şöbə üçün gap analysis"""
    
    department_id = request.GET.get('department_id')
    cycle_id = request.GET.get('cycle_id')
    
    if not department_id or not cycle_id:
        return JsonResponse({'error': 'Department və cycle seçilməlidir'})
    
    cycle = get_object_or_404(QiymetlendirmeDovru, id=cycle_id)
    
    # Şöbədəki işçilərin siyahısı
    team_members = Ishchi.objects.filter(
        organization_unit_id=department_id
    )
    
    team_gap_data = []
    
    for member in team_members:
        member_data = get_user_gap_analysis(member, cycle)
        
        if member_data['has_self_review']:
            team_gap_data.append({
                'user_id': member.id,
                'user_name': member.get_full_name(),
                'overall_gap': member_data['overall_gap'],
                'categories_count': len(member_data['categories']),
                'highest_gap_category': max(
                    member_data['categories'], 
                    key=lambda x: abs(x['gap'])
                )['category'].ad if member_data['categories'] else None
            })
    
    context = {
        'cycle': cycle,
        'team_gap_data': team_gap_data,
        'team_members_count': team_members.count(),
        'page_title': f'Komanda Fərq Təhlili - {cycle.ad}'
    }
    
    return render(request, 'gap_analysis/team.html', context)


def get_user_gap_analysis(user, cycle):
    """
    İstifadəçinin gap analysis məlumatlarını hesablayır
    """
    # Self-review qiymətləndirməsi
    self_review = Qiymetlendirme.objects.filter(
        qiymetlendirilen=user,
        qiymetlendiren=user,
        dovr=cycle,
        qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW,
        status=Qiymetlendirme.Status.TAMAMLANDI
    ).first()
    
    if not self_review:
        return {
            'has_self_review': False,
            'categories': [],
            'overall_gap': 0
        }
    
    # Başqalarının qiymətləndirmələri
    others_reviews = Qiymetlendirme.objects.filter(
        qiymetlendirilen=user,
        dovr=cycle,
        status=Qiymetlendirme.Status.TAMAMLANDI
    ).exclude(
        qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
    )
    
    # Kateqoriyalar üzrə analiz
    categories_data = []
    total_gap = 0
    
    for category in SualKateqoriyasi.objects.all():
        # Self-review cavabları
        self_answers = Cavab.objects.filter(
            qiymetlendirme=self_review,
            sual__kateqoriya=category
        )
        
        if not self_answers.exists():
            continue
        
        self_avg = self_answers.aggregate(Avg('xal'))['xal__avg']
        
        # Başqalarının cavabları
        others_answers = Cavab.objects.filter(
            qiymetlendirme__in=others_reviews,
            sual__kateqoriya=category
        )
        
        if not others_answers.exists():
            continue
        
        others_avg = others_answers.aggregate(Avg('xal'))['xal__avg']
        
        # Gap hesabla
        gap = self_avg - others_avg
        gap_percentage = (gap / 10) * 100  # 10 maksimum bal
        
        # Tövsiyələr
        recommendations = generate_gap_recommendations(category, gap)
        
        categories_data.append({
            'category': category,
            'self_score': round(self_avg, 2),
            'others_score': round(others_avg, 2),
            'gap': round(gap, 2),
            'gap_percentage': round(gap_percentage, 1),
            'recommendations': recommendations
        })
        
        total_gap += abs(gap)
    
    overall_gap = total_gap / len(categories_data) if categories_data else 0
    
    return {
        'has_self_review': True,
        'categories': categories_data,
        'overall_gap': round(overall_gap, 2)
    }


def get_department_average(department, cycle):
    """Şöbənin ortalama performansını hesablayır"""
    
    # Şöbədəki bütün tamamlanmış qiymətləndirmələr
    dept_evaluations = Qiymetlendirme.objects.filter(
        qiymetlendirilen__organization_unit=department,
        dovr=cycle,
        status=Qiymetlendirme.Status.TAMAMLANDI
    ).exclude(
        qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
    )
    
    if not dept_evaluations.exists():
        return None
    
    # Kateqoriyalar üzrə ortalama
    dept_categories = []
    
    for category in SualKateqoriyasi.objects.all():
        answers = Cavab.objects.filter(
            qiymetlendirme__in=dept_evaluations,
            sual__kateqoriya=category
        )
        
        if answers.exists():
            avg_score = answers.aggregate(Avg('xal'))['xal__avg']
            dept_categories.append({
                'category': category,
                'average_score': round(avg_score, 2)
            })
    
    return dept_categories


def get_company_average(cycle):
    """Şirkətin ümumi ortalamasını hesablayır"""
    
    # Bütün tamamlanmış qiymətləndirmələr
    all_evaluations = Qiymetlendirme.objects.filter(
        dovr=cycle,
        status=Qiymetlendirme.Status.TAMAMLANDI
    ).exclude(
        qiymetlendirme_novu=Qiymetlendirme.QiymetlendirmeNovu.SELF_REVIEW
    )
    
    if not all_evaluations.exists():
        return None
    
    # Kateqoriyalar üzrə ortalama
    company_categories = []
    
    for category in SualKateqoriyasi.objects.all():
        answers = Cavab.objects.filter(
            qiymetlendirme__in=all_evaluations,
            sual__kateqoriya=category
        )
        
        if answers.exists():
            avg_score = answers.aggregate(Avg('xal'))['xal__avg']
            company_categories.append({
                'category': category,
                'average_score': round(avg_score, 2)
            })
    
    return company_categories


def generate_gap_recommendations(category, gap):
    """
    Gap əsasında tövsiyələr generasiya edir
    """
    recommendations = []
    
    if abs(gap) < 0.5:
        recommendations.append("Özünü qiymətləndirmə dəqiqdir, yaxşı öz-dərketmə")
    elif gap > 1.5:  # Özünü yüksək qiymətləndirir
        recommendations.append(f"{category.ad} sahəsində daha təvazökar yanaşma")
        recommendations.append("Başqalarından daha çox geri bildirim istəyin")
        recommendations.append("Bu sahədə əlavə təlim və inkişaf lazım ola bilər")
    elif gap < -1.5:  # Özünü aşağı qiymətləndirir
        recommendations.append(f"{category.ad} sahəsində özünə inamını artır")
        recommendations.append("Uğurlarınızı daha çox qeyd edin və paylaşın")
        recommendations.append("Bu sahədəki güclü tərəflərinizi daha yaxşı tanıyın")
    else:
        recommendations.append("Kiçik fərq, ümumiyyətlə yaxşı öz-dərketmə")
    
    return recommendations