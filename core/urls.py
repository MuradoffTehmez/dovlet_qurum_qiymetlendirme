# core/urls.py - Updated for URL resolution fix

from django.urls import path, include

from . import views
from . import notification_views
from . import report_views
from . import calendar_views
from . import dashboard_views
from . import ai_risk_views
from . import training_views
from . import performance_views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("qeydiyyat/", views.qeydiyyat_sehifesi, name="qeydiyyat"),
    path(
        "qiymetlendir/<int:qiymetlendirme_id>/",
        views.qiymetlendirme_etmek,
        name="qiymetlendirme_etmek",
    ),
    # Yeni ortaq hesabat URL-ləri
    path("hesabatim/", views.hesabat_gorunumu, name="hesabatim"),
    path("hesabat/bax/<int:ishchi_id>/", views.hesabat_gorunumu, name="hesabat_bax"),
    path(
        "hesabat/pdf/<int:ishchi_id>/",
        views.hesabat_pdf_yukle,
        name="hesabat_pdf_yukle",
    ),
    path("profil/", views.ProfileView.as_view(), name="profil"),
    # Rəhbər və Superadmin panelləri
    path("rehber-paneli/", views.rehber_paneli, name="rehber_paneli"),
    path("superadmin/", views.superadmin_paneli, name="superadmin_paneli"),
    path("superadmin/yeni-dovr/", views.yeni_dovr_yarat, name="yeni_dovr_yarat"),
    path(
        "superadmin/export-excel/",
        views.export_departments_excel,
        name="export_departments_excel",
    ),
    path(
        "superadmin/export-pdf/",
        views.export_departments_pdf,
        name="export_departments_pdf",
    ),
    path(
        "plan/yarat/<int:ishchi_id>/<int:dovr_id>/",
        views.plan_yarat_ve_redakte_et,
        name="plan_yarat",
    ),
    path("plan/bax/<int:plan_id>/", views.plan_bax, name="plan_bax"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    
    # === BİLDİRİŞ SİSTEMİ URL-LƏRİ ===
    path("bildirisler/", 
         include([
             path("", notification_views.notification_center, name="notification_center"),
             path("api/", notification_views.notification_api, name="notification_api"),
             path("oxu/<int:notification_id>/", notification_views.mark_notification_read, name="mark_notification_read"),
             path("hamisi-oxu/", notification_views.mark_all_notifications_read, name="mark_all_notifications_read"),
             path("arxiv/<int:notification_id>/", notification_views.archive_notification, name="archive_notification"),
             path("detal/<int:notification_id>/", notification_views.notification_detail, name="notification_detail"),
             path("tenzimlemeler/", notification_views.notification_preferences, name="notification_preferences"),
         ])
    ),
    
    # === ADMİN BİLDİRİŞ URL-LƏRİ ===
    path("admin-bildirisler/",
         include([
             path("dashboard/", notification_views.admin_notification_dashboard, name="admin_notification_dashboard"),
             path("toplu-gonder/", notification_views.send_bulk_notification, name="send_bulk_notification"),
         ])
    ),
    
    # === HESABAT MƏRKƏZİ URL-LƏRİ ===
    path("hesabatlar/",
         include([
             path("", report_views.report_center, name="report_center"),
             path("generate/<str:report_type>/", report_views.generate_report, name="generate_report"),
             path("preview/<str:report_type>/", report_views.report_preview, name="report_preview"),
             path("schedule/", report_views.schedule_report, name="schedule_report"),
             path("analytics/", report_views.report_analytics, name="report_analytics"),
             path("sample/<str:report_type>/", report_views.download_sample_report, name="download_sample_report"),
             path("settings/", report_views.report_settings, name="report_settings"),
         ])
    ),
    
    # === TƏQVİM SİSTEMİ URL-LƏRİ ===
    path("teqvim/",
         include([
             path("", calendar_views.calendar_view, name="calendar_view"),
             path("api/events/", calendar_views.calendar_events_api, name="calendar_events_api"),
             path("api/stats/", calendar_views.calendar_stats, name="calendar_stats"),
             path("api/reminder/", calendar_views.create_reminder, name="create_reminder"),
             path("api/event/create/", calendar_views.create_event, name="create_event"),
             path("api/event/update/<int:event_id>/", calendar_views.update_event, name="update_event"),
             path("api/event/delete/<int:event_id>/", calendar_views.delete_event, name="delete_event"),
             path("api/event/form/", calendar_views.event_form_modal, name="event_form_modal"),
             path("api/event/form/<int:event_id>/", calendar_views.event_form_modal, name="event_form_modal_edit"),
             path("event-detail/<str:event_type>/<int:event_id>/", calendar_views.event_detail, name="event_detail"),
         ])
    ),
    
    # === İNTERAKTİV DASHBOARD URL-LƏRİ ===
    path("interactive-dashboard/",
         include([
             path("", dashboard_views.interactive_dashboard, name="interactive_dashboard"),
             path("api/stats/", dashboard_views.dashboard_stats_api, name="dashboard_stats_api"),
             path("api/chart/", dashboard_views.performance_chart_api, name="performance_chart_api"),
             path("api/widget/<str:widget_type>/", dashboard_views.dashboard_widget_data, name="dashboard_widget_data"),
             path("api/preferences/", dashboard_views.dashboard_widget_preferences, name="dashboard_widget_preferences"),
         ])
    ),
    
    # === SELF-REVIEW URL-LƏRİ ===
    path("self-review/", include('core.urls.self_review')),
    
    # === AI RİSK DETECTION URL-LƏRİ ===
    path("ai-risk/", ai_risk_views.ai_risk_dashboard, name="ai_risk_dashboard"),
    path("ai-risk/dashboard/", ai_risk_views.ai_risk_dashboard_api, name="ai_risk_dashboard_api"),
    path("ai-risk/trends/", ai_risk_views.ai_risk_trends_api, name="ai_risk_trends_api"),
    path("ai-risk/risk-flags/", ai_risk_views.risk_flags_management, name="risk_flags_management"),
    path("ai-risk/psychological-surveys/", ai_risk_views.psychological_surveys, name="psychological_surveys"),
    path("ai-risk/strategic-hr-planning/", ai_risk_views.strategic_hr_planning, name="strategic_hr_planning"),
    
    # AI Risk Analysis API endpoints
    path("api/ai-risk-detection/dashboard/", ai_risk_views.ai_risk_dashboard_api, name="api_ai_risk_dashboard"),
    path("api/ai-risk-detection/trends/", ai_risk_views.ai_risk_trends_api, name="api_ai_risk_trends"),
    path("api/ai-risk-detection/run-analysis/", ai_risk_views.run_ai_risk_analysis_api, name="api_run_ai_risk_analysis"),
    
    # Psychological Surveys API
    path("api/v1/psych-surveys/statistics/", ai_risk_views.psychological_surveys_api, name="api_psych_surveys_stats"),
    
    # Strategic HR Planning API
    path("api/v1/strategic-hr/analyze/", ai_risk_views.strategic_hr_planning_api, name="api_strategic_hr_analyze"),
    
    # === TƏHSİL VƏ İNKİŞAF URL-LƏRİ ===
    path("training/", training_views.training_dashboard, name="training_dashboard"),
    path("training/programs/", training_views.training_programs, name="training_programs"),
    path("training/learning-path/", training_views.employee_learning_path, name="employee_learning_path"),
    path("training/skills-matrix/", training_views.skills_matrix, name="skills_matrix"),
    path("training/certifications/", training_views.certifications, name="certifications"),
    path("training/api/stats/", training_views.training_api_stats, name="training_api_stats"),
    path("training/api/skills/", training_views.skills_assessment_api, name="skills_assessment_api"),
    
    # === PERFORMANS İDARƏETMƏ URL-LƏRİ ===
    path("performance/", performance_views.performance_dashboard, name="performance_dashboard"),
    path("performance/analytics/", performance_views.performance_analytics, name="performance_analytics"),
    path("performance/goals/", performance_views.goal_management, name="goal_management"),
    path("performance/talent-review/", performance_views.talent_review, name="talent_review"),
    path("performance/career-development/", performance_views.career_development, name="career_development"),
    path("performance/api/stats/", performance_views.performance_api_stats, name="performance_api_stats"),
    path("performance/api/matrix/", performance_views.performance_matrix_api, name="performance_matrix_api"),
    path("performance/api/goals/", performance_views.goals_api, name="goals_api"),
    
    # === MƏRHƏLƏ 2 YENİ XÜSUSİYYƏTLƏR ===
    # Gap Analysis (Fərq Təhlili)
    path("gap-analysis/", include('core.urls.gap_analysis')),
    
    # Performance Trends (İnkişaf Trendi)
    path("performance-trends/", include('core.urls.performance_trends')),
    
    # Participation Monitoring (İştirak Nəzarəti)
    path("participation-monitoring/", include('core.urls.participation_monitoring')),
    
    # Quick Feedback (Sürətli Geri Bildirim)
    path("quick-feedback/", include('core.urls.quick_feedback')),
    
    # Private Notes (Məxfi Qeydlər)
    path("private-notes/", include('core.urls.private_notes')),
    
    # Idea Bank (İdeya Bankı)
    path("idea-bank/", include('core.urls.idea_bank')),
]
# Uncomment the following lines if you want to enable these views
# path('superadmin/dovrlar/', views.dovrlar_siyahisi, name='dovrlar_siyahisi'),
# path('superadmin/dovrlar/sil/<int:dovr_id>/', views.dovr_sil, name='dovr_sil'),
# path('superadmin/dovrlar/duzenle/<int:dovr_id>/', views.dovr_duzenle, name='dovr_duzenle'),
# path('superadmin/ishciler/', views.ishciler_siyahisi, name='ishciler_siyahisi'),
# path('superadmin/ishciler/sil/<int:ishchi_id>/', views.ishci_sil, name='ishci_sil'),
# path('superadmin/ishciler/duzenle/<int:ishchi_id>/', views.ishci_duzenle, name='ishci_duzenle'),
# path('superadmin/ishciler/yeni/', views.yeni_ishci_yarat, name='yeni_ishci_yarat'),
# path('superadmin/hesabatlar/', views.hesabatlar_siyahisi, name='hesabatlar_siyahisi'),
# path('superadmin/hesabatlar/sil/<int:hesabat_id>/', views.hesabat_sil, name='hesabat_sil'),
# path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/', views.hesabat_duzenle, name='hesabat_duzenle'),
# path('superadmin/hesabatlar/yeni/', views.yeni_hesabat_yarat, name='yeni_hesabat_yarat'),
# path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/', views.hesabat_pdf_duzenle, name='hesabat_pdf_duzenle'),
# path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/sil/', views.hesabat_pdf_sil, name='hesabat_pdf_sil'),
# path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/yukle/', views.hesabat_pdf_yukle, name='hesabat_pdf_yukle'),
# path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/duzenle/', views.hesabat_pdf_duzenle, name='hesabat_pdf_duzenle'),
# path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/yukle/', views.hesabat_pdf_yukle, name='hesabat_pdf_yukle'),
# path('superadmin/hesabatlar/duzenle/<int:hesabat_id>/pdf/sil/', views.hesabat_pdf_sil, name='hesabat_pdf_sil'),
