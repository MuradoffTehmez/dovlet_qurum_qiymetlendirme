"""
Quick Feedback (Sürətli Əks Əlaqə) Views
Rəsmi qiymətləndirmə dövrləri arasında sürətli geri bildirim sistemi
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count

from ..models import (
    Ishchi, QuickFeedback, QuickFeedbackCategory, Notification
)
from ..permissions import require_role


@login_required
def quick_feedback_dashboard(request):
    """Quick feedback ana səhifəsi"""
    
    # Son alınan geri bildirimlər
    received_feedbacks = QuickFeedback.objects.filter(
        to_user=request.user,
        is_archived=False
    ).select_related('from_user', 'category').order_by('-created_at')[:10]
    
    # Son verilən geri bildirimlər
    given_feedbacks = QuickFeedback.objects.filter(
        from_user=request.user,
        is_archived=False
    ).select_related('to_user', 'category').order_by('-created_at')[:10]
    
    # Oxunmamış sayı
    unread_count = QuickFeedback.objects.filter(
        to_user=request.user,
        is_read=False,
        is_archived=False
    ).count()
    
    # Statistikalar
    stats = {
        'total_received': QuickFeedback.objects.filter(to_user=request.user).count(),
        'total_given': QuickFeedback.objects.filter(from_user=request.user).count(),
        'unread_count': unread_count,
        'this_week_received': QuickFeedback.objects.filter(
            to_user=request.user,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
    }
    
    # Kateqoriyalar
    categories = QuickFeedbackCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'received_feedbacks': received_feedbacks,
        'given_feedbacks': given_feedbacks,
        'stats': stats,
        'categories': categories,
        'page_title': 'Sürətli Geri Bildirim'
    }
    
    return render(request, 'quick_feedback/dashboard.html', context)


@login_required
def send_quick_feedback(request):
    """Sürətli geri bildirim göndərmə"""
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Form məlumatları
                to_user_id = request.POST.get('to_user')
                category_id = request.POST.get('category')
                feedback_type = request.POST.get('feedback_type', 'POSITIVE')
                priority = request.POST.get('priority', 'MEDIUM')
                title = request.POST.get('title', '').strip()
                message = request.POST.get('message', '').strip()
                is_anonymous = request.POST.get('is_anonymous') == 'on'
                rating = request.POST.get('rating')
                
                # Validasiya
                if not to_user_id or not title or not message:
                    messages.error(request, 'Bütün tələb olunan sahələr doldurulmalıdır.')
                    return redirect('quick_feedback:send')
                
                if to_user_id == str(request.user.id):
                    messages.error(request, 'Özünüzə geri bildirim göndərə bilməzsiniz.')
                    return redirect('quick_feedback:send')
                
                to_user = get_object_or_404(Ishchi, id=to_user_id)
                category = get_object_or_404(QuickFeedbackCategory, id=category_id) if category_id else None
                
                # QuickFeedback yaradırık
                quick_feedback = QuickFeedback.objects.create(
                    from_user=request.user,
                    to_user=to_user,
                    category=category,
                    feedback_type=feedback_type,
                    priority=priority,
                    title=title,
                    message=message,
                    is_anonymous=is_anonymous,
                    rating=int(rating) if rating else None
                )
                
                # Bildiriş göndər
                if not is_anonymous:
                    sender_name = request.user.get_full_name()
                else:
                    sender_name = "Anonim İşçi"
                
                Notification.create_notification(
                    recipient=to_user,
                    title=f"Yeni Sürətli Geri Bildirim: {title}",
                    message=f"{sender_name} sizə yeni geri bildirim göndərdi.",
                    notification_type=Notification.NotificationType.FEEDBACK_RECEIVED,
                    priority=Notification.Priority.MEDIUM,
                    action_url=f"/quick-feedback/{quick_feedback.id}/",
                    action_text="Geri Bildirimi Görüntülə"
                )
                
                messages.success(request, f"{to_user.get_full_name()}-ə geri bildirim uğurla göndərildi.")
                return redirect('quick_feedback:dashboard')
                
        except Exception as e:
            messages.error(request, f"Geri bildirim göndərilirkən xəta: {str(e)}")
            return redirect('quick_feedback:send')
    
    # GET request
    # İstifadəçi siyahısı (özü xaric)
    users = Ishchi.objects.filter(
        is_active=True
    ).exclude(id=request.user.id).order_by('first_name', 'last_name')
    
    # Kateqoriyalar
    categories = QuickFeedbackCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'users': users,
        'categories': categories,
        'page_title': 'Sürətli Geri Bildirim Göndər'
    }
    
    return render(request, 'quick_feedback/send.html', context)


@login_required
def view_quick_feedback(request, feedback_id):
    """Geri bildirimi görüntüləmə"""
    
    feedback = get_object_or_404(
        QuickFeedback,
        id=feedback_id,
        to_user=request.user
    )
    
    # Oxunmuş kimi işarələ
    if not feedback.is_read:
        feedback.mark_as_read()
    
    context = {
        'feedback': feedback,
        'page_title': f'Geri Bildirim: {feedback.title}'
    }
    
    return render(request, 'quick_feedback/view.html', context)


@login_required
def quick_feedback_inbox(request):
    """Gelen geri bildirimlər (gələn qutusu)"""
    
    # Filtr parametrləri
    category_id = request.GET.get('category')
    feedback_type = request.GET.get('type')
    is_read = request.GET.get('is_read')
    
    # Base query
    feedbacks = QuickFeedback.objects.filter(
        to_user=request.user,
        is_archived=False
    ).select_related('from_user', 'category')
    
    # Filtrlər
    if category_id:
        feedbacks = feedbacks.filter(category_id=category_id)
    
    if feedback_type:
        feedbacks = feedbacks.filter(feedback_type=feedback_type)
    
    if is_read == 'read':
        feedbacks = feedbacks.filter(is_read=True)
    elif is_read == 'unread':
        feedbacks = feedbacks.filter(is_read=False)
    
    feedbacks = feedbacks.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(feedbacks, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Kateqoriyalar filtri üçün
    categories = QuickFeedbackCategory.objects.filter(is_active=True).order_by('name')
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': int(category_id) if category_id else None,
        'current_type': feedback_type,
        'current_is_read': is_read,
        'page_title': 'Gələn Geri Bildirimlər'
    }
    
    return render(request, 'quick_feedback/inbox.html', context)


@login_required
def quick_feedback_sent(request):
    """Göndərilən geri bildirimlər"""
    
    # Filtr parametrləri
    category_id = request.GET.get('category')
    feedback_type = request.GET.get('type')
    
    # Base query
    feedbacks = QuickFeedback.objects.filter(
        from_user=request.user,
        is_archived=False
    ).select_related('to_user', 'category')
    
    # Filtrlər
    if category_id:
        feedbacks = feedbacks.filter(category_id=category_id)
    
    if feedback_type:
        feedbacks = feedbacks.filter(feedback_type=feedback_type)
    
    feedbacks = feedbacks.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(feedbacks, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Kateqoriyalar filtri üçün
    categories = QuickFeedbackCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': int(category_id) if category_id else None,
        'current_type': feedback_type,
        'page_title': 'Göndərilən Geri Bildirimlər'
    }
    
    return render(request, 'quick_feedback/sent.html', context)


@login_required
@require_http_methods(["POST"])
def mark_feedback_read(request, feedback_id):
    """Geri bildirimi oxunmuş kimi işarələ (AJAX)"""
    
    feedback = get_object_or_404(
        QuickFeedback,
        id=feedback_id,
        to_user=request.user
    )
    
    feedback.mark_as_read()
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def archive_feedback(request, feedback_id):
    """Geri bildirimi arxivləşdir"""
    
    feedback = get_object_or_404(
        QuickFeedback,
        id=feedback_id
    )
    
    # Yalnız alan və ya göndərən arxivləşdirə bilər
    if feedback.to_user != request.user and feedback.from_user != request.user:
        return JsonResponse({'success': False, 'error': 'İcazəsiz əməliyyat'})
    
    feedback.is_archived = True
    feedback.save()
    
    return JsonResponse({'success': True})


@login_required
def quick_feedback_analytics(request):
    """Geri bildirim analitikası"""
    
    # Son 6 ay məlumatları
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    
    # Alınan geri bildirimlər analitikası
    received_stats = {
        'total': QuickFeedback.objects.filter(to_user=request.user).count(),
        'last_6_months': QuickFeedback.objects.filter(
            to_user=request.user,
            created_at__gte=six_months_ago
        ).count(),
        'by_type': QuickFeedback.objects.filter(
            to_user=request.user
        ).values('feedback_type').annotate(count=Count('id')),
        'by_category': QuickFeedback.objects.filter(
            to_user=request.user,
            category__isnull=False
        ).values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
    }
    
    # Verilən geri bildirimlər analitikası
    given_stats = {
        'total': QuickFeedback.objects.filter(from_user=request.user).count(),
        'last_6_months': QuickFeedback.objects.filter(
            from_user=request.user,
            created_at__gte=six_months_ago
        ).count(),
        'by_type': QuickFeedback.objects.filter(
            from_user=request.user
        ).values('feedback_type').annotate(count=Count('id')),
    }
    
    # Aylıq trend
    monthly_trend = get_monthly_feedback_trend(request.user)
    
    context = {
        'received_stats': received_stats,
        'given_stats': given_stats,
        'monthly_trend': monthly_trend,
        'page_title': 'Geri Bildirim Analitikası'
    }
    
    return render(request, 'quick_feedback/analytics.html', context)


@login_required
def quick_feedback_api(request):
    """Quick feedback üçün AJAX API"""
    
    action = request.GET.get('action')
    
    if action == 'unread_count':
        count = QuickFeedback.objects.filter(
            to_user=request.user,
            is_read=False,
            is_archived=False
        ).count()
        return JsonResponse({'unread_count': count})
    
    elif action == 'recent_feedbacks':
        feedbacks = QuickFeedback.objects.filter(
            to_user=request.user,
            is_archived=False
        ).select_related('from_user', 'category').order_by('-created_at')[:5]
        
        data = []
        for feedback in feedbacks:
            data.append({
                'id': feedback.id,
                'title': feedback.title,
                'from_user': feedback.get_display_sender(),
                'created_at': feedback.created_at.strftime('%d.%m.%Y %H:%M'),
                'is_read': feedback.is_read,
                'feedback_type': feedback.get_feedback_type_display(),
                'color_class': feedback.get_color_class()
            })
        
        return JsonResponse({'feedbacks': data})
    
    elif action == 'search_users':
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'users': []})
        
        users = Ishchi.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query),
            is_active=True
        ).exclude(id=request.user.id)[:10]
        
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'name': user.get_full_name(),
                'department': user.organization_unit.name if user.organization_unit else ''
            })
        
        return JsonResponse({'users': data})
    
    return JsonResponse({'error': 'Bilinməyən əməliyyat'})


def get_monthly_feedback_trend(user):
    """Aylıq geri bildirim trendini qaytarır"""
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    import calendar
    
    # Son 6 ay
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    
    # Alınan geri bildirimlər aylıq
    received_monthly = QuickFeedback.objects.filter(
        to_user=user,
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Verilən geri bildirimlər aylıq
    given_monthly = QuickFeedback.objects.filter(
        from_user=user,
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Formatla
    trend_data = {
        'labels': [],
        'received': [],
        'given': []
    }
    
    # Son 6 ayı yarat
    current_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    for i in range(6):
        month_date = current_date - timezone.timedelta(days=i*30)
        month_name = calendar.month_name[month_date.month][:3]
        
        trend_data['labels'].insert(0, f"{month_name} {month_date.year}")
        
        # Həmin ay üçün məlumatları tap
        received_count = 0
        given_count = 0
        
        for item in received_monthly:
            if item['month'].month == month_date.month and item['month'].year == month_date.year:
                received_count = item['count']
                break
        
        for item in given_monthly:
            if item['month'].month == month_date.month and item['month'].year == month_date.year:
                given_count = item['count']
                break
        
        trend_data['received'].insert(0, received_count)
        trend_data['given'].insert(0, given_count)
    
    return trend_data