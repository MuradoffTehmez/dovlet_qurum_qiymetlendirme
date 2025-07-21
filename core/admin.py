from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Cavab, Ishchi, Qiymetlendirme, QiymetlendirmeDovru,
    Sual, SualKateqoriyasi, Hedef, InkishafPlani, OrganizationUnit,
    Notification, Feedback, CalendarEvent, RiskFlag, EmployeeRiskAnalysis,
    PsychologicalRiskSurvey, PsychologicalRiskResponse, QuickFeedback,
    PrivateNote, Idea, IdeaCategory, QuickFeedbackCategory
)

# --- Ishchi modeli üçün admin ---
@admin.register(Ishchi)
class IshchiHistoryAdmin(UserAdmin, SimpleHistoryAdmin):
    list_display = ("username", "first_name", "last_name", "rol", "organization_unit", "get_unit_type")
    list_filter = (
        "rol",
        "organization_unit__type",
        "organization_unit",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "first_name", "last_name", "email", "organization_unit__name")
    fieldsets = UserAdmin.fieldsets + (
        ("Təşkilati Məlumatlar", {"fields": ("rol", "vezife", "organization_unit", "elaqe_nomresi", "dogum_tarixi", "profil_sekli")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Təşkilati Məlumatlar", {"fields": ("rol", "vezife", "organization_unit")}),
    )
    
    def get_unit_type(self, obj):
        """İşçinin təşkilati vahidinin növünü göstərir"""
        if obj.organization_unit:
            return obj.organization_unit.get_type_display()
        return "—"
    get_unit_type.short_description = "Vahid Növü"


# --- Yeni Struktur Vahidi modeli üçün admin ---
@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(SimpleHistoryAdmin):
    list_display = ("name", "type", "parent", "get_hierarchy_level", "get_employees_count", "get_children_count")
    list_filter = ("type", "parent")
    search_fields = ("name",)
    ordering = ("type", "parent", "name")
    readonly_fields = ("get_full_path", "get_employees_count", "get_children_count")
    
    def get_hierarchy_level(self, obj):
        """Təşkilati vahidin hierarchiya səviyyəsini göstərir"""
        level = 0
        current = obj
        while current.parent:
            level += 1
            current = current.parent
        return "—" * level + f" (Səviyyə {level})"
    get_hierarchy_level.short_description = "Hierarchiya Səviyyəsi"
    
    def get_employees_count(self, obj):
        """Bu vahiddə işləyən əməkdaşların sayını göstərir"""
        return obj.get_employees_count()
    get_employees_count.short_description = "Əməkdaş Sayı"
    
    def get_children_count(self, obj):
        """Alt vahidlərin sayını göstərir"""
        return obj.get_children_count()
    get_children_count.short_description = "Alt Vahid Sayı"


# --- Sual hovuzu modelləri ---
@admin.register(Sual)
class SualAdmin(SimpleHistoryAdmin):
    list_display = ("metn", "kateqoriya", "yaradan")
    list_filter = ("kateqoriya", "applicable_to")
    search_fields = ("metn",)


@admin.register(SualKateqoriyasi)
class SualKateqoriyasiAdmin(SimpleHistoryAdmin):
    list_display = ("ad",)


# --- Qiymətləndirmə dövrləri ---
@admin.register(QiymetlendirmeDovru)
class QiymetlendirmeDovruAdmin(SimpleHistoryAdmin):
    list_display = ("ad", "bashlama_tarixi", "bitme_tarixi", "aktivdir")
    list_filter = ("aktivdir",)


class CavabInline(admin.TabularInline):
    model = Cavab
    extra = 0
    readonly_fields = ("sual", "xal", "metnli_rey")


@admin.register(Qiymetlendirme)
class QiymetlendirmeAdmin(SimpleHistoryAdmin):
    list_display = ("dovr", "qiymetlendirilen", "qiymetlendiren", "status", "get_unit_info")
    list_filter = (
        "dovr", 
        "status",
        "qiymetlendirilen__organization_unit__type",
        "qiymetlendirilen__organization_unit",
    )
    search_fields = (
        "qiymetlendirilen__username", 
        "qiymetlendiren__username",
        "qiymetlendirilen__first_name",
        "qiymetlendirilen__last_name",
        "qiymetlendirilen__organization_unit__name",
    )
    inlines = [CavabInline]
    
    def get_unit_info(self, obj):
        """Qiymətləndirməyə daxil olan işçinin təşkilati vahidini göstərir"""
        if obj.qiymetlendirilen.organization_unit:
            return f"{obj.qiymetlendirilen.organization_unit.name} ({obj.qiymetlendirilen.organization_unit.get_type_display()})"
        return "—"
    get_unit_info.short_description = "Təşkilati Vahid"


@admin.register(Cavab)
class CavabAdmin(SimpleHistoryAdmin):
    list_display = ("sual", "xal", "qiymetlendirme")
    search_fields = ("qiymetlendirme__qiymetlendirilen__username",)


# --- İnkişaf Planı və Hədəflər ---
class HedefInline(admin.TabularInline):
    model = Hedef
    extra = 1
    fields = ("tesvir", "son_tarix", "status")


@admin.register(InkishafPlani)
class InkishafPlaniAdmin(SimpleHistoryAdmin):
    list_display = ("ishchi", "dovr", "status", "yaradilma_tarixi", "get_ishchi_unit")
    list_filter = (
        "status", 
        "dovr",
        "ishchi__organization_unit__type",
        "ishchi__organization_unit",
    )
    search_fields = (
        "ishchi__username", 
        "ishchi__first_name", 
        "ishchi__last_name",
        "ishchi__organization_unit__name",
    )
    inlines = [HedefInline]
    
    def get_ishchi_unit(self, obj):
        """İşçinin təşkilati vahidini göstərir"""
        if obj.ishchi.organization_unit:
            return f"{obj.ishchi.organization_unit.name} ({obj.ishchi.organization_unit.get_type_display()})"
        return "—"
    get_ishchi_unit.short_description = "İşçinin Təşkilati Vahidi"


# === BİLDİRİŞ SİSTEMİ ADMİN ===

@admin.register(Notification)
class NotificationAdmin(SimpleHistoryAdmin):
    list_display = (
        'title', 'recipient', 'notification_type', 'priority', 
        'is_read', 'created_at', 'get_sender_name'
    )
    list_filter = (
        'notification_type', 'priority', 'is_read', 'is_archived',
        'created_at', 'recipient__organization_unit'
    )
    search_fields = ('title', 'message', 'recipient__username', 'recipient__first_name', 'recipient__last_name')
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Əsas Məlumatlar', {
            'fields': ('recipient', 'sender', 'title', 'message', 'notification_type', 'priority')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_archived')
        }),
        ('Əməliyyat', {
            'fields': ('action_url', 'action_text')
        }),
        ('Tarixlər', {
            'fields': ('created_at', 'expires_at')
        }),
        ('Əlavə Məlumatlar', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'archive_notifications']
    
    def get_sender_name(self, obj):
        return obj.sender.get_full_name() if obj.sender else "Sistem"
    get_sender_name.short_description = "Göndərən"
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} bildiriş oxunmuş kimi işarələndi.")
    mark_as_read.short_description = "Seçilmiş bildirişləri oxunmuş kimi işarələ"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} bildiriş oxunmamış kimi işarələndi.")
    mark_as_unread.short_description = "Seçilmiş bildirişləri oxunmamış kimi işarələ"
    
    def archive_notifications(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(request, f"{updated} bildiriş arxivləşdirildi.")
    archive_notifications.short_description = "Seçilmiş bildirişləri arxivləşdir"


# === AI RİSK TƏHLİLİ ADMİN ===

@admin.register(RiskFlag)
class RiskFlagAdmin(SimpleHistoryAdmin):
    list_display = (
        'employee', 'cycle', 'flag_type', 'severity', 'status', 
        'detected_at', 'get_resolver_name'
    )
    list_filter = (
        'flag_type', 'severity', 'status', 'detected_at', 'cycle',
        'employee__organization_unit'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'hr_notes', 'resolution_action'
    )
    readonly_fields = ('detected_at', 'resolved_at', 'ai_confidence')
    
    fieldsets = (
        ('Əsas Məlumatlar', {
            'fields': ('employee', 'cycle', 'flag_type', 'severity', 'status')
        }),
        ('Təfərrüatlar', {
            'fields': ('risk_score', 'details', 'ai_confidence')
        }),
        ('Həll', {
            'fields': ('resolved_by', 'hr_notes', 'resolution_action', 'resolved_at')
        }),
        ('Tarixlər', {
            'fields': ('detected_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_resolved', 'mark_as_investigating']
    
    def get_resolver_name(self, obj):
        return obj.resolved_by.get_full_name() if obj.resolved_by else "—"
    get_resolver_name.short_description = "Həll Edən"
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status=RiskFlag.Status.RESOLVED,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f"{updated} risk bayrağı həll edildi.")
    mark_as_resolved.short_description = "Seçilmiş risk bayraqlari həll et"
    
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status=RiskFlag.Status.INVESTIGATING)
        self.message_user(request, f"{updated} risk bayrağı araşdırılır statusuna dəyişdirildi.")
    mark_as_investigating.short_description = "Araşdırılır statusuna dəyişdir"


@admin.register(EmployeeRiskAnalysis)
class EmployeeRiskAnalysisAdmin(SimpleHistoryAdmin):
    list_display = (
        'employee', 'cycle', 'risk_level', 'total_risk_score', 'reviewed_by_hr',
        'analyzed_at', 'get_flag_count'
    )
    list_filter = (
        'risk_level', 'reviewed_by_hr', 'analyzed_at', 'cycle',
        'employee__organization_unit'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'ai_recommendations'
    )
    readonly_fields = ('analyzed_at', 'total_risk_score', 'detailed_analysis', 'ai_recommendations')
    
    fieldsets = (
        ('Əsas Məlumatlar', {
            'fields': ('employee', 'cycle', 'risk_level', 'reviewed_by_hr')
        }),
        ('Risk Xalları', {
            'fields': ('performance_risk_score', 'consistency_risk_score', 'peer_feedback_risk_score', 'total_risk_score')
        }),
        ('Təhlil Nəticələri', {
            'fields': ('detailed_analysis', 'ai_recommendations')
        }),
        ('Tarixlər', {
            'fields': ('analyzed_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_flag_count(self, obj):
        # Defensive: check if employee and risk_flags exist
        if obj.employee and hasattr(obj.employee, 'risk_flags'):
            return obj.employee.risk_flags.filter(cycle=obj.cycle, status='ACTIVE').count()
        return 0
    get_flag_count.short_description = "Aktiv Bayraklar"


@admin.register(PsychologicalRiskSurvey)
class PsychologicalRiskSurveyAdmin(SimpleHistoryAdmin):
    list_display = (
        'title', 'survey_type', 'created_by', 'is_active', 'created_at',
        'get_questions_count', 'get_responses_count'
    )
    list_filter = ('survey_type', 'is_active', 'created_at', 'created_by')
    search_fields = ('title',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Əsas Məlumatlar', {
            'fields': ('title', 'survey_type', 'created_by', 'is_active', 'is_anonymous')
        }),
        ('Sorğu Məlumatları', {
            'fields': ('questions', 'scoring_method', 'risk_thresholds')
        }),
        ('Tarixlər', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_questions_count(self, obj):
        return len(obj.questions_data.get('questions', []))
    get_questions_count.short_description = "Sual Sayı"
    
    def get_responses_count(self, obj):
        return obj.responses.count()
    get_responses_count.short_description = "Cavab Sayı"


@admin.register(PsychologicalRiskResponse)
class PsychologicalRiskResponseAdmin(SimpleHistoryAdmin):
    list_display = (
        'survey', 'employee', 'total_score', 'risk_level', 'requires_attention',
        'responded_at', 'get_completion_time'
    )
    list_filter = (
        'risk_level', 'requires_attention', 'responded_at', 'survey__survey_type',
        'employee__organization_unit'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'survey__title', 'ai_analysis'
    )
    readonly_fields = ('responded_at', 'total_score', 'risk_level', 'ai_analysis')
    
    fieldsets = (
        ('Əsas Məlumatlar', {
            'fields': ('survey', 'employee', 'requires_attention')
        }),
        ('Cavablar', {
            'fields': ('answers', 'total_score', 'risk_level')
        }),
        ('Təhlil', {
            'fields': ('ai_analysis', 'is_anonymous_response')
        }),
        ('Tarixlər', {
            'fields': ('responded_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_completion_time(self, obj):
        # Since we only have responded_at, show when response was submitted
        if obj.responded_at:
            return obj.responded_at.strftime("%d.%m.%Y %H:%M")
        return "—"
    get_completion_time.short_description = "Cavab Tarixi"


@admin.register(Feedback)
class FeedbackAdmin(SimpleHistoryAdmin):
    list_display = (
        'title', 'user', 'feedback_type', 'priority', 'status', 
        'created_at', 'get_response_status'
    )
    list_filter = (
        'feedback_type', 'priority', 'status', 'created_at',
        'user__organization_unit'
    )
    search_fields = ('title', 'description', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'user', 'ip_address', 'user_agent')
    
    fieldsets = (
        ('Əsas Məlumatlar', {
            'fields': ('user', 'title', 'description', 'feedback_type', 'priority', 'status')
        }),
        ('Admin Cavabı', {
            'fields': ('admin_response', 'responded_by', 'response_date')
        }),
        ('Əlavə Fayllar', {
            'fields': ('attachment',)
        }),
        ('Tarixlər', {
            'fields': ('created_at', 'updated_at', 'resolved_at')
        }),
        ('Texniki Məlumatlar', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'mark_as_closed']
    
    def get_response_status(self, obj):
        if obj.admin_response:
            return "✅ Cavablanıb"
        return "❌ Cavablanmayıb"
    get_response_status.short_description = "Cavab Statusu"
    
    def save_model(self, request, obj, form, change):
        # Yeni feedback yaradılırkən user-i təyin et
        if not change and not obj.user:
            obj.user = request.user
            
        # Admin cavab verəndə responded_by sahəsini avtomatik doldur
        if obj.admin_response and not obj.responded_by:
            obj.responded_by = request.user
            from django.utils import timezone
            obj.response_date = timezone.now()
            
            # Status həll edilmiş kimi dəyişdir
            if obj.status == 'NEW':
                obj.status = 'RESOLVED'
                obj.resolved_at = timezone.now()
        
        super().save_model(request, obj, form, change)
        
        # İstifadəçiyə bildiriş göndər
        if obj.admin_response and obj.responded_by:
            from .notifications import NotificationManager
            
            NotificationManager.create_and_send(
                recipient=obj.user,
                title="Geri Bildiriminizə Cavab",
                message=f"'{obj.title}' mövzusunda geri bildiriminizə cavab verildi.",
                notification_type='SUCCESS',
                priority='MEDIUM',
                sender=request.user,
                action_url=f"/admin/core/feedback/{obj.id}/change/",
                action_text="Cavabı Gör",
                send_email=True
            )
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='RESOLVED', resolved_at=timezone.now())
        self.message_user(request, f"{updated} geri bildirim həll edilmiş kimi işarələndi.")
    mark_as_resolved.short_description = "Seçilmiş geri bildirişləri həll edilmiş kimi işarələ"
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"{updated} geri bildirim işləmədə kimi işarələndi.")
    mark_as_in_progress.short_description = "Seçilmiş geri bildirişləri işləmədə kimi işarələ"
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='CLOSED')
        self.message_user(request, f"{updated} geri bildirim bağlandı.")
    mark_as_closed.short_description = "Seçilmiş geri bildirişləri bağla"


# === TƏQVİM HADİSƏLƏRİ ADMİN ===

@admin.register(CalendarEvent)
class CalendarEventAdmin(SimpleHistoryAdmin):
    list_display = (
        'title', 'created_by', 'event_type', 'priority', 'start_date', 
        'end_date', 'is_all_day', 'is_private', 'is_active'
    )
    list_filter = (
        'event_type', 'priority', 'is_all_day', 'is_private', 'is_active',
        'start_date', 'created_by__organization_unit'
    )
    search_fields = ('title', 'description', 'location', 'created_by__username', 'created_by__first_name', 'created_by__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Əsas Məlumatlar', {
            'fields': ('created_by', 'title', 'description', 'event_type', 'priority')
        }),
        ('Vaxt Məlumatları', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time', 'is_all_day')
        }),
        ('Görünüş və Status', {
            'fields': ('color', 'is_private', 'is_active')
        }),
        ('Əlavə Məlumatlar', {
            'fields': ('location', 'reminder_minutes')
        }),
        ('Tarixlər', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    filter_horizontal = ('attendees',)
    
    actions = ['make_public', 'make_private', 'activate_events', 'deactivate_events']
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_private=False)
        self.message_user(request, f"{updated} hadisə ictimai edildi.")
    make_public.short_description = "Seçilmiş hadisələri ictimai et"
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_private=True)
        self.message_user(request, f"{updated} hadisə şəxsi edildi.")
    make_private.short_description = "Seçilmiş hadisələri şəxsi et"
    
    def activate_events(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} hadisə aktivləşdirildi.")
    activate_events.short_description = "Seçilmiş hadisələri aktivləşdir"
    
    def deactivate_events(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} hadisə deaktivləşdirildi.")
    deactivate_events.short_description = "Seçilmiş hadisələri deaktivləşdir"
