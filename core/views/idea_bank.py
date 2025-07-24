"""
Idea Bank (Təklif və İdeya Bankı) Views
İşçilərin ideyalarını paylaşdığı və səs verdiyi forum sistemi
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Case, When, IntegerField

from ..models import Ishchi, Idea, IdeaCategory, IdeaVote, IdeaComment, Notification
from ..permissions import require_role

IDEA_BANK_CREATE = 'idea_bank:create'
IDEA_BANK_DETAIL = 'idea_bank:detail'
IDEA_VIEW_TEXT = "İdeyanı Görüntülə"
APPLICATION_JSON = 'application/json'


@login_required
def idea_bank_dashboard(request):
    """İdeya Bankı ana səhifəsi"""
    
    # Filtr parametrləri
    category_id = request.GET.get('category')
    status = request.GET.get('status')
    sort_by = request.GET.get('sort', 'recent')  # recent, popular, top_rated
    
    # Base query
    ideas = Idea.objects.exclude(status=Idea.Status.DRAFT).select_related(
        'author', 'category', 'reviewer'
    ).annotate(
        upvotes=Count(Case(When(votes__vote_type='UPVOTE', then=1), output_field=IntegerField())),
        downvotes=Count(Case(When(votes__vote_type='DOWNVOTE', then=1), output_field=IntegerField())),
        comments_count=Count('comments', distinct=True)
    )
    
    # Filtrlər
    if category_id:
        ideas = ideas.filter(category_id=category_id)
    
    if status:
        ideas = ideas.filter(status=status)
    
    # Sıralama
    if sort_by == 'popular':
        ideas = ideas.order_by('-upvotes', '-created_at')
    elif sort_by == 'top_rated':
        ideas = ideas.order_by('-upvotes', 'downvotes', '-created_at')
    elif sort_by == 'commented':
        ideas = ideas.order_by('-comments_count', '-created_at')
    else:  # recent
        ideas = ideas.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(ideas, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtr üçün data
    categories = IdeaCategory.objects.filter(is_active=True).annotate(
        ideas_count=Count('ideas')
    ).order_by('name')
    
    # Statistikalar
    stats = {
        'total_ideas': Idea.objects.exclude(status=Idea.Status.DRAFT).count(),
        'this_month_ideas': Idea.objects.filter(
            created_at__gte=timezone.now().replace(day=1)
        ).exclude(status=Idea.Status.DRAFT).count(),
        'approved_ideas': Idea.objects.filter(status=Idea.Status.APPROVED).count(),
        'implemented_ideas': Idea.objects.filter(status=Idea.Status.IMPLEMENTED).count(),
        'my_ideas': Idea.objects.filter(author=request.user).count(),
    }
    
    # Trending ideyalar (son həftədə ən çox səs alan)
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    trending_ideas = Idea.objects.exclude(status=Idea.Status.DRAFT).annotate(
        recent_upvotes=Count(Case(
            When(votes__vote_type='UPVOTE', votes__created_at__gte=one_week_ago, then=1),
            output_field=IntegerField()
        ))
    ).filter(recent_upvotes__gt=0).order_by('-recent_upvotes')[:5]
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'trending_ideas': trending_ideas,
        'stats': stats,
        'current_filters': {
            'category': int(category_id) if category_id else None,
            'status': status,
            'sort': sort_by,
        },
        'page_title': 'İdeya Bankı'
    }
    return render(request, 'core/dashboard.html', context)
    # return render(request, 'idea_bank/dashboard.html', context)


@login_required
def idea_detail(request, idea_id):
    """İdeya detayı və şərhlər"""
    
    idea = get_object_or_404(
        Idea.objects.select_related('author', 'category', 'reviewer').annotate(
            upvotes=Count(Case(When(votes__vote_type='UPVOTE', then=1), output_field=IntegerField())),
            downvotes=Count(Case(When(votes__vote_type='DOWNVOTE', then=1), output_field=IntegerField()))
        ),
        id=idea_id
    )
    
    # İstifadəçinin səsi
    user_vote = IdeaVote.objects.filter(idea=idea, user=request.user).first()
    
    # Şərhlər (hierarchy ilə)
    comments = IdeaComment.objects.filter(
        idea=idea, parent=None, is_hidden=False
    ).select_related('author').prefetch_related(
        'replies__author'
    ).order_by('created_at')
    
    # Bənzər ideyalar
    similar_ideas = Idea.objects.filter(
        category=idea.category
    ).exclude(id=idea.id).exclude(status=Idea.Status.DRAFT)[:5]
    
    context = {
        'idea': idea,
        'user_vote': user_vote,
        'comments': comments,
        'similar_ideas': similar_ideas,
        'page_title': idea.title
    }
    
    return render(request, 'idea_bank/detail.html', context)


@login_required
def create_idea(request):
    """Yeni ideya yaratma"""
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Form məlumatları
                title = request.POST.get('title', '').strip()
                description = request.POST.get('description', '').strip()
                category_id = request.POST.get('category')
                priority = request.POST.get('priority', Idea.Priority.MEDIUM)
                estimated_impact = request.POST.get('estimated_impact', '').strip()
                budget_estimate = request.POST.get('budget_estimate')
                is_anonymous = request.POST.get('is_anonymous') == 'on'
                save_as_draft = request.POST.get('save_as_draft') == 'on'
                
                # Validasiya
                if not title or not description:
                    messages.error(request, 'Başlıq və təsvir sahələri mütləqdir.')
                    return redirect(IDEA_BANK_CREATE)
                
                category = None
                if category_id:
                    category = get_object_or_404(IdeaCategory, id=category_id)
                
                # Budget validasiyası
                budget_value = None
                if budget_estimate:
                    try:
                        budget_value = float(budget_estimate)
                    except ValueError:
                        messages.error(request, 'Büdcə təxmini düzgün rəqəm deyil.')
                        return redirect(IDEA_BANK_CREATE)
                
                # İdeya yaratmaq
                idea = Idea.objects.create(
                    title=title,
                    description=description,
                    category=category,
                    author=request.user,
                    priority=priority,
                    estimated_impact=estimated_impact,
                    budget_estimate=budget_value,
                    is_anonymous=is_anonymous,
                    status=Idea.Status.DRAFT if save_as_draft else Idea.Status.SUBMITTED
                )
                
                if not save_as_draft:
                    idea.submitted_at = timezone.now()
                    idea.save()
                    
                    # Bildiriş göndər (administratorlara)
                    admins = Ishchi.objects.filter(rol__in=['ADMIN', 'SUPERADMIN'])
                    for admin in admins:
                        Notification.create_notification(
                            recipient=admin,
                            title=f"Yeni İdeya: {title}",
                            message=f"{idea.get_author_display()} yeni ideya təqdim etdi.",
                            notification_type=Notification.NotificationType.IDEA_SUBMITTED,
                            priority=Notification.Priority.MEDIUM,
                            action_url=f"/idea-bank/{idea.id}/",
                            action_text=IDEA_VIEW_TEXT
                        )
                
                if save_as_draft:
                    messages.success(request, 'İdeya layihə olaraq saxlanıldı.')
                    return redirect('idea_bank:my_ideas')
                else:
                    messages.success(request, 'İdeya uğurla təqdim edildi!')
                    return redirect(IDEA_BANK_DETAIL, idea_id=idea.id)
                
        except Exception as e:
            messages.error(request, f'İdeya yaradılarkən xəta: {str(e)}')
            return redirect(IDEA_BANK_CREATE)
    
    # GET request
    categories = IdeaCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'categories': categories,
        'priorities': Idea.Priority.choices,
        'page_title': 'Yeni İdeya'
    }
    
    return render(request, 'idea_bank/create.html', context)


@login_required
def edit_idea(request, idea_id):
    """İdeya redaktəsi (yalnız müəllif və ya admin)"""
    
    idea = get_object_or_404(Idea, id=idea_id)
    
    # İcazə yoxlanışı
    if idea.author != request.user and request.user.rol not in ['ADMIN', 'SUPERADMIN']:
        messages.error(request, 'Bu ideyanı redaktə etmək icazəniz yoxdur.')
        return redirect(IDEA_BANK_DETAIL, idea_id=idea.id)
    
    # Yalnız layihə və ya təqdim edilmiş ideyalar redaktə oluna bilər
    if idea.status not in [Idea.Status.DRAFT, Idea.Status.SUBMITTED]:
        messages.error(request, 'Bu ideya artıq redaktə edilə bilməz.')
        return redirect(IDEA_BANK_DETAIL, idea_id=idea.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Form məlumatları
                title = request.POST.get('title', '').strip()
                description = request.POST.get('description', '').strip()
                category_id = request.POST.get('category')
                priority = request.POST.get('priority', idea.priority)
                estimated_impact = request.POST.get('estimated_impact', '').strip()
                budget_estimate = request.POST.get('budget_estimate')
                is_anonymous = request.POST.get('is_anonymous') == 'on'
                save_as_draft = request.POST.get('save_as_draft') == 'on'
                
                # Validasiya
                if not title or not description:
                    messages.error(request, 'Başlıq və təsvir sahələri mütləqdir.')
                    return redirect('idea_bank:edit', idea_id=idea.id)
                
                # İdeyanı yenilə
                idea.title = title
                idea.description = description
                idea.priority = priority
                idea.estimated_impact = estimated_impact
                idea.is_anonymous = is_anonymous
                
                if category_id:
                    idea.category = get_object_or_404(IdeaCategory, id=category_id)
                
                if budget_estimate:
                    try:
                        idea.budget_estimate = float(budget_estimate)
                    except ValueError:
                        idea.budget_estimate = None
                
                if save_as_draft:
                    idea.status = Idea.Status.DRAFT
                    idea.submitted_at = None
                elif idea.status == Idea.Status.DRAFT:
                    idea.status = Idea.Status.SUBMITTED
                    idea.submitted_at = timezone.now()
                
                idea.save()
                
                messages.success(request, 'İdeya uğurla yeniləndi.')
                return redirect(IDEA_BANK_DETAIL, idea_id=idea.id)
                
        except Exception as e:
            messages.error(request, f'İdeya yenilənərkən xəta: {str(e)}')
            return redirect('idea_bank:edit', idea_id=idea.id)
    
    # GET request
    categories = IdeaCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'idea': idea,
        'categories': categories,
        'priorities': Idea.Priority.choices,
        'page_title': f'İdeyanı Redaktə Et - {idea.title}'
    }
    
    return render(request, 'idea_bank/edit.html', context)


@login_required
def my_ideas(request):
    """İstifadəçinin ideyaları"""
    
    status_filter = request.GET.get('status')
    
    ideas = Idea.objects.filter(author=request.user).select_related('category').annotate(
        upvotes=Count(Case(When(votes__vote_type='UPVOTE', then=1), output_field=IntegerField())),
        downvotes=Count(Case(When(votes__vote_type='DOWNVOTE', then=1), output_field=IntegerField())),
        comments_count=Count('comments')
    )
    
    if status_filter:
        ideas = ideas.filter(status=status_filter)
    
    ideas = ideas.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(ideas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistikalar
    stats = {
        'total': ideas.count(),
        'draft': ideas.filter(status=Idea.Status.DRAFT).count(),
        'submitted': ideas.filter(status=Idea.Status.SUBMITTED).count(),
        'approved': ideas.filter(status=Idea.Status.APPROVED).count(),
        'implemented': ideas.filter(status=Idea.Status.IMPLEMENTED).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'current_status': status_filter,
        'page_title': 'Mənim İdeyalarım'
    }
    
    return render(request, 'idea_bank/my_ideas.html', context)


@login_required
@require_http_methods(["POST"])
def vote_idea(request, idea_id):
    """İdeyaya səs vermə (AJAX)"""
    
    idea = get_object_or_404(Idea, id=idea_id)
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['UPVOTE', 'DOWNVOTE']:
        return JsonResponse({'success': False, 'error': 'Yanlış səs növü'})
    
    # Öz ideyasına səs verə bilməz
    if idea.author == request.user:
        return JsonResponse({'success': False, 'error': 'Öz ideyanıza səs verə bilməzsiniz'})
    
    try:
        with transaction.atomic():
            # Mövcud səsi tap
            existing_vote = IdeaVote.objects.filter(idea=idea, user=request.user).first()
            
            if existing_vote:
                if existing_vote.vote_type == vote_type:
                    # Eyni səsi geri çək
                    existing_vote.delete()
                    action = 'removed'
                else:
                    # Səsi dəyişdir
                    existing_vote.vote_type = vote_type
                    existing_vote.save()
                    action = 'changed'
            else:
                # Yeni səs
                IdeaVote.objects.create(
                    idea=idea,
                    user=request.user,
                    vote_type=vote_type
                )
                action = 'added'
            
            # Yenilənmiş səs saylarını hesabla
            upvotes = IdeaVote.objects.filter(idea=idea, vote_type='UPVOTE').count()
            downvotes = IdeaVote.objects.filter(idea=idea, vote_type='DOWNVOTE').count()
            
            return JsonResponse({
                'success': True,
                'action': action,
                'upvotes': upvotes,
                'downvotes': downvotes
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def add_comment(request, idea_id):
    """İdeyaya şərh əlavə etmə"""
    
    idea = get_object_or_404(Idea, id=idea_id)
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    is_anonymous = request.POST.get('is_anonymous') == 'on'
    
    if not content:
        if request.headers.get('Accept') == APPLICATION_JSON:
            return JsonResponse({'success': False, 'error': 'Şərh boş ola bilməz'})
        messages.error(request, 'Şərh boş ola bilməz.')
        return redirect(IDEA_BANK_DETAIL, idea_id=idea.id)
    
    try:
        parent = None
        if parent_id:
            parent = get_object_or_404(IdeaComment, id=parent_id, idea=idea)
        
        comment = IdeaComment.objects.create(
            idea=idea,
            author=request.user,
            content=content,
            parent=parent,
            is_anonymous=is_anonymous
        )
        
        # İdeya müəllifinə bildiriş göndər (özü deyilsə)
        if idea.author != request.user:
            Notification.create_notification(
                recipient=idea.author,
                title=f"Yeni Şərh: {idea.title}",
                message=f"{comment.get_author_display()} ideyanıza şərh yazdı.",
                notification_type=Notification.NotificationType.IDEA_COMMENTED,
                priority=Notification.Priority.LOW,
                action_url=f"/idea-bank/{idea.id}/",
                action_text=IDEA_VIEW_TEXT
            )
        
        if request.headers.get('Accept') == APPLICATION_JSON:
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'author': comment.get_author_display(),
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
                }
            })
        
        messages.success(request, 'Şərh əlavə edildi.')
        return redirect(IDEA_BANK_DETAIL, idea_id=idea.id)
        
    except Exception as e:
        if request.headers.get('Accept') == APPLICATION_JSON:
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f'Şərh əlavə edilərkən xəta: {str(e)}')
        return redirect(IDEA_BANK_DETAIL, idea_id=idea.id)


@login_required
@require_role(['ADMIN', 'SUPERADMIN'])
def admin_review(request):
    """Admin baxış paneli"""
    
    status_filter = request.GET.get('status', 'SUBMITTED')
    
    ideas = Idea.objects.filter(
        status=status_filter
    ).select_related('author', 'category').annotate(
        upvotes=Count(Case(When(votes__vote_type='UPVOTE', then=1), output_field=IntegerField())),
        downvotes=Count(Case(When(votes__vote_type='DOWNVOTE', then=1), output_field=IntegerField())),
        comments_count=Count('comments')
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(ideas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistikalar
    stats = {
        'pending': Idea.objects.filter(status=Idea.Status.SUBMITTED).count(),
        'under_review': Idea.objects.filter(status=Idea.Status.UNDER_REVIEW).count(),
        'approved': Idea.objects.filter(status=Idea.Status.APPROVED).count(),
        'rejected': Idea.objects.filter(status=Idea.Status.REJECTED).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'current_status': status_filter,
        'page_title': 'İdeya Baxışı - Admin Panel'
    }
    
    return render(request, 'idea_bank/admin_review.html', context)


@login_required
@require_role(['ADMIN', 'SUPERADMIN'])
@require_http_methods(["POST"])
def review_idea(request, idea_id):
    """İdeyanı baxış və qərar vermə"""
    
    idea = get_object_or_404(Idea, id=idea_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '').strip()
    
    if action == 'approve':
        idea.approve(request.user, notes)
        messages.success(request, f'İdeya "{idea.title}" təsdiqləndi.')
    elif action == 'reject':
        idea.reject(request.user, notes)
        messages.warning(request, f'İdeya "{idea.title}" rədd edildi.')
    elif action == 'under_review':
        idea.status = Idea.Status.UNDER_REVIEW
        idea.reviewer = request.user
        idea.review_notes = notes
        idea.reviewed_at = timezone.now()
        idea.save()
        messages.info(request, f'İdeya "{idea.title}" baxış altına alındı.')
    else:
        messages.error(request, 'Yanlış əməliyyat.')
        return redirect('idea_bank:admin_review')
    
    # İdeya müəllifinə bildiriş göndər
    Notification.create_notification(
        recipient=idea.author,
        title=f"İdeya Statusu Dəyişdi: {idea.title}",
        message=f"İdeyanızın statusu '{idea.get_status_display()}' olaraq dəyişdirildi.",
        notification_type=Notification.NotificationType.IDEA_STATUS_CHANGED,
        priority=Notification.Priority.MEDIUM,
        action_url=f"/idea-bank/{idea.id}/",
        action_text=IDEA_VIEW_TEXT
    )
    
    return redirect('idea_bank:admin_review')


@login_required
def idea_analytics(request):
    """İdeya bankı analitikası"""
    
    # Son 6 ay məlumatları
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    
    # Aylıq statistikalar
    from django.db.models.functions import TruncMonth
    
    monthly_stats = Idea.objects.filter(
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Status üzrə paylanma
    status_stats = Idea.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Kateqoriya üzrə statistikalar
    category_stats = Idea.objects.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Ən aktiv istifadəçilər
    top_contributors = Idea.objects.values('author__first_name', 'author__last_name').annotate(
        ideas_count=Count('id')
    ).order_by('-ideas_count')[:10]
    
    # Ən çox səs alan ideyalar
    top_voted_ideas = Idea.objects.annotate(
        total_votes=Count('votes')
    ).filter(total_votes__gt=0).order_by('-total_votes')[:10]
    
    context = {
        'monthly_stats': monthly_stats,
        'status_stats': status_stats,
        'category_stats': category_stats,
        'top_contributors': top_contributors,
        'top_voted_ideas': top_voted_ideas,
        'page_title': 'İdeya Bankı Analitikası'
    }
    
    return render(request, 'idea_bank/analytics.html', context)

def complex_function_1(request):
    """Karmaşık funksiyanın birinci hissəsi (hələ implementasiya olunmayıb)"""
    # TODO: Implement functionality or remove if unused
    raise NotImplementedError("complex_function_1 is not implemented yet")

def complex_function_2(request):
    """Karmaşık funksiyanın ikinci hissəsi (hələ implementasiya olunmayıb)"""
    # TODO: Implement functionality or remove if unused
    raise NotImplementedError("complex_function_2 is not implemented yet")