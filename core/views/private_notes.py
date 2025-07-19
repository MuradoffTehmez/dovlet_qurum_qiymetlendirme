"""
Private Notes (Məxfi Qeydlər) Views
Rəhbərlərin işçilər haqqında məxfi qeydləri
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

from ..models import Ishchi, PrivateNote, QiymetlendirmeDovru, Notification
from ..permissions import require_role


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
def private_notes_dashboard(request):
    """Məxfi qeydlər dashboard"""
    
    # Rəhbər olan işçilər (alt işçiləri)
    subordinates = Ishchi.objects.filter(
        rehber=request.user,
        is_active=True
    ).order_by('first_name', 'last_name')
    
    # Son qeydlər
    recent_notes = PrivateNote.objects.filter(
        manager=request.user,
        is_archived=False
    ).select_related('employee', 'related_cycle').order_by('-created_at')[:10]
    
    # Statistikalar
    stats = {
        'total_notes': PrivateNote.objects.filter(manager=request.user).count(),
        'this_month_notes': PrivateNote.objects.filter(
            manager=request.user,
            created_at__gte=timezone.now().replace(day=1)
        ).count(),
        'subordinates_count': subordinates.count(),
        'urgent_notes': PrivateNote.objects.filter(
            manager=request.user,
            priority=PrivateNote.Priority.URGENT,
            is_archived=False
        ).count()
    }
    
    # Qeyd növləri üzrə paylanma
    note_types_stats = PrivateNote.objects.filter(
        manager=request.user
    ).values('note_type').annotate(count=Count('id')).order_by('-count')
    
    context = {
        'subordinates': subordinates,
        'recent_notes': recent_notes,
        'stats': stats,
        'note_types_stats': note_types_stats,
        'page_title': 'Məxfi Qeydlər'
    }
    
    return render(request, 'private_notes/dashboard.html', context)


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
def employee_notes(request, employee_id):
    """Bir işçi haqqında bütün qeydlər"""
    
    employee = get_object_or_404(
        Ishchi, 
        id=employee_id,
        rehber=request.user  # Yalnız alt işçi olmalıdır
    )
    
    # Filtr parametrləri
    note_type = request.GET.get('note_type')
    priority = request.GET.get('priority')
    cycle_id = request.GET.get('cycle')
    tags = request.GET.get('tags')
    
    # Base query
    notes = PrivateNote.objects.filter(
        employee=employee,
        manager=request.user,
        is_archived=False
    ).select_related('related_cycle')
    
    # Filtrlər
    if note_type:
        notes = notes.filter(note_type=note_type)
    
    if priority:
        notes = notes.filter(priority=priority)
    
    if cycle_id:
        notes = notes.filter(related_cycle_id=cycle_id)
    
    if tags:
        notes = notes.filter(tags__icontains=tags)
    
    notes = notes.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtr üçün data
    cycles = QiymetlendirmeDovru.objects.filter(aktivdir=True).order_by('-baslama_tarixi')
    all_tags = set()
    for note in PrivateNote.objects.filter(employee=employee, manager=request.user):
        all_tags.update(note.get_tags_list())
    
    # Statistikalar
    stats = {
        'total_notes': notes.count(),
        'performance_notes': notes.filter(note_type=PrivateNote.NoteType.PERFORMANCE).count(),
        'development_notes': notes.filter(note_type=PrivateNote.NoteType.DEVELOPMENT).count(),
        'concern_notes': notes.filter(note_type=PrivateNote.NoteType.CONCERN).count(),
        'achievement_notes': notes.filter(note_type=PrivateNote.NoteType.ACHIEVEMENT).count(),
    }
    
    context = {
        'employee': employee,
        'page_obj': page_obj,
        'cycles': cycles,
        'all_tags': sorted(all_tags),
        'stats': stats,
        'current_filters': {
            'note_type': note_type,
            'priority': priority,
            'cycle': cycle_id,
            'tags': tags,
        },
        'page_title': f'{employee.get_full_name()} - Məxfi Qeydlər'
    }
    
    return render(request, 'private_notes/employee_notes.html', context)


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
def create_note(request, employee_id=None):
    """Yeni qeyd yaratma"""
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Form məlumatları
                employee_id = request.POST.get('employee_id')
                title = request.POST.get('title', '').strip()
                content = request.POST.get('content', '').strip()
                note_type = request.POST.get('note_type', PrivateNote.NoteType.GENERAL)
                priority = request.POST.get('priority', PrivateNote.Priority.MEDIUM)
                cycle_id = request.POST.get('cycle_id')
                tags = request.POST.get('tags', '').strip()
                is_confidential = request.POST.get('is_confidential') == 'on'
                
                # Validasiya
                if not employee_id or not title or not content:
                    messages.error(request, 'Bütün tələb olunan sahələr doldurulmalıdır.')
                    return redirect('private_notes:create', employee_id=employee_id)
                
                employee = get_object_or_404(
                    Ishchi, 
                    id=employee_id, 
                    rehber=request.user
                )
                
                cycle = None
                if cycle_id:
                    cycle = get_object_or_404(QiymetlendirmeDovru, id=cycle_id)
                
                # Qeyd yaratmaq
                note = PrivateNote.objects.create(
                    employee=employee,
                    manager=request.user,
                    title=title,
                    content=content,
                    note_type=note_type,
                    priority=priority,
                    related_cycle=cycle,
                    tags=tags,
                    is_confidential=is_confidential
                )
                
                # Təcili qeyd üçün bildiriş
                if priority == PrivateNote.Priority.URGENT:
                    # HR-a və ya üst rəhbərə bildiriş göndər
                    pass  # Bu hissə sonra həyata keçiriləcək
                
                messages.success(request, f'{employee.get_full_name()} haqqında qeyd uğurla yaradıldı.')
                return redirect('private_notes:employee_notes', employee_id=employee.id)
                
        except Exception as e:
            messages.error(request, f'Qeyd yaradılarkən xəta: {str(e)}')
            return redirect('private_notes:create', employee_id=employee_id)
    
    # GET request
    subordinates = Ishchi.objects.filter(
        rehber=request.user,
        is_active=True
    ).order_by('first_name', 'last_name')
    
    cycles = QiymetlendirmeDovru.objects.filter(aktivdir=True).order_by('-baslama_tarixi')
    
    selected_employee = None
    if employee_id:
        selected_employee = get_object_or_404(
            Ishchi, 
            id=employee_id, 
            rehber=request.user
        )
    
    context = {
        'subordinates': subordinates,
        'cycles': cycles,
        'selected_employee': selected_employee,
        'note_types': PrivateNote.NoteType.choices,
        'priorities': PrivateNote.Priority.choices,
        'page_title': 'Yeni Məxfi Qeyd'
    }
    
    return render(request, 'private_notes/create.html', context)


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
def edit_note(request, note_id):
    """Qeydi redaktə etmə"""
    
    note = get_object_or_404(
        PrivateNote,
        id=note_id,
        manager=request.user
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Form məlumatları
                title = request.POST.get('title', '').strip()
                content = request.POST.get('content', '').strip()
                note_type = request.POST.get('note_type', note.note_type)
                priority = request.POST.get('priority', note.priority)
                cycle_id = request.POST.get('cycle_id')
                tags = request.POST.get('tags', '').strip()
                is_confidential = request.POST.get('is_confidential') == 'on'
                
                # Validasiya
                if not title or not content:
                    messages.error(request, 'Başlıq və məzmun sahələri mütləqdir.')
                    return redirect('private_notes:edit', note_id=note.id)
                
                # Qeydi yenilə
                note.title = title
                note.content = content
                note.note_type = note_type
                note.priority = priority
                note.tags = tags
                note.is_confidential = is_confidential
                
                if cycle_id:
                    note.related_cycle = get_object_or_404(QiymetlendirmeDovru, id=cycle_id)
                else:
                    note.related_cycle = None
                
                note.save()
                
                messages.success(request, 'Qeyd uğurla yeniləndi.')
                return redirect('private_notes:employee_notes', employee_id=note.employee.id)
                
        except Exception as e:
            messages.error(request, f'Qeyd yenilənərkən xəta: {str(e)}')
            return redirect('private_notes:edit', note_id=note.id)
    
    # GET request
    cycles = QiymetlendirmeDovru.objects.filter(aktivdir=True).order_by('-baslama_tarixi')
    
    context = {
        'note': note,
        'cycles': cycles,
        'note_types': PrivateNote.NoteType.choices,
        'priorities': PrivateNote.Priority.choices,
        'page_title': f'Qeydi Redaktə Et - {note.title}'
    }
    
    return render(request, 'private_notes/edit.html', context)


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
def view_note(request, note_id):
    """Qeydi görüntüləmə"""
    
    note = get_object_or_404(
        PrivateNote,
        id=note_id,
        manager=request.user
    )
    
    context = {
        'note': note,
        'page_title': f'Qeyd: {note.title}'
    }
    
    return render(request, 'private_notes/view.html', context)


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
@require_http_methods(["POST"])
def delete_note(request, note_id):
    """Qeydi silmə (arxivləşdirmə)"""
    
    note = get_object_or_404(
        PrivateNote,
        id=note_id,
        manager=request.user
    )
    
    note.is_archived = True
    note.save()
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Qeyd arxivləşdirildi.')
    return redirect('private_notes:employee_notes', employee_id=note.employee.id)


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
def search_notes(request):
    """Qeydlərdə axtarış"""
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'notes': []})
    
    notes = PrivateNote.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query) | Q(tags__icontains=query),
        manager=request.user,
        is_archived=False
    ).select_related('employee', 'related_cycle').order_by('-created_at')[:20]
    
    data = []
    for note in notes:
        data.append({
            'id': note.id,
            'title': note.title,
            'employee_name': note.employee.get_full_name(),
            'note_type': note.get_note_type_display(),
            'priority': note.get_priority_display(),
            'created_at': note.created_at.strftime('%d.%m.%Y'),
            'url': f'/private-notes/view/{note.id}/'
        })
    
    return JsonResponse({'notes': data})


@login_required
@require_role(['REHBER', 'ADMIN', 'SUPERADMIN'])
def notes_analytics(request):
    """Qeydlər analitikası"""
    
    # Son 6 ay məlumatları
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    
    # Aylıq statistikalar
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    
    monthly_stats = PrivateNote.objects.filter(
        manager=request.user,
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Növ üzrə statistikalar
    type_stats = PrivateNote.objects.filter(
        manager=request.user
    ).values('note_type').annotate(count=Count('id')).order_by('-count')
    
    # İşçi üzrə statistikalar
    employee_stats = PrivateNote.objects.filter(
        manager=request.user
    ).values('employee__first_name', 'employee__last_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Ən çox istifadə olunan etiketlər
    all_tags = []
    for note in PrivateNote.objects.filter(manager=request.user):
        all_tags.extend(note.get_tags_list())
    
    from collections import Counter
    tag_stats = Counter(all_tags).most_common(10)
    
    context = {
        'monthly_stats': monthly_stats,
        'type_stats': type_stats,
        'employee_stats': employee_stats,
        'tag_stats': tag_stats,
        'page_title': 'Qeydlər Analitikası'
    }
    
    return render(request, 'private_notes/analytics.html', context)