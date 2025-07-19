# core/api_views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    OrganizationUnit, Ishchi, SualKateqoriyasi, Sual,
    QiymetlendirmeDovru, Qiymetlendirme, InkishafPlani,
    Feedback, Notification, CalendarEvent, QuickFeedback,
    PrivateNote, Idea, IdeaCategory, IdeaComment, Cavab
)
from .serializers import (
    OrganizationUnitSerializer, IshchiSerializer, IshchiCreateSerializer,
    SualKateqoriyasiSerializer, SualSerializer, QiymetlendirmeDovruSerializer,
    QiymetlendirmeSerializer, QiymetlendirmeDetailSerializer,
    InkishafPlaniSerializer, FeedbackSerializer, NotificationSerializer,
    CalendarEventSerializer, QuickFeedbackSerializer, PrivateNoteSerializer,
    IdeaSerializer, IdeaDetailSerializer, IdeaCategorySerializer,
    UserProfileSerializer, ChangePasswordSerializer
)
from .api_permissions import IsOwnerOrReadOnly, IsManagerOrAdmin

User = get_user_model()


# --- Authentication Views ---
class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT token alınması üçün custom view"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data.get('username'))
            response.data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'rol': user.rol,
                'organization_unit': user.organization_unit.name if user.organization_unit else None
            }
        return response


# --- User Management Views ---
class IshchiViewSet(viewsets.ModelViewSet):
    queryset = Ishchi.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IshchiCreateSerializer
        return IshchiSerializer
    
    def get_queryset(self):
        queryset = Ishchi.objects.all()
        
        # Axtarış funksiyası
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Təşkilati vahidə görə filtr
        organization_unit = self.request.query_params.get('organization_unit', None)
        if organization_unit:
            queryset = queryset.filter(organization_unit=organization_unit)
        
        # Rola görə filtr
        rol = self.request.query_params.get('rol', None)
        if rol:
            queryset = queryset.filter(rol=rol)
        
        return queryset.select_related('organization_unit')
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Cari istifadəçinin profili"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Profil yeniləmə"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Şifrə dəyişdirmə"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Köhnə şifrə yanlışdır.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({'message': 'Şifrə uğurla dəyişdirildi.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Organization Structure Views ---
class OrganizationUnitViewSet(viewsets.ModelViewSet):
    queryset = OrganizationUnit.objects.all()
    serializer_class = OrganizationUnitSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Təşkilati vahidin alt vahidləri"""
        unit = self.get_object()
        children = unit.children.all()
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Təşkilati vahiddə işləyən əməkdaşlar"""
        unit = self.get_object()
        employees = unit.ishchiler.all()
        serializer = IshchiSerializer(employees, many=True)
        return Response(serializer.data)


# --- Questions Management Views ---
class SualKateqoriyasiViewSet(viewsets.ModelViewSet):
    queryset = SualKateqoriyasi.objects.all()
    serializer_class = SualKateqoriyasiSerializer
    permission_classes = [IsAuthenticated]


class SualViewSet(viewsets.ModelViewSet):
    queryset = Sual.objects.all()
    serializer_class = SualSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Sual.objects.all()
        
        # Kateqoriyaya görə filtr
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(kateqoriya=category)
        
        # Roluna görə filtr
        applicable_to = self.request.query_params.get('applicable_to', None)
        if applicable_to:
            queryset = queryset.filter(applicable_to=applicable_to)
        
        return queryset.select_related('kateqoriya', 'yaradan')


# --- Performance Management Views ---
class QiymetlendirmeDovruViewSet(viewsets.ModelViewSet):
    queryset = QiymetlendirmeDovru.objects.all()
    serializer_class = QiymetlendirmeDovruSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Aktiv qiymətləndirmə dövrü"""
        active_cycles = self.queryset.filter(aktivdir=True)
        serializer = self.get_serializer(active_cycles, many=True)
        return Response(serializer.data)


class QiymetlendirmeViewSet(viewsets.ModelViewSet):
    queryset = Qiymetlendirme.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QiymetlendirmeDetailSerializer
        return QiymetlendirmeSerializer
    
    def get_queryset(self):
        queryset = Qiymetlendirme.objects.all()
        
        # Yalnız istifadəçinin aid olduğu qiymətləndirmələr
        user = self.request.user
        if not user.rol in ['ADMIN', 'SUPERADMIN']:
            queryset = queryset.filter(
                Q(qiymetlendirilecek=user) | Q(qiymetlendiren=user)
            )
        
        # Dövrə görə filtr
        dovr = self.request.query_params.get('dovr', None)
        if dovr:
            queryset = queryset.filter(dovr=dovr)
        
        # Statusə görə filtr
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('qiymetlendirilecek', 'qiymetlendiren', 'dovr')
    
    @action(detail=False, methods=['get'])
    def my_evaluations(self, request):
        """Mənim qiymətləndirmələrim"""
        evaluations = self.queryset.filter(qiymetlendirilecek=request.user)
        serializer = self.get_serializer(evaluations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_evaluations(self, request):
        """Gözləyən qiymətləndirmələr"""
        pending = self.queryset.filter(
            qiymetlendiren=request.user,
            status='PENDING'
        )
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)


# --- Development Plans Views ---
class InkishafPlaniViewSet(viewsets.ModelViewSet):
    queryset = InkishafPlani.objects.all()
    serializer_class = InkishafPlaniSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = InkishafPlani.objects.all()
        
        # Yalnız öz planlarını görə bilər (admin xaric)
        user = self.request.user
        if not user.rol in ['ADMIN', 'SUPERADMIN']:
            queryset = queryset.filter(ishchi=user)
        
        return queryset.select_related('ishchi', 'dovr')


# --- Feedback Views ---
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Feedback.objects.all()
        
        # Yalnız göndərdiyi və aldığı rəylər
        user = self.request.user
        if not user.rol in ['ADMIN', 'SUPERADMIN']:
            queryset = queryset.filter(
                Q(gonderici=user) | Q(alici=user)
            )
        
        return queryset.select_related('gonderici', 'alici')
    
    def perform_create(self, serializer):
        serializer.save(gonderici=self.request.user)


# --- Notifications Views ---
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Bütün bildirişləri oxunmuş kimi işarələ"""
        self.get_queryset().update(is_read=True)
        return Response({'message': 'Bütün bildirişlər oxunmuş kimi işarələndi.'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Bildirişi oxunmuş kimi işarələ"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Bildiriş oxunmuş kimi işarələndi.'})


# --- Calendar Views ---
class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CalendarEvent.objects.all()
        
        # Tarix aralığına görə filtr
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.select_related('created_by')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# --- Quick Feedback Views ---
class QuickFeedbackViewSet(viewsets.ModelViewSet):
    queryset = QuickFeedback.objects.all()
    serializer_class = QuickFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = QuickFeedback.objects.all()
        
        # Yalnız göndərdiyi və aldığı feedback-lər
        user = self.request.user
        if not user.rol in ['ADMIN', 'SUPERADMIN']:
            queryset = queryset.filter(
                Q(from_user=user) | Q(to_user=user)
            )
        
        return queryset.select_related('from_user', 'to_user', 'category')
    
    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)


# --- Private Notes Views ---
class PrivateNoteViewSet(viewsets.ModelViewSet):
    queryset = PrivateNote.objects.all()
    serializer_class = PrivateNoteSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        # Yalnız öz qeydlərini görə bilər
        return PrivateNote.objects.filter(author=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# --- Idea Bank Views ---
class IdeaCategoryViewSet(viewsets.ModelViewSet):
    queryset = IdeaCategory.objects.all()
    serializer_class = IdeaCategorySerializer
    permission_classes = [IsAuthenticated]


class IdeaViewSet(viewsets.ModelViewSet):
    queryset = Idea.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IdeaDetailSerializer
        return IdeaSerializer
    
    def get_queryset(self):
        queryset = Idea.objects.all()
        
        # Kateqoriyaya görə filtr
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Statusə görə filtr
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('author', 'category').prefetch_related('comments', 'likes')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """İdeya bəyən"""
        idea = self.get_object()
        from .models import IdeaVote
        
        vote, created = IdeaVote.objects.get_or_create(
            idea=idea,
            user=request.user,
            defaults={'vote_type': 'LIKE'}
        )
        
        if not created:
            if vote.vote_type == 'LIKE':
                vote.delete()
                return Response({'message': 'Bəyənmə geri alındı.'})
            else:
                vote.vote_type = 'LIKE'
                vote.save()
        
        return Response({'message': 'İdeya bəyənildi.'})
    
    @action(detail=True, methods=['post'])
    def dislike(self, request, pk=None):
        """İdeya bəyənmə"""
        idea = self.get_object()
        from .models import IdeaVote
        
        vote, created = IdeaVote.objects.get_or_create(
            idea=idea,
            user=request.user,
            defaults={'vote_type': 'DISLIKE'}
        )
        
        if not created:
            if vote.vote_type == 'DISLIKE':
                vote.delete()
                return Response({'message': 'Bəyənməmə geri alındı.'})
            else:
                vote.vote_type = 'DISLIKE'
                vote.save()
        
        return Response({'message': 'İdeya bəyənilmədi.'})


# --- Dashboard & Analytics Views ---
class DashboardViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Ümumi statistika"""
        user = request.user
        
        # Əsas statistikalar
        stats = {
            'pending_evaluations': Qiymetlendirme.objects.filter(
                qiymetlendiren=user, status='PENDING'
            ).count(),
            'completed_evaluations': Qiymetlendirme.objects.filter(
                qiymetlendirilen=user, status='COMPLETED'
            ).count(),
            'unread_notifications': Notification.objects.filter(
                recipient=user, is_read=False
            ).count(),
            'quick_feedback_received': QuickFeedback.objects.filter(
                to_user=user
            ).count(),
            'ideas_submitted': Idea.objects.filter(author=user).count(),
        }
        
        # Admin/Manager üçün əlavə statistikalar
        if user.rol in ['ADMIN', 'SUPERADMIN', 'REHBER']:
            stats.update({
                'total_employees': Ishchi.objects.filter(is_active=True).count(),
                'active_cycles': QiymetlendirmeDovru.objects.filter(aktivdir=True).count(),
                'pending_evaluations_all': Qiymetlendirme.objects.filter(status='PENDING').count(),
            })
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def recent_activities(self, request):
        """Son fəaliyyətlər"""
        activities = []
        
        # Son qiymətləndirmələr
        recent_evaluations = Qiymetlendirme.objects.filter(
            Q(qiymetlendirilen=request.user) | Q(qiymetlendiren=request.user)
        ).order_by('-yaradilma_tarixi')[:5]
        
        for eval in recent_evaluations:
            activities.append({
                'type': 'evaluation',
                'title': f'Qiymətləndirmə: {eval.dovr.ad}',
                'date': eval.yaradilma_tarixi,
                'status': eval.status
            })
        
        # Son feedback-lər
        recent_feedback = QuickFeedback.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).order_by('-created_at')[:5]
        
        for feedback in recent_feedback:
            activities.append({
                'type': 'feedback',
                'title': f'Sürətli rəy: {feedback.category.name}',
                'date': feedback.created_at,
                'is_sender': feedback.sender == request.user
            })
        
        # Tarixə görə sırala
        activities = sorted(activities, key=lambda x: x['date'], reverse=True)[:10]
        
        return Response(activities)