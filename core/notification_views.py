# core/notification_views.py
"""
Bildiriş sistemi üçün view-lər
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Notification, Ishchi
from .notifications import NotificationManager
from .permissions import permission_required


@login_required
def notification_center(request):
    """Bildiriş mərkəzi ana səhifəsi"""
    # Query parametrləri
    filter_type = request.GET.get('type', 'all')
    filter_read = request.GET.get('read', 'all')
    search_query = request.GET.get('search', '')
    
    # Bildirişləri filtrləmə
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_archived=False
    ).select_related('sender').order_by('-created_at')
    
    # Növə görə filtr
    if filter_type != 'all':
        notifications = notifications.filter(notification_type=filter_type)
    
    # Oxunub/oxunmamışa görə filtr  
    if filter_read == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_read == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Axtarış
    if search_query:
        notifications = notifications.filter(
            Q(title__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Səhifələmə
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistika
    stats = {
        'total': Notification.objects.filter(recipient=request.user, is_archived=False).count(),
        'unread': Notification.objects.filter(recipient=request.user, is_read=False, is_archived=False).count(),
        'today': Notification.objects.filter(
            recipient=request.user, 
            is_archived=False,
            created_at__date=timezone.now().date()
        ).count()
    }
    
    # Bildiriş növləri dropdown üçün
    notification_types = Notification.NotificationType.choices
    
    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'stats': stats,
        'notification_types': notification_types,
        'current_filter_type': filter_type,
        'current_filter_read': filter_read,
        'search_query': search_query,
        'title': 'Bildiriş Mərkəzi'
    }
    
    return render(request, 'core/notifications/notification_center.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Bildirişi oxunmuş kimi işarələ"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Bildiriş oxunmuş kimi işarələndi',
            'unread_count': Notification.get_unread_count(request.user)
        })
    
    return redirect('notification_center')


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Bütün bildirişləri oxunmuş kimi işarələ"""
    updated_count = NotificationManager.mark_all_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{updated_count} bildiriş oxunmuş kimi işarələndi',
            'unread_count': 0
        })
    
    return redirect('notification_center')


@login_required
@require_http_methods(["POST"])
def archive_notification(request, notification_id):
    """Bildirişi arxivləşdir"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    notification.is_archived = True
    notification.save(update_fields=['is_archived'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Bildiriş arxivləşdirildi'
        })
    
    return redirect('notification_center')


@login_required
def notification_detail(request, notification_id):
    """Bildiriş detalları"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    # Avtomatik oxunmuş işarələ
    if not notification.is_read:
        notification.mark_as_read()
    
    context = {
        'notification': notification,
        'title': notification.title
    }
    
    return render(request, 'core/notifications/notification_detail.html', context)


@login_required
def notification_api(request):
    """
    AJAX üçün bildiriş API-si
    Real-time notification polling üçün
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    action = request.GET.get('action', 'get_recent')
    
    if action == 'get_recent':
        # Son 10 bildiriş
        notifications = NotificationManager.get_user_notifications(
            user=request.user, 
            limit=10, 
            unread_only=False
        )
        
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
                'type': notification.notification_type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
                'icon': notification.get_icon(),
                'color_class': notification.get_color_class(),
                'action_url': notification.action_url,
                'action_text': notification.action_text,
            })
        
        return JsonResponse({
            'notifications': data,
            'unread_count': Notification.get_unread_count(request.user),
            'total_count': len(notifications)
        })
    
    elif action == 'get_unread_count':
        return JsonResponse({
            'unread_count': Notification.get_unread_count(request.user)
        })
    
    else:
        return JsonResponse({'error': 'Naməlum əməliyyat'}, status=400)


@login_required
def notification_preferences(request):
    """Bildiriş tənzimləmələri"""
    if request.method == 'POST':
        # İstifadəçi tənzimləmələrini yadda saxla
        # Bu hissəni UserPreferences modeli ilə genişləndirə bilərik
        
        email_notifications = request.POST.get('email_notifications') == 'on'
        browser_notifications = request.POST.get('browser_notifications') == 'on'
        deadline_reminders = request.POST.get('deadline_reminders') == 'on'
        evaluation_updates = request.POST.get('evaluation_updates') == 'on'
        
        # User profile-də saxla və ya ayrıca model yarat
        # request.user.profile.email_notifications = email_notifications
        # request.user.profile.save()
        
        return redirect('notification_preferences')
    
    context = {
        'title': 'Bildiriş Tənzimləmələri'
    }
    
    return render(request, 'core/notifications/notification_preferences.html', context)


# === ADMIN FUNKSİYALARI ===

@permission_required('manage_system_settings')
def admin_notification_dashboard(request):
    """Admin bildiriş dashboard-u"""
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    # Son 30 günün statistikası
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Günlük bildiriş sayları
    from django.db.models import DateTimeField
    from django.db.models.functions import TruncDate
    
    daily_stats = Notification.objects.filter(
        created_at__range=[start_date, end_date]
    ).annotate(
        day=TruncDate('created_at')
    ).values('day').annotate(
        count=Count('id'),
        unread=Count('id', filter=Q(is_read=False))
    ).order_by('day')
    
    # Növə görə dağılım
    type_stats = Notification.objects.filter(
        created_at__range=[start_date, end_date]
    ).values('notification_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Ümumi statistika
    total_stats = {
        'total_notifications': Notification.objects.count(),
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
        'archived_notifications': Notification.objects.filter(is_archived=True).count(),
        'this_month': Notification.objects.filter(created_at__month=timezone.now().month).count(),
    }
    
    context = {
        'daily_stats': list(daily_stats),
        'type_stats': list(type_stats),
        'total_stats': total_stats,
        'title': 'Bildiriş İdarəetmə Dashboard-u'
    }
    
    return render(request, 'core/notifications/admin_dashboard.html', context)


@permission_required('manage_system_settings')
def send_bulk_notification(request):
    """Toplu bildiriş göndərmə"""
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type', 'INFO')
        priority = request.POST.get('priority', 'MEDIUM')
        target_audience = request.POST.get('target_audience', 'all')
        
        # Hədəf auditoriyasını təyin et
        if target_audience == 'all':
            recipients = Ishchi.objects.filter(is_active=True)
        elif target_audience == 'managers':
            recipients = Ishchi.objects.filter(rol__in=['REHBER', 'ADMIN', 'SUPERADMIN'])
        elif target_audience == 'employees':
            recipients = Ishchi.objects.filter(rol='ISHCHI')
        else:
            recipients = Ishchi.objects.filter(is_active=True)
        
        # Bildirişləri göndər
        notifications = NotificationManager.bulk_notify(
            recipients=recipients,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            sender=request.user
        ) or []
        
        return JsonResponse({
            'success': True,
            'message': f'{len(notifications)} bildiriş göndərildi',
            'count': len(notifications)
        })
    
    context = {
        'notification_types': Notification.NotificationType.choices,
        'priorities': Notification.Priority.choices,
        'title': 'Toplu Bildiriş Göndər'
    }
    
    return render(request, 'core/notifications/bulk_notification.html', context)