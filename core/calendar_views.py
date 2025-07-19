# core/calendar_views.py
"""
Təqvim sistemi view-ləri
FullCalendar.js ilə qiymətləndirmə dövrləri, son tarixlər və hadisələrin göstərilməsi
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models import (
    QiymetlendirmeDovru, Hedef, Qiymetlendirme, 
    InkishafPlani, Notification, CalendarEvent
)
from .permissions import permission_required


@login_required
def calendar_view(request):
    """Təqvim ana səhifəsi"""
    context = {
        'title': 'Təqvim və Hadisələr'
    }
    return render(request, 'core/calendar/calendar_view.html', context)


@login_required
def calendar_events_api(request):
    """Təqvim hadisələri API (FullCalendar üçün)"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    # Tarix aralığını al
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if start_date and end_date:
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
        except ValueError:
            return JsonResponse({'error': 'Yanlış tarix formatı'}, status=400)
    else:
        # Default: bu ayın tarixləri
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    events = []
    
    # 1. Qiymətləndirmə dövrləri
    evaluation_periods = QiymetlendirmeDovru.objects.filter(
        Q(bashlama_tarixi__lte=end_date) & Q(bitme_tarixi__gte=start_date)
    )
    
    for period in evaluation_periods:
        events.append({
            'id': f'period_{period.id}',
            'title': f'🎯 {period.ad}',
            'start': period.bashlama_tarixi.isoformat(),
            'end': (period.bitme_tarixi + timedelta(days=1)).isoformat(),  # FullCalendar üçün +1 gün
            'backgroundColor': '#667eea',
            'borderColor': '#667eea',
            'textColor': 'white',
            'extendedProps': {
                'type': 'evaluation_period',
                'description': f'Qiymətləndirmə dövrü: {period.bashlama_tarixi.strftime("%d.%m.%Y")} - {period.bitme_tarixi.strftime("%d.%m.%Y")}',
                'url': f'/admin/core/qiymetlendirmedovru/{period.id}/change/'
            }
        })
    
    # 2. İstifadəçiyə aid hədəflərin son tarixləri
    user_goals = Hedef.objects.filter(
        plan__ishchi=request.user,
        son_tarix__range=[start_date, end_date],
        status__in=['BASHLANMAYIB', 'ICRADA']
    ).select_related('plan')
    
    for goal in user_goals:
        # Rəng təyin et - son tarixə görə
        days_left = (goal.son_tarix - timezone.now().date()).days
        if days_left < 0:
            color = '#dc3545'  # Qırmızı - keçmiş
        elif days_left <= 3:
            color = '#fd7e14'  # Narıncı - təcili
        elif days_left <= 7:
            color = '#ffc107'  # Sarı - yaxın
        else:
            color = '#28a745'  # Yaşıl - vaxt var
        
        events.append({
            'id': f'goal_{goal.id}',
            'title': f'🎯 {goal.tesvir[:30]}...' if len(goal.tesvir) > 30 else f'🎯 {goal.tesvir}',
            'start': goal.son_tarix.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'textColor': 'white',
            'extendedProps': {
                'type': 'goal_deadline',
                'description': f'Hədəf son tarixi: {goal.tesvir}',
                'status': goal.get_status_display(),
                'plan_title': goal.plan.ishchi.get_full_name(),
                'days_left': days_left
            }
        })
    
    # 3. Rəhbər üçün komanda üzvlərinin hədəfləri
    if request.user.rol in ['REHBER', 'ADMIN', 'SUPERADMIN']:
        team_goals = Hedef.objects.filter(
            plan__ishchi__organization_unit=request.user.organization_unit,
            son_tarix__range=[start_date, end_date],
            status__in=['BASHLANMAYIB', 'ICRADA']
        ).exclude(plan__ishchi=request.user).select_related('plan', 'plan__ishchi')
        
        for goal in team_goals:
            days_left = (goal.son_tarix - timezone.now().date()).days
            if days_left <= 3:
                color = '#e83e8c'  # Çəhrayı - komanda üçün təcili
            else:
                color = '#6f42c1'  # Bənövşəyi - komanda
            
            events.append({
                'id': f'team_goal_{goal.id}',
                'title': f'👥 {goal.plan.ishchi.get_full_name()}: {goal.tesvir[:25]}...' if len(goal.tesvir) > 25 else f'👥 {goal.plan.ishchi.get_full_name()}: {goal.tesvir}',
                'start': goal.son_tarix.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'textColor': 'white',
                'extendedProps': {
                    'type': 'team_goal_deadline',
                    'description': f'Komanda hədəfi: {goal.tesvir}',
                    'employee': goal.plan.ishchi.get_full_name(),
                    'status': goal.get_status_display(),
                    'days_left': days_left
                }
            })
    
    # 4. Vaciblə bildirişlərin tarixi
    important_notifications = Notification.objects.filter(
        recipient=request.user,
        created_at__date__range=[start_date, end_date],
        priority__in=['HIGH', 'URGENT'],
        is_archived=False
    )
    
    for notification in important_notifications:
        events.append({
            'id': f'notification_{notification.id}',
            'title': f'🔔 {notification.title}',
            'start': notification.created_at.date().isoformat(),
            'backgroundColor': '#17a2b8',
            'borderColor': '#17a2b8',
            'textColor': 'white',
            'extendedProps': {
                'type': 'notification',
                'description': notification.message,
                'priority': notification.get_priority_display(),
                'is_read': notification.is_read
            }
        })
    
    # 5. Qiymətləndirmə tarixi (əgər var)
    evaluations = Qiymetlendirme.objects.filter(
        Q(qiymetlendirilen=request.user) | Q(qiymetlendiren=request.user),
        tarix__range=[start_date, end_date]
    ).select_related('qiymetlendirilen', 'qiymetlendiren')
    
    for evaluation in evaluations:
        if evaluation.qiymetlendirilen == request.user:
            title = f'📊 Qiymətləndirmə (Tərəfimdən)'
            color = '#20c997'
        else:
            title = f'📊 Qiymətləndirmə ({evaluation.qiymetlendirilen.get_full_name()})'
            color = '#6610f2'
        
        events.append({
            'id': f'evaluation_{evaluation.id}',
            'title': title,
            'start': evaluation.tarix.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'textColor': 'white',
            'extendedProps': {
                'type': 'evaluation',
                'description': f'Performans qiymətləndirməsi - {evaluation.umumi_qiymet} bal',
                'score': evaluation.umumi_qiymet,
                'evaluator': evaluation.qiymetlendiren.get_full_name(),
                'employee': evaluation.qiymetlendirilen.get_full_name()
            }
        })
    
    # 6. İstifadəçi yaratdığı hadisələr
    custom_events = CalendarEvent.get_events_for_period(
        user=request.user,
        start_date=start_date,
        end_date=end_date,
        include_private=True
    )
    
    for custom_event in custom_events:
        events.append(custom_event.to_fullcalendar_event())
    
    return JsonResponse(events, safe=False)


@login_required
@require_http_methods(["POST"])
def create_reminder(request):
    """Xatırlatma yaratma"""
    try:
        data = json.loads(request.body)
        
        title = data.get('title')
        date = data.get('date')
        description = data.get('description', '')
        
        if not title or not date:
            return JsonResponse({'error': 'Başlıq və tarix mütləqdir'}, status=400)
        
        # Tarix format yoxlaması
        try:
            reminder_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
        except ValueError:
            return JsonResponse({'error': 'Yanlış tarix formatı'}, status=400)
        
        # Notification kimi xatırlatma yarat
        from .notifications import NotificationManager
        
        notification = NotificationManager.create_and_send(
            recipient=request.user,
            title=f"⏰ Xatırlatma: {title}",
            message=description or f"{title} üçün xatırlatma",
            notification_type='INFO',
            priority='MEDIUM',
            expires_in_days=30
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Xatırlatma yaradıldı',
            'event': {
                'id': f'reminder_{notification.id}',
                'title': f'⏰ {title}',
                'start': reminder_date.isoformat(),
                'backgroundColor': '#fd7e14',
                'borderColor': '#fd7e14',
                'textColor': 'white'
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Yanlış JSON formatı'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def calendar_stats(request):
    """Təqvim statistikaları API"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    today = timezone.now().date()
    week_from_now = today + timedelta(days=7)
    month_from_now = today + timedelta(days=30)
    
    stats = {
        'upcoming_deadlines': {
            'this_week': Hedef.objects.filter(
                plan__ishchi=request.user,
                son_tarix__range=[today, week_from_now],
                status__in=['BASHLANMAYIB', 'ICRADA']
            ).count(),
            'this_month': Hedef.objects.filter(
                plan__ishchi=request.user,
                son_tarix__range=[today, month_from_now],
                status__in=['BASHLANMAYIB', 'ICRADA']
            ).count(),
            'overdue': Hedef.objects.filter(
                plan__ishchi=request.user,
                son_tarix__lt=today,
                status__in=['BASHLANMAYIB', 'ICRADA']
            ).count()
        },
        'evaluations': {
            'pending': Qiymetlendirme.objects.filter(
                qiymetlendirilen=request.user,
                umumi_qiymet__isnull=True
            ).count(),
            'completed_this_month': Qiymetlendirme.objects.filter(
                qiymetlendirilen=request.user,
                tarix__month=today.month,
                tarix__year=today.year
            ).count()
        },
        'active_periods': QiymetlendirmeDovru.objects.filter(
            bashlama_tarixi__lte=today,
            bitme_tarixi__gte=today
        ).count()
    }
    
    # Rəhbər üçün komanda statistikaları
    if request.user.rol in ['REHBER', 'ADMIN', 'SUPERADMIN']:
        stats['team'] = {
            'upcoming_deadlines': Hedef.objects.filter(
                plan__ishchi__organization_unit=request.user.organization_unit,
                son_tarix__range=[today, week_from_now],
                status__in=['BASHLANMAYIB', 'ICRADA']
            ).exclude(plan__ishchi=request.user).count(),
            'team_members': request.user.organization_unit.ishchiler.filter(
                is_active=True
            ).exclude(id=request.user.id).count() if request.user.organization_unit else 0
        }
    
    return JsonResponse(stats)


@login_required
def event_detail(request, event_type, event_id):
    """Hadisə detalları modal"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    try:
        if event_type == 'goal':
            goal = get_object_or_404(Hedef, id=event_id, plan__ishchi=request.user)
            
            return JsonResponse({
                'title': goal.tesvir,
                'description': f'Status: {goal.get_status_display()}',
                'deadline': goal.son_tarix.strftime('%d.%m.%Y'),
                'days_left': (goal.son_tarix - timezone.now().date()).days,
                'plan_owner': goal.plan.ishchi.get_full_name(),
                'actions': [
                    {
                        'text': 'Planı Gör',
                        'url': f'/plan/bax/{goal.plan.id}/',
                        'class': 'btn-primary'
                    }
                ]
            })
            
        elif event_type == 'evaluation':
            evaluation = get_object_or_404(
                Qiymetlendirme, 
                Q(qiymetlendirilen=request.user) | Q(qiymetlendiren=request.user),
                id=event_id
            )
            
            return JsonResponse({
                'title': 'Performans Qiymətləndirməsi',
                'description': f'Qiymətləndirən: {evaluation.qiymetlendiren.get_full_name()}',
                'score': evaluation.umumi_qiymet,
                'date': evaluation.tarix.strftime('%d.%m.%Y'),
                'actions': [
                    {
                        'text': 'Detalları Gör',
                        'url': f'/qiymetlendirmelerim/',
                        'class': 'btn-primary'
                    }
                ]
            })
            
        elif event_type == 'period':
            period = get_object_or_404(QiymetlendirmeDovru, id=event_id)
            
            return JsonResponse({
                'title': period.ad,
                'description': 'Qiymətləndirmə dövrü',
                'start_date': period.bashlama_tarixi.strftime('%d.%m.%Y'),
                'end_date': period.bitme_tarixi.strftime('%d.%m.%Y'),
                'is_active': period.bashlama_tarixi <= timezone.now().date() <= period.bitme_tarixi,
                'actions': []
            })
            
        else:
            return JsonResponse({'error': 'Naməlum hadisə növü'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_event(request):
    """Yeni təqvim hadisəsi yaratma"""
    try:
        data = json.loads(request.body)
        
        title = data.get('title')
        start_date = data.get('start_date')
        
        if not title or not start_date:
            return JsonResponse({'error': 'Başlıq və tarix mütləqdir'}, status=400)
        
        # Tarix format yoxlaması
        try:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
        except ValueError:
            return JsonResponse({'error': 'Yanlış tarix formatı'}, status=400)
        
        # Hadisə yaradırıq
        event = CalendarEvent(
            created_by=request.user,
            title=title,
            description=data.get('description', ''),
            start_date=start_date_obj,
            event_type=data.get('event_type', CalendarEvent.EventType.PERSONAL),
            priority=data.get('priority', CalendarEvent.Priority.MEDIUM),
            color=data.get('color', '#3788d8'),
            location=data.get('location', ''),
            is_all_day=data.get('is_all_day', False),
            is_private=data.get('is_private', True),
            reminder_minutes=data.get('reminder_minutes')
        )
        
        # End date əlavə et (əgər var)
        end_date = data.get('end_date')
        if end_date:
            try:
                event.end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
            except ValueError:
                pass
        
        # Vaxt məlumatları əlavə et (əgər bütün gün deyil)
        if not event.is_all_day:
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            
            if start_time:
                try:
                    event.start_time = datetime.strptime(start_time, '%H:%M').time()
                except ValueError:
                    pass
            
            if end_time:
                try:
                    event.end_time = datetime.strptime(end_time, '%H:%M').time()
                except ValueError:
                    pass
        
        event.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Hadisə uğurla yaradıldı',
            'event': event.to_fullcalendar_event()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Yanlış JSON formatı'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_event(request, event_id):
    """Təqvim hadisəsini yenilə"""
    try:
        event = get_object_or_404(CalendarEvent, id=event_id, created_by=request.user)
        data = json.loads(request.body)
        
        # Məlumatları yenilə
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'start_date' in data:
            try:
                event.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00')).date()
            except ValueError:
                return JsonResponse({'error': 'Yanlış başlama tarixi formatı'}, status=400)
        
        if 'end_date' in data and data['end_date']:
            try:
                event.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')).date()
            except ValueError:
                return JsonResponse({'error': 'Yanlış bitmə tarixi formatı'}, status=400)
        
        if 'event_type' in data:
            event.event_type = data['event_type']
        if 'priority' in data:
            event.priority = data['priority']
        if 'color' in data:
            event.color = data['color']
        if 'location' in data:
            event.location = data['location']
        if 'is_all_day' in data:
            event.is_all_day = data['is_all_day']
        if 'is_private' in data:
            event.is_private = data['is_private']
        if 'reminder_minutes' in data:
            event.reminder_minutes = data['reminder_minutes']
        
        # Vaxt məlumatları
        if not event.is_all_day:
            if 'start_time' in data and data['start_time']:
                try:
                    event.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
                except ValueError:
                    pass
            
            if 'end_time' in data and data['end_time']:
                try:
                    event.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
                except ValueError:
                    pass
        else:
            event.start_time = None
            event.end_time = None
        
        event.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Hadisə uğurla yeniləndi',
            'event': event.to_fullcalendar_event()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Yanlış JSON formatı'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_event(request, event_id):
    """Təqvim hadisəsini sil"""
    try:
        event = get_object_or_404(CalendarEvent, id=event_id, created_by=request.user)
        event.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Hadisə uğurla silindi'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def event_form_modal(request, event_id=None):
    """Hadisə yaratma/redaktə formu modal"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bu endpoint yalnız AJAX üçündür'}, status=400)
    
    event = None
    if event_id:
        try:
            event = get_object_or_404(CalendarEvent, id=event_id, created_by=request.user)
        except:
            return JsonResponse({'error': 'Hadisə tapılmadı'}, status=404)
    
    # Form HTML yaradırıq
    form_html = f"""
    <form id="eventForm" data-event-id="{event.id if event else ''}">
        <div class="row">
            <div class="col-md-12 mb-3">
                <label class="form-label">Başlıq <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="eventTitle" name="title" 
                       value="{event.title if event else ''}" required>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6 mb-3">
                <label class="form-label">Hadisə Növü</label>
                <select class="form-select" id="eventType" name="event_type">
                    <option value="PERSONAL" {'selected' if event and event.event_type == 'PERSONAL' else ''}>Şəxsi</option>
                    <option value="MEETING" {'selected' if event and event.event_type == 'MEETING' else ''}>Görüş</option>
                    <option value="TASK" {'selected' if event and event.event_type == 'TASK' else ''}>Tapşırıq</option>
                    <option value="REMINDER" {'selected' if event and event.event_type == 'REMINDER' else ''}>Xatırlatma</option>
                    <option value="DEADLINE" {'selected' if event and event.event_type == 'DEADLINE' else ''}>Son Tarix</option>
                    <option value="TRAINING" {'selected' if event and event.event_type == 'TRAINING' else ''}>Təlim</option>
                    <option value="EVALUATION" {'selected' if event and event.event_type == 'EVALUATION' else ''}>Qiymətləndirmə</option>
                    <option value="OTHER" {'selected' if event and event.event_type == 'OTHER' else ''}>Digər</option>
                </select>
            </div>
            
            <div class="col-md-6 mb-3">
                <label class="form-label">Prioritet</label>
                <select class="form-select" id="eventPriority" name="priority">
                    <option value="LOW" {'selected' if event and event.priority == 'LOW' else ''}>Aşağı</option>
                    <option value="MEDIUM" {'selected' if event and event.priority == 'MEDIUM' else ''}>Orta</option>
                    <option value="HIGH" {'selected' if event and event.priority == 'HIGH' else ''}>Yüksək</option>
                    <option value="URGENT" {'selected' if event and event.priority == 'URGENT' else ''}>Təcili</option>
                </select>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6 mb-3">
                <label class="form-label">Başlama Tarixi <span class="text-danger">*</span></label>
                <input type="date" class="form-control" id="eventStartDate" name="start_date" 
                       value="{event.start_date if event else ''}" required>
            </div>
            
            <div class="col-md-6 mb-3">
                <label class="form-label">Bitmə Tarixi</label>
                <input type="date" class="form-control" id="eventEndDate" name="end_date" 
                       value="{event.end_date if event else ''}">
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12 mb-3">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="eventAllDay" name="is_all_day" 
                           {'checked' if event and event.is_all_day else ''}>
                    <label class="form-check-label" for="eventAllDay">
                        Bütün gün
                    </label>
                </div>
            </div>
        </div>
        
        <div class="row" id="timeFields" style="{'display: none;' if event and event.is_all_day else ''}">
            <div class="col-md-6 mb-3">
                <label class="form-label">Başlama Vaxtı</label>
                <input type="time" class="form-control" id="eventStartTime" name="start_time" 
                       value="{event.start_time.strftime('%H:%M') if event and event.start_time else ''}">
            </div>
            
            <div class="col-md-6 mb-3">
                <label class="form-label">Bitmə Vaxtı</label>
                <input type="time" class="form-control" id="eventEndTime" name="end_time" 
                       value="{event.end_time.strftime('%H:%M') if event and event.end_time else ''}">
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6 mb-3">
                <label class="form-label">Rəng</label>
                <input type="color" class="form-control form-control-color" id="eventColor" name="color" 
                       value="{event.color if event else '#3788d8'}">
            </div>
            
            <div class="col-md-6 mb-3">
                <div class="form-check mt-4">
                    <input class="form-check-input" type="checkbox" id="eventPrivate" name="is_private" 
                           {'checked' if event and event.is_private else 'checked'}>
                    <label class="form-check-label" for="eventPrivate">
                        Şəxsi hadisə
                    </label>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6 mb-3">
                <label class="form-label">Yer</label>
                <input type="text" class="form-control" id="eventLocation" name="location" 
                       value="{event.location if event else ''}" placeholder="Hadisənin yeri">
            </div>
            
            <div class="col-md-6 mb-3">
                <label class="form-label">Xatırlatma</label>
                <select class="form-select" id="eventReminder" name="reminder_minutes">
                    <option value="">Xatırlatma yox</option>
                    <option value="5" {'selected' if event and event.reminder_minutes == 5 else ''}>5 dəqiqə əvvəl</option>
                    <option value="15" {'selected' if event and event.reminder_minutes == 15 else ''}>15 dəqiqə əvvəl</option>
                    <option value="30" {'selected' if event and event.reminder_minutes == 30 else ''}>30 dəqiqə əvvəl</option>
                    <option value="60" {'selected' if event and event.reminder_minutes == 60 else ''}>1 saat əvvəl</option>
                    <option value="1440" {'selected' if event and event.reminder_minutes == 1440 else ''}>1 gün əvvəl</option>
                </select>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12 mb-3">
                <label class="form-label">Təsvir</label>
                <textarea class="form-control" id="eventDescription" name="description" rows="3" 
                          placeholder="Hadisə haqqında əlavə məlumat">{event.description if event else ''}</textarea>
            </div>
        </div>
    </form>
    """
    
    return JsonResponse({
        'title': f'{"Hadisəni Redaktə Et" if event else "Yeni Hadisə Yarat"}',
        'form_html': form_html,
        'event_id': event.id if event else None
    })