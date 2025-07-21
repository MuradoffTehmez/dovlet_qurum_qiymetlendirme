"""
Self-review (Öz-özünə Qiymətləndirmə) Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from core.models import (
    QiymetlendirmeDovru, Qiymetlendirme, Cavab, Sual, 
    SualKateqoriyasi, Notification
)
from core.permissions import require_role

SELF_REVIEW_EDIT = 'self_review:edit'


@login_required
@require_role(['ISHCHI', 'REHBER', 'ADMIN', 'SUPERADMIN'])
def self_review_dashboard(request):
    """Self-review dashboard - öz qiymətləndirmələrinin siyahısı"""
    
    # Aktiv dövrləri tap
    active_cycles = QiymetlendirmeDovru.objects.filter(
        aktivdir=True,
        bashlama_tarixi__lte=timezone.now().date(),
        bitme_tarixi__gte=timezone.now().date()
    )
    
    # İstifadəçinin self-review qiymətləndirmələri
    self_reviews = Qiymetlendirme.objects.filter(
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW,
        dovr__in=active_cycles
    ).select_related('dovr').order_by('-yaradilma_tarixi')
    
    # Keçmiş self-review qiymətləndirmələri
    past_self_reviews = Qiymetlendirme.objects.filter(
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW,
        status=Qiymetlendime.Status.TAMAMLANDI
    ).select_related('dovr').order_by('-tamamlanma_tarixi')[:5]
    
    # Aktiv dövrlərdə self-review yaratılmamış olanları tap
    missing_self_reviews = []
    for cycle in active_cycles:
        existing_review = self_reviews.filter(dovr=cycle).first()
        if not existing_review:
            missing_self_reviews.append(cycle)
    
    context = {
        'active_cycles': active_cycles,
        'self_reviews': self_reviews,
        'past_self_reviews': past_self_reviews,
        'missing_self_reviews': missing_self_reviews,
        'page_title': 'Öz-özünə Qiymətləndirmə'
    }
    
    return render(request, 'self_review/dashboard.html', context)


@login_required
@require_role(['ISHCHI', 'REHBER', 'ADMIN', 'SUPERADMIN'])
def create_self_review(request, cycle_id):
    """Yeni self-review yaratma"""
    
    cycle = get_object_or_404(QiymetlendirmeDovru, id=cycle_id, aktivdir=True)
    
    # Artıq self-review olub olmadığını yoxla
    existing_review = Qiymetlendirme.objects.filter(
        dovr=cycle,
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW
    ).first()
    
    if existing_review:
        messages.warning(request, f"{cycle.ad} dövrü üçün self-review artıq mövcuddur.")
        return redirect(SELF_REVIEW_EDIT, review_id=existing_review.id)
    
    # Yeni self-review yarat
    try:
        with transaction.atomic():
            new_review = Qiymetlendirme.objects.create(
                dovr=cycle,
                qiymetlendirilen=request.user,
                qiymetlendiren=request.user,
                qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW,
                status=Qiymetlendime.Status.GOZLEMEDE
            )
            
            # Bildiriş yarat
            Notification.create_notification(
                recipient=request.user,
                title="Yeni Self-Review Yaradıldı",
                message=f"{cycle.ad} dövrü üçün öz-özünə qiymətləndirmə yaradıldı.",
                notification_type=Notification.NotificationType.TASK_ASSIGNED,
                priority=Notification.Priority.MEDIUM,
                action_url=f"/self-review/{new_review.id}/edit/",
                action_text="Qiymətləndirməni Başla"
            )
            
            messages.success(request, f"{cycle.ad} dövrü üçün self-review uğurla yaradıldı.")
            return redirect(SELF_REVIEW_EDIT, review_id=new_review.id)
            
    except Exception as e:
        messages.error(request, f"Self-review yaradılarkən xəta baş verdi: {str(e)}")
        return redirect('self_review:dashboard')


@login_required 
@require_role(['ISHCHI', 'REHBER', 'ADMIN', 'SUPERADMIN'])
def edit_self_review(request, review_id):
    """Self-review redaktə etmə"""
    
    review = get_object_or_404(
        Qiymetlendirme,
        id=review_id,
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW
    )
    
    # Sualları kategoriyalara görə qrupla
    categories = SualKateqoriyasi.objects.all()
    questions_by_category = {}
    
    for category in categories:
        questions = Sual.objects.filter(
            kateqoriya=category,
            applicable_to__in=['all', 'employee']
        ).order_by('id')
        
        # Mövcud cavabları əlavə et
        questions_with_answers = []
        for question in questions:
            existing_answer = Cavab.objects.filter(
                qiymetlendirme=review,
                sual=question
            ).first()
            
            questions_with_answers.append({
                'question': question,
                'answer': existing_answer
            })
        
        if questions_with_answers:
            questions_by_category[category] = questions_with_answers
    
    # Tamamlanma faizi
    completion_percentage = review.get_completion_percentage()
    
    context = {
        'review': review,
        'questions_by_category': questions_by_category,
        'completion_percentage': completion_percentage,
        'page_title': f'Self-Review: {review.dovr.ad}'
    }
    
    return render(request, 'self_review/edit.html', context)


@login_required
@require_http_methods(["POST"])
def save_answer(request, review_id):
    """AJAX ilə cavab saxlama"""
    
    review = get_object_or_404(
        Qiymetlendirme,
        id=review_id,
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW,
        status=Qiymetlendime.Status.GOZLEMEDE
    )
    
    question_id = request.POST.get('question_id')
    score = request.POST.get('score')
    comment = request.POST.get('comment', '')
    
    try:
        question = get_object_or_404(Sual, id=question_id)
        
        # Balı yoxla
        score = int(score)
        if not (1 <= score <= 10):
            return JsonResponse({
                'success': False,
                'error': 'Bal 1 ilə 10 arasında olmalıdır'
            })
        
        # Cavabı yarat və ya yenilə
        _, created = Cavab.objects.update_or_create(
            qiymetlendirme=review,
            sual=question,
            defaults={
                'xal': score,
                'metnli_rey': comment
            }
        )
        
        # Tamamlanma faizini yenilə
        completion_percentage = review.get_completion_percentage()
        
        return JsonResponse({
            'success': True,
            'message': 'Cavab saxlanıldı' if not created else 'Cavab yaradıldı',
            'completion_percentage': completion_percentage
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Yanlış bal dəyəri'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Xəta baş verdi: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def complete_self_review(request, review_id):
    """Self-review tamamlama"""
    
    review = get_object_or_404(
        Qiymetlendirme,
        id=review_id,
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW,
        status=Qiymetlendime.Status.GOZLEMEDE
    )
    
    # Bütün sualların cavablandığını yoxla
    total_questions = Sual.objects.filter(
        applicable_to__in=['all', 'employee']
    ).count()
    
    answered_questions = review.cavablar.count()
    
    if answered_questions < total_questions:
        missing_count = total_questions - answered_questions
        messages.error(
            request, 
            f"Self-review tamamlanmadan əvvəl {missing_count} sual daha cavablandırılmalıdır."
        )
        return redirect('self_review:edit', review_id=review.id)
    
    try:
        with transaction.atomic():
            # Review-ı tamamla
            review.status = Qiymetlendirme.Status.TAMAMLANDI
            review.tamamlanma_tarixi = timezone.now()
            review.save()
            
            # Bildiriş yarat
            Notification.create_notification(
                recipient=request.user,
                title="Self-Review Tamamlandı",
                message=f"{review.dovr.ad} dövrü üçün öz-özünə qiymətləndirmə uğurla tamamlandı.",
                notification_type=Notification.NotificationType.EVALUATION_COMPLETED,
                priority=Notification.Priority.MEDIUM,
                action_url=f"/self-review/{review.id}/view/",
                action_text="Nəticələri Görüntülə"
            )
            
            # Rəhbərə də bildiriş göndər (əgər varsa)
            if hasattr(request.user, 'organization_unit') and request.user.organization_unit:
                managers = request.user.organization_unit.ishchiler.filter(
                    rol__in=['REHBER', 'ADMIN']
                ).exclude(id=request.user.id)
                
                for manager in managers:
                    Notification.create_notification(
                        recipient=manager,
                        title="İşçi Self-Review Tamamladı",
                        message=f"{request.user.get_full_name()} öz-özünə qiymətləndirməni tamamladı.",
                        notification_type=Notification.NotificationType.EVALUATION_COMPLETED,
                        priority=Notification.Priority.LOW,
                        action_url=f"/self-review/{review.id}/view/",
                        action_text="Nəticələri Görüntülə"
                    )
            
            messages.success(request, "Self-review uğurla tamamlandı!")
            return redirect('self_review:view', review_id=review.id)
            
    except Exception as e:
        messages.error(request, f"Self-review tamamlanarkən xəta: {str(e)}")
        return redirect('self_review:edit', review_id=review.id)


@login_required
def view_self_review(request, review_id):
    """Tamamlanmış self-review görüntüləmə"""
    
    review = get_object_or_404(
        Qiymetlendirme,
        id=review_id,
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW
    )
    
    # Cavabları kategoriyalara görə qrupla
    categories = SualKateqoriyasi.objects.all()
    results_by_category = {}
    
    for category in categories:
        answers = Cavab.objects.filter(
            qiymetlendirme=review,
            sual__kateqoriya=category
        ).select_related('sual').order_by('sual__id')
        
        if answers.exists():
            category_avg = sum(answer.xal for answer in answers) / answers.count()
            results_by_category[category] = {
                'answers': answers,
                'average_score': round(category_avg, 2),
                'total_answers': answers.count()
            }
    
    # Ümumi ortalama
    overall_average = review.calculate_average_score()
    
    context = {
        'review': review,
        'results_by_category': results_by_category,
        'overall_average': overall_average,
        'page_title': f'Self-Review Nəticələri: {review.dovr.ad}'
    }
    
    return render(request, 'self_review/view.html', context)


@login_required
def self_review_analytics(request):
    """Self-review analitika və trendlər"""
    
    # İstifadəçinin bütün tamamlanmış self-reviewları
    completed_reviews = Qiymetlendirme.objects.filter(
        qiymetlendirilen=request.user,
        qiymetlendiren=request.user,
        qiymetlendirme_novu=Qiymetlendime.QiymetlendirmeNovu.SELF_REVIEW,
        status=Qiymetlendime.Status.TAMAMLANDI
    ).select_related('dovr').order_by('dovr__bashlama_tarixi')
    
    # Zaman üzrə trend
    trend_data = []
    for review in completed_reviews:
        trend_data.append({
            'cycle': review.dovr.ad,
            'date': review.dovr.bashlama_tarixi,
            'average_score': review.calculate_average_score()
        })
    
    # Kategoriya üzrə analiz (son review)
    category_analysis = {}
    if completed_reviews.exists():
        latest_review = completed_reviews.last()
        
        for category in SualKateqoriyasi.objects.all():
            answers = Cavab.objects.filter(
                qiymetlendirme=latest_review,
                sual__kateqoriya=category
            )
            
            if answers.exists():
                avg_score = sum(answer.xal for answer in answers) / answers.count()
                category_analysis[category.ad] = round(avg_score, 2)
    
    context = {
        'completed_reviews': completed_reviews,
        'trend_data': trend_data,
        'category_analysis': category_analysis,
        'page_title': 'Self-Review Analitika'
    }
    
    return render(request, 'self_review/analytics.html', context)