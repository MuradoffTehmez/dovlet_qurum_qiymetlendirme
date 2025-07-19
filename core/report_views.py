# core/report_views.py
"""
Hesabat Mərkəzi Views
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
import json

from .reports import ReportManager, EmployeePerformanceReport, ReportGenerator
from .permissions import permission_required, has_permission
from .tasks import generate_report_task
from .notifications import NotificationManager


@login_required
@permission_required('view_organization_reports')
def report_center(request):
    """Hesabat mərkəzi ana səhifəsi"""
    available_reports = ReportManager.get_available_reports()
    filter_options = ReportManager.get_filter_options()
    
    # İstifadəçinin icazələrinə görə hesabatları filtrləmək
    user_reports = {}
    for report_id, report_info in available_reports.items():
        # Burada icazə yoxlaması əlavə edə bilərik
        user_reports[report_id] = report_info
    
    # Son generasiya edilmiş hesabatlar (cache-dən)
    from django.core.cache import cache
    recent_reports = cache.get(f'recent_reports_{request.user.id}', [])
    
    context = {
        'available_reports': user_reports,
        'filter_options': filter_options,
        'recent_reports': recent_reports,
        'title': 'Hesabat Mərkəzi'
    }
    
    return render(request, 'core/reports/report_center.html', context)


@login_required
@permission_required('view_organization_reports')
def generate_report(request, report_type):
    """Hesabat generasiya səhifəsi"""
    available_reports = ReportManager.get_available_reports()
    
    if report_type not in available_reports:
        messages.error(request, 'Naməlum hesabat növü')
        return redirect('report_center')
    
    report_info = available_reports[report_type]
    filter_options = ReportManager.get_filter_options()
    
    if request.method == 'POST':
        # Filtrləri hazırla
        filters = {}
        
        # Tarix filtri
        date_range = request.POST.get('date_range')
        if date_range == 'custom':
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')
            if date_from:
                filters['date_from'] = datetime.strptime(date_from, '%Y-%m-%d').date()
            if date_to:
                filters['date_to'] = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            # Predefined date ranges
            end_date = timezone.now().date()
            if date_range == 'last_7_days':
                start_date = end_date - timedelta(days=7)
            elif date_range == 'last_30_days':
                start_date = end_date - timedelta(days=30)
            elif date_range == 'last_3_months':
                start_date = end_date - timedelta(days=90)
            elif date_range == 'last_6_months':
                start_date = end_date - timedelta(days=180)
            elif date_range == 'last_year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = None
            
            if start_date:
                filters['date_from'] = start_date
                filters['date_to'] = end_date
        
        # Digər filtrlər
        if request.POST.get('department'):
            filters['department'] = request.POST.get('department')
            
        if request.POST.get('role'):
            filters['role'] = request.POST.get('role')
            
        if request.POST.get('evaluation_period'):
            filters['evaluation_period'] = request.POST.get('evaluation_period')
        
        # Format
        output_format = request.POST.get('format', 'pdf')
        
        # Hesabatı generasiya et
        try:
            if report_type == 'employee_performance':
                report = EmployeePerformanceReport(filters)
                report_data = report.get_data()
                report_data['title'] = 'İşçi Performans Hesabatı'
                
                if output_format == 'pdf':
                    buffer = ReportGenerator.generate_pdf(report_data, report_type)
                    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="performans_hesabati_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
                    
                elif output_format == 'excel':
                    buffer = ReportGenerator.generate_excel(report_data, report_type)
                    response = HttpResponse(
                        buffer.getvalue(),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    response['Content-Disposition'] = f'attachment; filename="performans_hesabati_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
                    
                elif output_format == 'csv':
                    buffer = ReportGenerator.generate_csv(report_data, report_type)
                    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="performans_hesabati_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
                
                # Son hesabatları cache-ə əlavə et
                from django.core.cache import cache
                recent_reports = cache.get(f'recent_reports_{request.user.id}', [])
                recent_reports.insert(0, {
                    'type': report_type,
                    'title': report_data['title'],
                    'generated_at': timezone.now(),
                    'format': output_format,
                    'filters': filters
                })
                recent_reports = recent_reports[:10]  # Son 10 hesabat
                cache.set(f'recent_reports_{request.user.id}', recent_reports, 3600)
                
                return response
                
        except Exception as e:
            messages.error(request, f'Hesabat generasiya edilərkən xəta baş verdi: {str(e)}')
    
    context = {
        'report_type': report_type,
        'report_info': report_info,
        'filter_options': filter_options,
        'title': f'Hesabat Generasiya - {report_info["name"]}'
    }
    
    return render(request, 'core/reports/generate_report.html', context)


@login_required
@permission_required('view_organization_reports')
def report_preview(request, report_type):
    """Hesabat preview (AJAX)"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    # Filtrləri al
    filters = {}
    if request.GET.get('date_from'):
        filters['date_from'] = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d').date()
    if request.GET.get('date_to'):
        filters['date_to'] = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d').date()
    if request.GET.get('department'):
        filters['department'] = request.GET.get('department')
    if request.GET.get('role'):
        filters['role'] = request.GET.get('role')
    
    try:
        if report_type == 'employee_performance':
            report = EmployeePerformanceReport(filters)
            data = report.get_data()
            
            # Preview üçün məlumatları hazırla
            preview_data = {
                'stats': data['stats'],
                'sample_data': list(data['detailed_data'][:10]),  # İlk 10 qeyd
                'total_records': len(data['detailed_data']),
                'filters_applied': data['filters_applied']
            }
            
            return JsonResponse({
                'success': True,
                'preview_data': preview_data
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required('generate_reports')
def schedule_report(request):
    """Planlanmış hesabat yaratma"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        schedule_type = request.POST.get('schedule_type')  # daily, weekly, monthly
        recipients = request.POST.getlist('recipients')
        
        # Filtrləri hazırla
        filters = {}
        if request.POST.get('department'):
            filters['department'] = request.POST.get('department')
        if request.POST.get('role'):
            filters['role'] = request.POST.get('role')
        
        # Celery task-ı planla
        if schedule_type == 'weekly':
            # Həftəlik hesabat planla
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
            
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=9,
                day_of_week=1,  # Bazar ertəsi
                day_of_month='*',
                month_of_year='*'
            )
            
            task_name = f"weekly_report_{report_type}_{request.user.id}"
            
            PeriodicTask.objects.update_or_create(
                name=task_name,
                defaults={
                    'crontab': schedule,
                    'task': 'core.tasks.generate_scheduled_report',
                    'kwargs': json.dumps({
                        'report_type': report_type,
                        'user_id': request.user.id,
                        'filters': filters,
                        'recipients': recipients
                    }),
                    'enabled': True
                }
            )
            
            messages.success(request, 'Həftəlik hesabat uğurla planlandı')
        
        return redirect('report_center')
    
    # GET request üçün
    filter_options = ReportManager.get_filter_options()
    available_reports = ReportManager.get_available_reports()
    
    # Potensial alıcılar
    from django.contrib.auth.models import Group
    recipients = []
    
    # Rəhbərlər
    managers = Group.objects.filter(name__in=['HR Manager', 'Department Manager']).first()
    if managers:
        recipients.extend(managers.user_set.all())
    
    context = {
        'available_reports': available_reports,
        'filter_options': filter_options,
        'potential_recipients': recipients,
        'title': 'Planlanmış Hesabat Yaradın'
    }
    
    return render(request, 'core/reports/schedule_report.html', context)


@login_required
@permission_required('view_organization_reports')
def report_analytics(request):
    """Hesabat analitikası dashboard-u"""
    from django.db.models import Count
    from datetime import timedelta
    
    # Son 30 günün hesabat statistikası
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Hesabat növləri üzrə dağılım (cache-dən)
    from django.core.cache import cache
    
    report_stats = []
    total_reports = 0
    
    # Bütün istifadəçilərin cache-dəki hesabatlarını yığ
    # (Real production-da database-də saxlamaq daha yaxşıdır)
    
    # Performans trendləri
    performance_trend = []
    for i in range(7):
        date = end_date - timedelta(days=i)
        # Simulasiya məlumatı
        performance_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'avg_score': 75 + (i * 2),  # Simulasiya
            'evaluations_count': 10 + i
        })
    
    context = {
        'report_stats': report_stats,
        'total_reports': total_reports,
        'performance_trend': performance_trend,
        'title': 'Hesabat Analitikası'
    }
    
    return render(request, 'core/reports/report_analytics.html', context)


@login_required
def download_sample_report(request, report_type):
    """Nümunə hesabat endirmə"""
    available_reports = ReportManager.get_available_reports()
    
    if report_type not in available_reports:
        messages.error(request, 'Naməlum hesabat növü')
        return redirect('report_center')
    
    # Nümunə məlumatlarla hesabat generasiya et
    if report_type == 'employee_performance':
        # Son 30 günün məlumatı ilə nümunə
        filters = {
            'date_from': (timezone.now() - timedelta(days=30)).date(),
            'date_to': timezone.now().date()
        }
        
        report = EmployeePerformanceReport(filters)
        report_data = report.get_data()
        report_data['title'] = 'Nümunə İşçi Performans Hesabatı'
        
        buffer = ReportGenerator.generate_pdf(report_data, report_type)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="numune_performans_hesabati.pdf"'
        
        return response
    
    messages.error(request, 'Bu hesabat növü üçün nümunə mövcud deyil')
    return redirect('report_center')


@login_required 
@permission_required('manage_system_settings')
def report_settings(request):
    """Hesabat sistem tənzimləmələri"""
    if request.method == 'POST':
        # Tənzimləmələri yadda saxla
        settings_data = {
            'auto_generate_weekly': request.POST.get('auto_generate_weekly') == 'on',
            'default_format': request.POST.get('default_format', 'pdf'),
            'cache_duration': int(request.POST.get('cache_duration', 300)),
            'max_records_preview': int(request.POST.get('max_records_preview', 10))
        }
        
        # Cache-də saxla və ya database model yarat
        from django.core.cache import cache
        cache.set('report_settings', settings_data, 86400)  # 24 saat
        
        messages.success(request, 'Hesabat tənzimləmələri yadda saxlanıldı')
        return redirect('report_settings')
    
    # Mövcud tənzimləmələri yüklə
    from django.core.cache import cache
    current_settings = cache.get('report_settings', {
        'auto_generate_weekly': False,
        'default_format': 'pdf',
        'cache_duration': 300,
        'max_records_preview': 10
    })
    
    context = {
        'current_settings': current_settings,
        'title': 'Hesabat Tənzimləmələri'
    }
    
    return render(request, 'core/reports/report_settings.html', context)