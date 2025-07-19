# core/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .api_views import (
    CustomTokenObtainPairView, IshchiViewSet, OrganizationUnitViewSet,
    SualKateqoriyasiViewSet, SualViewSet, QiymetlendirmeDovruViewSet,
    QiymetlendirmeViewSet, InkishafPlaniViewSet, FeedbackViewSet,
    NotificationViewSet, CalendarEventViewSet, QuickFeedbackViewSet,
    PrivateNoteViewSet, IdeaCategoryViewSet, IdeaViewSet, DashboardViewSet
)

# Router yaradılması
router = DefaultRouter()

# ViewSet-ləri router-a qoşmaq
router.register(r'users', IshchiViewSet)
router.register(r'organization-units', OrganizationUnitViewSet)
router.register(r'question-categories', SualKateqoriyasiViewSet)
router.register(r'questions', SualViewSet)
router.register(r'evaluation-cycles', QiymetlendirmeDovruViewSet)
router.register(r'evaluations', QiymetlendirmeViewSet)
router.register(r'development-plans', InkishafPlaniViewSet)
router.register(r'feedback', FeedbackViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'calendar-events', CalendarEventViewSet)
router.register(r'quick-feedback', QuickFeedbackViewSet)
router.register(r'private-notes', PrivateNoteViewSet)
router.register(r'idea-categories', IdeaCategoryViewSet)
router.register(r'ideas', IdeaViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API routes
    path('', include(router.urls)),
]