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
from typing import List

from .models import (
    OrganizationUnit, Ishchi, SualKateqoriyasi, Sual,
    QiymetlendirmeDovru, Qiymetlendirme, InkishafPlani,
    Feedback, Notification, CalendarEvent, QuickFeedback,
    PrivateNote, Idea, IdeaCategory, IdeaComment, Cavab,
    RiskFlag, EmployeeRiskAnalysis, PsychologicalRiskSurvey, PsychologicalRiskResponse
)
from .serializers import (
    OrganizationUnitSerializer, IshchiSerializer, IshchiCreateSerializer,
    SualKateqoriyasiSerializer, SualSerializer, QiymetlendirmeDovruSerializer,
    QiymetlendirmeSerializer, QiymetlendirmeDetailSerializer,
    InkishafPlaniSerializer, FeedbackSerializer, NotificationSerializer,
    CalendarEventSerializer, QuickFeedbackSerializer, PrivateNoteSerializer,
    IdeaSerializer, IdeaDetailSerializer, IdeaCategorySerializer,
    UserProfileSerializer, ChangePasswordSerializer,
    RiskFlagSerializer, EmployeeRiskAnalysisSerializer,
    PsychologicalRiskSurveySerializer, PsychologicalRiskResponseSerializer,
    DashboardStatsSerializer, AIRiskAnalysisSerializer, StatisticalAnomalySerializer
)
from .api_permissions import IsOwnerOrReadOnly, IsManagerOrAdmin
from .i18n_utils import translation_manager

User = get_user_model()


# === INTERNATIONALIZATION API VIEWS ===

class TranslationAPIView(viewsets.ViewSet):
    """API for frontend translations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def get_translations(self, request, language=None):
        """Get translations for specific language"""
        lang_code = language or request.LANGUAGE_CODE
        translations = translation_manager.export_translations_json(lang_code)
        
        return Response({
            'language': lang_code,
            'translations': translations
        })
    
    @action(detail=False, methods=['get'])
    def get_language_info(self, request):
        """Get current language information"""
        from .i18n_utils import i18n_manager
        
        info = i18n_manager.get_language_info()
        return Response(info)
    
    @action(detail=False, methods=['post'])
    def switch_language(self, request):
        """Switch user language preference"""
        lang_code = request.data.get('language')
        
        if not lang_code:
            return Response({'error': 'Language code required'}, status=400)
        
        # Validate language
        from .i18n_utils import i18n_manager
        if not i18n_manager.is_valid_language(lang_code):
            return Response({'error': 'Invalid language code'}, status=400)
        
        # Update user preference if authenticated
        if request.user.is_authenticated:
            # You can add a preferred_language field to your User model
            # request.user.preferred_language = lang_code
            # request.user.save()
            pass
        
        # Update session
        request.session['django_language'] = lang_code
        
        return Response({
            'success': True,
            'language': lang_code,
            'redirect_url': f'/{lang_code}/'
        })

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
        """Şifrə dəyişdirmə"""s
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
                Q(qiymetlendirilen=user) | Q(qiymetlendiren=user)
            )
        
        # Dövrə görə filtr
        dovr = self.request.query_params.get('dovr', None)
        if dovr:
            queryset = queryset.filter(dovr=dovr)
        
        # Statusə görə filtr
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('qiymetlendirilen', 'qiymetlendiren', 'dovr')
    
    @action(detail=False, methods=['get'])
    def my_evaluations(self, request):
        """Mənim qiymətləndirmələrim"""
        evaluations = self.queryset.filter(qiymetlendirilen=request.user)
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
        user = self.request.user
        if not user.rol in ['ADMIN', 'SUPERADMIN']:
            queryset = queryset.filter(user=user)
        return queryset.select_related('user')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
            defaults={'vote_type': 'UPVOTE'}
        )
        
        if not created:
            if vote.vote_type == 'UPVOTE':
                vote.delete()
                return Response({'message': 'Bəyənmə geri alındı.'})
            else:
                vote.vote_type = 'UPVOTE'
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
            defaults={'vote_type': 'DOWNVOTE'}
        )
        
        if not created:
            if vote.vote_type == 'DOWNVOTE':
                vote.delete()
                return Response({'message': 'Bəyənməmə geri alındı.'})
            else:
                vote.vote_type = 'DOWNVOTE'
                vote.save()
        
        return Response({'message': 'İdeya bəyənilmədi.'})


# --- Dashboard & Analytics Views ---
class DashboardViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DashboardStatsSerializer
    
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
            Q(from_user=request.user) | Q(to_user=request.user)
        ).order_by('-created_at')[:5]
        
        for feedback in recent_feedback:
            activities.append({
                'type': 'feedback',
                'title': f'Sürətli rəy: {feedback.category.name}',
                'date': feedback.created_at,
                'is_sender': feedback.from_user == request.user
            })
        
        # Tarixə görə sırala
        activities = sorted(activities, key=lambda x: x['date'], reverse=True)[:10]
        
        return Response(activities)


# === AI RİSK ANALİZİ API VİEWS ===

class RiskFlagViewSet(viewsets.ModelViewSet):
    """Risk Bayraqlari API"""
    queryset = RiskFlag.objects.all()
    serializer_class = RiskFlagSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'cycle', 'flag_type', 'severity', 'status']
    search_fields = ['employee__first_name', 'employee__last_name', 'flag_type']
    ordering_fields = ['detected_at', 'severity', 'risk_score']
    ordering = ['-detected_at', '-severity']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # İşçilər yalnız öz risklərini görə bilər
        if self.request.user.rol == 'ISHCHI':
            queryset = queryset.filter(employee=self.request.user)
        
        # Aktiv risklər filtri
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(status=RiskFlag.Status.ACTIVE)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Risk bayrağını həll edilmiş kimi işarələ"""
        risk_flag = self.get_object()
        action_taken = request.data.get('action_taken', '')
        
        risk_flag.resolve(request.user, action_taken)
        
        return Response({
            'status': 'resolved',
            'message': 'Risk bayrağı həll edildi'
        })
    
    @action(detail=True, methods=['post'])
    def ignore(self, request, pk=None):
        """Risk bayrağını rədd et"""
        risk_flag = self.get_object()
        reason = request.data.get('reason', '')
        
        risk_flag.ignore(request.user, reason)
        
        return Response({
            'status': 'ignored',
            'message': 'Risk bayrağı rədd edildi'
        })


class EmployeeRiskAnalysisViewSet(viewsets.ModelViewSet):
    """İşçi Risk Analizi API"""
    queryset = EmployeeRiskAnalysis.objects.all()
    serializer_class = EmployeeRiskAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'cycle', 'risk_level']
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering_fields = ['analyzed_at', 'total_risk_score', 'risk_level']
    ordering = ['-total_risk_score', '-analyzed_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # İşçilər yalnız öz analizlərini görə bilər
        if self.request.user.rol == 'ISHCHI':
            queryset = queryset.filter(employee=self.request.user)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def analyze_employee(self, request):
        """Müəyyən işçi üçün risk analizi apar"""
        from .ai_risk_detection import AIRiskDetector
        
        employee_id = request.data.get('employee_id')
        cycle_id = request.data.get('cycle_id')
        
        if not employee_id:
            return Response({'error': 'employee_id tələb olunur'}, status=400)
        
        try:
            employee = Ishchi.objects.get(id=employee_id)
            cycle = None
            if cycle_id:
                cycle = QiymetlendirmeDovru.objects.get(id=cycle_id)
            
            detector = AIRiskDetector()
            risk_data = detector.analyze_employee_risks(employee, cycle)
            
            # Risk analizi nəticəsini saxla
            if 'error' not in risk_data:
                analysis, created = EmployeeRiskAnalysis.objects.update_or_create(
                    employee=employee,
                    cycle=cycle or QiymetlendirmeDovru.objects.filter(aktivdir=True).first(),
                    defaults={
                        'total_risk_score': risk_data['total_risk_score'],
                        'risk_level': risk_data['risk_level'],
                        'performance_risk_score': risk_data['detailed_analysis']['performance_risk']['risk_score'],
                        'consistency_risk_score': risk_data['detailed_analysis']['consistency_risk']['risk_score'],
                        'peer_feedback_risk_score': risk_data['detailed_analysis']['peer_feedback_risk']['risk_score'],
                        'behavioral_risk_score': risk_data['detailed_analysis']['behavioral_risk']['risk_score'],
                        'detailed_analysis': risk_data['detailed_analysis'],
                    }
                )
                
                # Red Flag-ları saxla
                for flag_type in risk_data['red_flags']:
                    RiskFlag.objects.get_or_create(
                        employee=employee,
                        cycle=cycle or QiymetlendirmeDovru.objects.filter(aktivdir=True).first(),
                        flag_type=flag_type,
                        defaults={
                            'severity': RiskFlag.Severity.HIGH if risk_data['risk_level'] in ['HIGH', 'CRITICAL'] else RiskFlag.Severity.MEDIUM,
                            'risk_score': risk_data['total_risk_score'],
                            'details': risk_data['detailed_analysis'],
                            'ai_confidence': 0.85
                        }
                    )
            
            return Response(risk_data)
            
        except Ishchi.DoesNotExist:
            return Response({'error': 'İşçi tapılmadı'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def bulk_analyze(self, request):
        """Bütün işçilər üçün risk analizi"""
        from .ai_risk_detection import AIRiskDetector
        
        cycle_id = request.data.get('cycle_id')
        cycle = None
        if cycle_id:
            try:
                cycle = QiymetlendirmeDovru.objects.get(id=cycle_id)
            except QiymetlendirmeDovru.DoesNotExist:
                return Response({'error': 'Dövr tapılmadı'}, status=404)
        
        detector = AIRiskDetector()
        results = detector.bulk_analyze_all_employees(cycle)
        
        return Response({
            'total_analyzed': len(results),
            'results': results[:10],  # İlk 10 nəticəni qaytar
            'summary': detector.get_organization_risk_summary()
        })


class PsychologicalRiskSurveyViewSet(viewsets.ModelViewSet):
    """Psixoloji Risk Sorğuları API"""
    queryset = PsychologicalRiskSurvey.objects.all()
    serializer_class = PsychologicalRiskSurveySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['survey_type', 'is_active', 'is_anonymous']
    search_fields = ['title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # İşçilər yalnız aktiv sorğuları görə bilər
        if self.request.user.rol == 'ISHCHI':
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_default_surveys(self, request):
        """Standart psixoloji sorğuları yaradır"""
        from .psychological_surveys import PsychologicalSurveyManager
        
        # Yalnız admin və superadmin yarada bilər
        if request.user.rol not in ['ADMIN', 'SUPERADMIN']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        manager = PsychologicalSurveyManager()
        surveys = manager.create_default_surveys(request.user)
        
        serialized_surveys = PsychologicalRiskSurveySerializer(surveys, many=True)
        
        return Response({
            'created_surveys': len(surveys),
            'surveys': serialized_surveys.data,
            'message': f'{len(surveys)} yeni sorğu yaradıldı' if surveys else 'Bütün standart sorğular artıq mövcuddur'
        })
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Sorğu analitik məlumatları"""
        from .psychological_surveys import PsychologicalSurveyManager
        
        survey = self.get_object()
        manager = PsychologicalSurveyManager()
        analytics = manager.get_survey_analytics(survey)
        
        return Response(analytics)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Sorğunu kopyalayır"""
        if request.user.rol not in ['ADMIN', 'SUPERADMIN']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        original_survey = self.get_object()
        new_title = request.data.get('title', f"{original_survey.title} (Kopya)")
        
        # Yeni sorğu yarad
        new_survey = PsychologicalRiskSurvey.objects.create(
            title=new_title,
            survey_type=original_survey.survey_type,
            questions=original_survey.questions,
            scoring_method=original_survey.scoring_method,
            risk_thresholds=original_survey.risk_thresholds,
            is_active=False,  # Kopya deaktiv başlayır
            is_anonymous=original_survey.is_anonymous,
            created_by=request.user
        )
        
        serializer = PsychologicalRiskSurveySerializer(new_survey)
        return Response(serializer.data)


class PsychologicalRiskResponseViewSet(viewsets.ModelViewSet):
    """Psixoloji Risk Cavabları API"""
    queryset = PsychologicalRiskResponse.objects.all()
    serializer_class = PsychologicalRiskResponseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['survey', 'risk_level', 'requires_attention']
    ordering = ['-responded_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # İşçilər yalnız öz cavablarını görə bilər
        if self.request.user.rol == 'ISHCHI':
            queryset = queryset.filter(employee=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        from .psychological_surveys import PsychologicalSurveyManager
        
        survey = serializer.validated_data['survey']
        answers = serializer.validated_data['answers']
        
        # Xalı hesabla
        manager = PsychologicalSurveyManager()
        calculated_score = manager.calculate_survey_score(survey, answers)
        
        response = serializer.save(
            employee=self.request.user,
            total_score=calculated_score
        )
        
        # Risk səviyyəsini hesabla
        risk_level = response.calculate_risk_level()
        response.risk_level = risk_level
        
        # Yüksək risk halında diqqət tələb edir
        if risk_level in ['HIGH', 'VERY_HIGH']:
            response.requires_attention = True
        
        response.save()
    
    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        """Cavab analizi və tövsiyələr"""
        from .psychological_surveys import PsychologicalSurveyManager
        
        response = self.get_object()
        
        # Yalnız öz cavabını və ya admin/manager-lar görə bilər
        if response.employee != request.user and request.user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        manager = PsychologicalSurveyManager()
        analysis = manager.analyze_survey_response(response)
        
        return Response(analysis)


class AIRiskDetectionViewSet(viewsets.ViewSet):
    """AI Risk Detection əməliyyatları"""
    permission_classes = [IsAuthenticated]
    serializer_class = AIRiskAnalysisSerializer
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Risk analizi dashboard məlumatları"""
        
        # Aktiv dövr
        active_cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        if not active_cycle:
            return Response({'error': 'Aktiv dövr tapılmadı'}, status=404)
        
        # Risk statistikaları
        risk_stats = {
            'total_flags': RiskFlag.objects.filter(cycle=active_cycle).count(),
            'active_flags': RiskFlag.objects.filter(cycle=active_cycle, status=RiskFlag.Status.ACTIVE).count(),
            'critical_flags': RiskFlag.objects.filter(
                cycle=active_cycle, 
                severity=RiskFlag.Severity.CRITICAL,
                status=RiskFlag.Status.ACTIVE
            ).count(),
            'high_risk_employees': EmployeeRiskAnalysis.objects.filter(
                cycle=active_cycle,
                risk_level__in=['HIGH', 'CRITICAL']
            ).count(),
        }
        
        # Risk səviyyəsi paylanması
        risk_distribution = EmployeeRiskAnalysis.objects.filter(cycle=active_cycle).values('risk_level').annotate(
            count=Count('id')
        )
        
        # Son risk analizi
        recent_analyses = EmployeeRiskAnalysis.objects.filter(
            cycle=active_cycle
        ).order_by('-analyzed_at')[:5]
        
        # Ən çox rastlanan risk növləri
        common_flags = RiskFlag.objects.filter(
            cycle=active_cycle,
            status=RiskFlag.Status.ACTIVE
        ).values('flag_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'cycle': active_cycle.ad,
            'stats': risk_stats,
            'risk_distribution': list(risk_distribution),
            'recent_analyses': EmployeeRiskAnalysisSerializer(recent_analyses, many=True).data,
            'common_flags': list(common_flags)
        })
    
    @action(detail=False, methods=['get'])
    def organization_summary(self, request):
        """Təşkilat üçün ümumi risk xülasəsi"""
        from .ai_risk_detection import AIRiskDetector
        
        detector = AIRiskDetector()
        summary = detector.get_organization_risk_summary()
        
        return Response(summary)


# === STATİSTİK ANOMALİ AŞKARLAMA API VİEWS ===

class StatisticalAnomalyViewSet(viewsets.ViewSet):
    """Statistik Anomaliy Aşkarlama əməliyyatları"""
    permission_classes = [IsAuthenticated]
    serializer_class = StatisticalAnomalySerializer
    
    @action(detail=False, methods=['post'])
    def detect_performance_anomalies(self, request):
        """Performans anomaliyalarını aşkarlayır"""
        from .statistical_anomaly_detection import StatisticalAnomalyDetector
        
        cycle_id = request.data.get('cycle_id')
        cycle = None
        if cycle_id:
            try:
                cycle = QiymetlendirmeDovru.objects.get(id=cycle_id)
            except QiymetlendirmeDovru.DoesNotExist:
                return Response({'error': 'Dövr tapılmadı'}, status=404)
        
        detector = StatisticalAnomalyDetector()
        results = detector.detect_performance_anomalies(cycle)
        
        return Response(results)
    
    @action(detail=False, methods=['post'])
    def detect_behavioral_anomalies(self, request):
        """Davranış anomaliyalarını aşkarlayır"""
        from .statistical_anomaly_detection import StatisticalAnomalyDetector
        
        days_back = request.data.get('days_back', 30)
        
        try:
            days_back = int(days_back)
            if days_back <= 0 or days_back > 365:
                days_back = 30
        except (ValueError, TypeError):
            days_back = 30
        
        detector = StatisticalAnomalyDetector()
        results = detector.detect_behavioral_anomalies(days_back)
        
        return Response(results)
    
    @action(detail=False, methods=['post'])
    def analyze_employee_trends(self, request):
        """Müəyyən işçinin zaman ərzində performans trendi"""
        from .statistical_anomaly_detection import StatisticalAnomalyDetector
        
        employee_id = request.data.get('employee_id')
        months_back = request.data.get('months_back', 6)
        
        if not employee_id:
            return Response({'error': 'employee_id tələb olunur'}, status=400)
        
        try:
            employee = Ishchi.objects.get(id=employee_id)
            months_back = int(months_back)
            if months_back <= 0 or months_back > 24:
                months_back = 6
        except Ishchi.DoesNotExist:
            return Response({'error': 'İşçi tapılmadı'}, status=404)
        except (ValueError, TypeError):
            months_back = 6
        
        detector = StatisticalAnomalyDetector()
        results = detector.detect_temporal_anomalies(employee, months_back)
        
        return Response(results)
    
    @action(detail=False, methods=['post'])
    def generate_full_report(self, request):
        """Tam anomaliy hesabatı yaradır"""
        from .statistical_anomaly_detection import StatisticalAnomalyDetector
        
        cycle_id = request.data.get('cycle_id')
        cycle = None
        if cycle_id:
            try:
                cycle = QiymetlendirmeDovru.objects.get(id=cycle_id)
            except QiymetlendirmeDovru.DoesNotExist:
                return Response({'error': 'Dövr tapılmadı'}, status=404)
        
        detector = StatisticalAnomalyDetector()
        report = detector.generate_anomaly_report(cycle)
        
        return Response(report)
    
    @action(detail=False, methods=['get'])
    def anomaly_statistics(self, request):
        """Anomaliy statistikaları"""
        
        # Aktiv dövr
        active_cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        if not active_cycle:
            return Response({'error': 'Aktiv dövr tapılmadı'}, status=404)
        
        # Statistik anomaliy bayraqlari
        stats = {
            'statistical_anomaly_flags': RiskFlag.objects.filter(
                cycle=active_cycle,
                flag_type__in=['STATISTICAL_ANOMALY', 'BEHAVIORAL_ANOMALY'],
                status=RiskFlag.Status.ACTIVE
            ).count(),
            'performance_anomalies': RiskFlag.objects.filter(
                cycle=active_cycle,
                flag_type='STATISTICAL_ANOMALY',
                status=RiskFlag.Status.ACTIVE
            ).count(),
            'behavioral_anomalies': RiskFlag.objects.filter(
                cycle=active_cycle,
                flag_type='BEHAVIORAL_ANOMALY',
                status=RiskFlag.Status.ACTIVE
            ).count(),
            'critical_anomalies': RiskFlag.objects.filter(
                cycle=active_cycle,
                flag_type__in=['STATISTICAL_ANOMALY', 'BEHAVIORAL_ANOMALY'],
                severity=RiskFlag.Severity.CRITICAL,
                status=RiskFlag.Status.ACTIVE
            ).count(),
        }
        
        # Ən çox anomaliy olan işçilər
        from django.db.models import Count
        top_anomaly_employees = RiskFlag.objects.filter(
            cycle=active_cycle,
            flag_type__in=['STATISTICAL_ANOMALY', 'BEHAVIORAL_ANOMALY'],
            status=RiskFlag.Status.ACTIVE
        ).values(
            'employee__id', 'employee__first_name', 'employee__last_name'
        ).annotate(
            anomaly_count=Count('id')
        ).order_by('-anomaly_count')[:10]
        
        # Anomaliy növlərinin paylanması
        anomaly_distribution = RiskFlag.objects.filter(
            cycle=active_cycle,
            flag_type__in=['STATISTICAL_ANOMALY', 'BEHAVIORAL_ANOMALY'],
            status=RiskFlag.Status.ACTIVE
        ).values('flag_type', 'severity').annotate(
            count=Count('id')
        )
        
        return Response({
            'cycle': active_cycle.ad,
            'statistics': stats,
            'top_anomaly_employees': list(top_anomaly_employees),
            'anomaly_distribution': list(anomaly_distribution),
            'analysis_date': timezone.now()
        })


# === STRATEJİ KADR PLANLAŞDIRMASI API VİEWS ===

class StrategicHRPlanningViewSet(viewsets.ViewSet):
    """Strateji HR planlaşdırma əməliyyatları"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def workforce_composition(self, request):
        """İş qüvvəsi tərkibi analizi"""
        from .strategic_hr_planning import StrategicHRPlanner
        
        # Yalnız admin və rəhbərlər görə bilər
        if request.user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        unit_id = request.data.get('organization_unit_id')
        unit = None
        if unit_id:
            try:
                unit = OrganizationUnit.objects.get(id=unit_id)
            except OrganizationUnit.DoesNotExist:
                return Response({'error': 'Təşkilati vahid tapılmadı'}, status=404)
        
        planner = StrategicHRPlanner()
        analysis = planner.analyze_workforce_composition(unit)
        
        return Response(analysis)
    
    @action(detail=False, methods=['post'])
    def high_potential_employees(self, request):
        """Yüksək potensial işçilər analizi"""
        from .strategic_hr_planning import StrategicHRPlanner
        
        if request.user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        cycle_id = request.data.get('cycle_id')
        cycle = None
        if cycle_id:
            try:
                cycle = QiymetlendirmeDovru.objects.get(id=cycle_id)
            except QiymetlendirmeDovru.DoesNotExist:
                return Response({'error': 'Dövr tapılmadı'}, status=404)
        
        planner = StrategicHRPlanner()
        analysis = planner.identify_high_potential_employees(cycle)
        
        return Response(analysis)
    
    @action(detail=False, methods=['post'])
    def succession_planning(self, request):
        """Varislik planlaşdırması"""
        from .strategic_hr_planning import StrategicHRPlanner
        
        if request.user.rol not in ['ADMIN', 'SUPERADMIN']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        unit_id = request.data.get('organization_unit_id')
        unit = None
        if unit_id:
            try:
                unit = OrganizationUnit.objects.get(id=unit_id)
            except OrganizationUnit.DoesNotExist:
                return Response({'error': 'Təşkilati vahid tapılmadı'}, status=404)
        
        planner = StrategicHRPlanner()
        succession_plan = planner.create_succession_plan(unit)
        
        return Response(succession_plan)
    
    @action(detail=False, methods=['get'])
    def talent_pipeline(self, request):
        """Talent pipeline analizi"""
        from .strategic_hr_planning import StrategicHRPlanner
        
        if request.user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        planner = StrategicHRPlanner()
        pipeline_analysis = planner.analyze_talent_pipeline()
        
        return Response(pipeline_analysis)
    
    @action(detail=False, methods=['post'])
    def hr_strategy_recommendations(self, request):
        """HR strategiyası tövsiyələri"""
        from .strategic_hr_planning import StrategicHRPlanner
        
        if request.user.rol not in ['ADMIN', 'SUPERADMIN']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        unit_id = request.data.get('organization_unit_id')
        unit = None
        if unit_id:
            try:
                unit = OrganizationUnit.objects.get(id=unit_id)
            except OrganizationUnit.DoesNotExist:
                return Response({'error': 'Təşkilati vahid tapılmadı'}, status=404)
        
        planner = StrategicHRPlanner()
        strategy = planner.generate_hr_strategy_recommendations(unit)
        
        return Response(strategy)
    
    @action(detail=False, methods=['get'])
    def dashboard_metrics(self, request):
        """Strateji HR dashboard məlumatları"""
        from .strategic_hr_planning import StrategicHRPlanner
        
        if request.user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        planner = StrategicHRPlanner()
        
        # Əsas metrikalar
        workforce = planner.analyze_workforce_composition()
        talent_pipeline = planner.analyze_talent_pipeline()
        high_potential = planner.identify_high_potential_employees()
        
        # Aktiv dövr üçün risk analizi
        active_cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        risk_metrics = {}
        if active_cycle:
            risk_metrics = {
                'high_risk_employees': EmployeeRiskAnalysis.objects.filter(
                    cycle=active_cycle,
                    risk_level__in=['HIGH', 'CRITICAL']
                ).count(),
                'active_flags': RiskFlag.objects.filter(
                    cycle=active_cycle,
                    status=RiskFlag.Status.ACTIVE
                ).count(),
                'retention_alerts': PsychologicalRiskResponse.objects.filter(
                    requires_attention=True
                ).count()
            }
        
        dashboard_data = {
            'overview': {
                'total_employees': workforce.get('total_employees', 0),
                'high_potential_count': high_potential.get('high_potential_count', 0),
                'succession_ready': high_potential.get('succession_ready_count', 0),
                'stars_count': talent_pipeline.get('pipeline_summary', {}).get('stars', {}).get('count', 0)
            },
            'talent_distribution': talent_pipeline.get('pipeline_summary', {}),
            'risk_metrics': risk_metrics,
            'workforce_demographics': workforce.get('demographics', {}),
            'key_insights': [
                f"{high_potential.get('high_potential_count', 0)} yüksək potensial işçi müəyyən edilib",
                f"{high_potential.get('succession_ready_count', 0)} işçi varislik üçün hazırdır",
                f"{talent_pipeline.get('pipeline_summary', {}).get('stars', {}).get('count', 0)} star performer mövcuddur"
            ],
            'last_updated': timezone.now()
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['post'])
    def employee_potential_assessment(self, request):
        """Müəyyən işçinin potensial qiymətləndirməsi"""
        from .strategic_hr_planning import StrategicHRPlanner
        
        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response({'error': 'employee_id tələb olunur'}, status=400)
        
        try:
            employee = Ishchi.objects.get(id=employee_id)
        except Ishchi.DoesNotExist:
            return Response({'error': 'İşçi tapılmadı'}, status=404)
        
        # Yalnız öz məlumatını və ya admin/manager-lar görə bilər
        if employee != request.user and request.user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']:
            return Response({'error': 'İcazə yoxdur'}, status=403)
        
        planner = StrategicHRPlanner()
        cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        
        if not cycle:
            return Response({'error': 'Aktiv dövr tapılmadı'}, status=404)
        
        # Potensial hesablama
        potential_score = planner._calculate_potential_score(employee, cycle)
        
        # Performans məlumatları
        performance_data = planner._get_employee_performance(employee, cycle)
        
        # 9-box grid mövqeyi
        if performance_data:
            grid_position = planner._determine_9box_position(
                performance_data['performance'], 
                potential_score
            )
        else:
            grid_position = 'insufficient_data'
        
        # Varislik hazırlığı
        retention_risk = planner._assess_retention_risk(employee, cycle)
        
        assessment = {
            'employee': {
                'id': employee.id,
                'name': employee.get_full_name(),
                'position': employee.vezife,
                'unit': employee.organization_unit.name if employee.organization_unit else 'N/A'
            },
            'scores': {
                'potential_score': round(potential_score, 2),
                'performance_score': round(performance_data['performance'], 2) if performance_data else 0,
                'retention_risk': round(retention_risk, 2)
            },
            'assessments': {
                'grid_position': grid_position,
                'is_high_potential': potential_score >= 4.0,
                'succession_readiness': planner._assess_succession_readiness(employee, employee.vezife)
            },
            'development_recommendations': self._get_development_recommendations(grid_position, potential_score),
            'analysis_date': timezone.now()
        }
        
        return Response(assessment)
    
    def _get_development_recommendations(self, grid_position: str, potential_score: float) -> List[str]:
        """Grid mövqeyinə əsasən inkişaf tövsiyələri"""
        recommendations_map = {
            'star': [
                'Stretch assignments və challenging projects verin',
                'Executive coaching proqramına daxil edin',
                'Cross-functional leadership rolları təklif edin'
            ],
            'future_leader': [
                'Leadership development proqramına qoşun',
                'Mentoring relationships qurun',
                'Strategic thinking skills inkişaf etdirin'
            ],
            'high_potential': [
                'Skill development opportunities yaradın',
                'Job rotation proqramlarına daxil edin',
                'Performance coaching dəstəyi verin'
            ],
            'solid_performer': [
                'Current role-da expertise dərinləşdirin',
                'Specialization opportunities axtarın',
                'Team leadership skills inkişaf etdirin'
            ],
            'developing': [
                'Fundamental skills training təmin edin',
                'Regular feedback və coaching',
                'Clear performance expectations qoyun'
            ],
            'underperformer': [
                'Performance improvement plan yaradın',
                'Intensive coaching və support',
                'Role fit assessment aparın'
            ]
        }
        
        return recommendations_map.get(grid_position, [
            'Professional development planı yaradın',
            'Skill assessment və gap analysis aparın',
            'Mentor təyin edin'
        ])