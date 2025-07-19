# core/urls/__init__.py

from django.urls import path, include

from .. import views
from .. import notification_views
from .. import report_views
from .. import calendar_views
from .. import dashboard_views

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
    
    # === GAP ANALYSIS URL-LƏRİ ===
    path("gap-analysis/", include('core.urls.gap_analysis')),
    
    # === PERFORMANCE TRENDS URL-LƏRİ ===
    path("performance-trends/", include('core.urls.performance_trends')),
    
    # === PARTICIPATION MONITORING URL-LƏRİ ===
    path("participation/", include('core.urls.participation_monitoring')),
    
    # === QUICK FEEDBACK URL-LƏRİ ===
    path("quick-feedback/", include('core.urls.quick_feedback')),
    
    # === PRIVATE NOTES URL-LƏRİ ===
    path("private-notes/", include('core.urls.private_notes')),
]