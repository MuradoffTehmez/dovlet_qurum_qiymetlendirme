from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

# AI Risk Detection Models will be added directly to avoid circular imports


# --- Yeni Təşkilati Struktur Modeli ---
class OrganizationUnit(models.Model):
    class UnitType(models.TextChoices):
        ALI_IDARE = 'ali_idare', 'Ali İdarə'
        NAZIRLIK = 'nazirlik', 'Nazirlik'
        IDARE_KOMITE = 'idare_komite', 'İdarə / Komitə'
        MUESSISE = 'muessise', 'Müəssisə'
        SHOBE = 'shobe', 'Şöbə'
        SEKTOR = 'sektor', 'Sektor'

    name = models.CharField(max_length=255, verbose_name="Struktur Vahidinin Adı")
    type = models.CharField(max_length=50, choices=UnitType.choices, verbose_name="Növü")
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name="Tabe Olduğu Qurum"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Təşkilati Vahid"
        verbose_name_plural = "Təşkilati Vahidlər"

    def __str__(self):
        return self.name
    
    def get_full_path(self):
        """Tam hierarchik yolu göstərir"""
        path = []
        current = self
        while current:
            path.append(current.name)
            current = current.parent
        return " → ".join(reversed(path))
    
    def get_children_count(self):
        """Alt vahidlərin sayını göstərir"""
        return self.children.count()
    
    def get_employees_count(self):
        """Bu vahiddə işləyən əməkdaşların sayını göstərir"""
        return self.ishchiler.count()


# --- Genişləndirilmiş İstifadəçi Modeli ---
class Ishchi(AbstractUser):
    class Rol(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', 'Superadmin'
        ADMIN = 'ADMIN', 'Admin'
        REHBER = 'REHBER', 'Rəhbər'
        ISHCHI = 'ISHCHI', 'İşçi'

    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.ISHCHI, verbose_name="İstifadəçi Rolu")
    vezife = models.CharField(max_length=255, verbose_name="Vəzifəsi", blank=True)
    organization_unit = models.ForeignKey(
        OrganizationUnit, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ishchiler", verbose_name="Təşkilati Vahid"
    )
    elaqe_nomresi = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Əlaqə Nömrəsi"
    )
    dogum_tarixi = models.DateField(blank=True, null=True, verbose_name="Doğum Tarixi")
    profil_sekli = models.ImageField(
        upload_to="profil_sekilleri/",
        default="profil_sekilleri/default.png",
        verbose_name="Profil Şəkli",
    )

    history = HistoricalRecords()

    def __str__(self):
        return self.get_full_name() or self.username


# --- Sual Hovuzu Modelləri ---
class SualKateqoriyasi(models.Model):
    ad = models.CharField(max_length=255, verbose_name="Kompetensiya / Kateqoriya Adı")

    def __str__(self):
        return self.ad

    history = HistoricalRecords()


class Sual(models.Model):
    class ApplicableTo(models.TextChoices):
        EMPLOYEE = 'employee', 'Əməkdaş'
        MANAGER = 'manager', 'Rəhbər'
        ALL = 'all', 'Hamısı'

    metn = models.TextField(verbose_name="Sualın Mətni")
    kateqoriya = models.ForeignKey(
        SualKateqoriyasi, on_delete=models.SET_NULL, null=True, blank=True
    )
    applicable_to = models.CharField(
        max_length=50, choices=ApplicableTo.choices, default=ApplicableTo.ALL,
        verbose_name="Aid Olduğu Rol"
    )
    yaradan = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True, verbose_name="Sualı Yaradan"
    )

    def __str__(self):
        return self.metn[:50] + "..."

    history = HistoricalRecords()


# --- Qiymətləndirmə Prosesi Modelləri ---
class QiymetlendirmeDovru(models.Model):
    class AnonymityLevel(models.TextChoices):
        FULL_ANONYMOUS = 'FULL_ANONYMOUS', 'Tam Anonim'
        MANAGER_ONLY = 'MANAGER_ONLY', 'Yalnız Rəhbər Görür'
        OPEN = 'OPEN', 'Açıq'

    ad = models.CharField(max_length=255, verbose_name="Dövrün Adı (məs: 2025 Q1)")
    bashlama_tarixi = models.DateField()
    bitme_tarixi = models.DateField()
    aktivdir = models.BooleanField(default=True)
    anonymity_level = models.CharField(
        max_length=20, 
        choices=AnonymityLevel.choices, 
        default=AnonymityLevel.MANAGER_ONLY,
        verbose_name="Anonimlik Səviyyəsi"
    )

    def __str__(self):
        return self.ad

    def is_anonymous_for_user(self, user):
        """İstifadəçi üçün bu dövrün anonim olub olmadığını yoxlayır"""
        if self.anonymity_level == self.AnonymityLevel.OPEN:
            return False
        elif self.anonymity_level == self.AnonymityLevel.FULL_ANONYMOUS:
            return True
        elif self.anonymity_level == self.AnonymityLevel.MANAGER_ONLY:
            # Yalnız rəhbər və admin rolları adları görə bilər
            return user.rol not in ['ADMIN', 'SUPERADMIN', 'REHBER']
        return True

    history = HistoricalRecords()


class Qiymetlendirme(models.Model):
    class Status(models.TextChoices):
        GOZLEMEDE = "GOZLEMEDE", "Gözləmədə"
        TAMAMLANDI = "TAMAMLANDI", "Tamamlandı"

    class QiymetlendirmeNovu(models.TextChoices):
        PEER_REVIEW = "PEER_REVIEW", "Həmkar Qiymətləndirməsi"
        MANAGER_REVIEW = "MANAGER_REVIEW", "Rəhbər Qiymətləndirməsi"
        SELF_REVIEW = "SELF_REVIEW", "Öz-özünə Qiymətləndirmə"
        SUBORDINATE_REVIEW = "SUBORDINATE_REVIEW", "Təbə Qiymətləndirməsi"

    dovr = models.ForeignKey(QiymetlendirmeDovru, on_delete=models.CASCADE)
    qiymetlendirilen = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE, related_name="verilen_qiymetler"
    )
    qiymetlendiren = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE, related_name="etdiyi_qiymetler"
    )
    qiymetlendirme_novu = models.CharField(
        max_length=20,
        choices=QiymetlendirmeNovu.choices,
        default=QiymetlendirmeNovu.PEER_REVIEW,
        verbose_name="Qiymətləndirmə Növü"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.GOZLEMEDE
    )
    yaradilma_tarixi = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Yaradılma Tarixi")
    tamamlanma_tarixi = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarixi")

    class Meta:
        unique_together = ("dovr", "qiymetlendirilen", "qiymetlendiren", "qiymetlendirme_novu")

    def __str__(self):
        return f"{self.qiymetlendiren} -> {self.qiymetlendirilen} ({self.dovr.ad}) [{self.get_qiymetlendirme_novu_display()}]"

    def is_self_review(self):
        """Bu qiymətləndirmənin self-review olub olmadığını yoxlayır"""
        return self.qiymetlendirme_novu == self.QiymetlendirmeNovu.SELF_REVIEW

    def calculate_average_score(self):
        """Bu qiymətləndirmənin ortalama balını hesablayır"""
        from django.db.models import Avg
        result = self.cavablar.aggregate(avg_score=Avg('xal'))
        return round(result['avg_score'] or 0, 2)

    def get_completion_percentage(self):
        """Qiymətləndirmənin tamamlanma faizini hesablayır"""
        total_questions = self.dovr.suallar.count() if hasattr(self.dovr, 'suallar') else 0
        answered_questions = self.cavablar.count()
        
        if total_questions == 0:
            return 100.0 if answered_questions == 0 else 0.0
        
        return round((answered_questions / total_questions) * 100, 1)

    history = HistoricalRecords()


class Cavab(models.Model):
    qiymetlendirme = models.ForeignKey(
        Qiymetlendirme, on_delete=models.CASCADE, related_name="cavablar"
    )
    sual = models.ForeignKey(Sual, on_delete=models.CASCADE)
    xal = models.PositiveSmallIntegerField(verbose_name="Verilən Xal (1-10)")
    metnli_rey = models.TextField(verbose_name="Əlavə Rəy", blank=True, null=True)

    def __str__(self):
        return f"{self.qiymetlendirme}: Sual {self.sual.id} - {self.xal} xal"

    history = HistoricalRecords()


class InkishafPlani(models.Model):
    class Status(models.TextChoices):
        AKTIV = "AKTIV", "Aktiv"
        TAMAMLANMISH = "TAMAMLANMISH", "Tamamlanmış"

    ishchi = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="inkishaf_planlari", verbose_name="İşçi"
    )
    dovr = models.ForeignKey(
        QiymetlendirmeDovru, on_delete=models.CASCADE,
        verbose_name="Qiymətləndirmə Dövrü"
    )
    yaradilma_tarixi = models.DateField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.AKTIV, verbose_name="Planın Statusu"
    )

    class Meta:
        verbose_name = "Fərdi İnkişaf Planı"
        verbose_name_plural = "Fərdi İnkişaf Planları"
        unique_together = ("ishchi", "dovr")

    def __str__(self):
        return f"{self.ishchi.get_full_name()} - {self.dovr.ad} İnkişaf Planı"

    history = HistoricalRecords()


class Hedef(models.Model):
    class Status(models.TextChoices):
        BASHLANMAYIB = "BASHLANMAYIB", "Başlanmayıb"
        DAVAM_EDIR = "DAVAM_EDIR", "Davam Edir"
        TAMAMLANDI = "TAMAMLANDI", "Tamamlandı"
        LEGVEDILDI = "LEGVEDILDI", "Ləğv Edildi"

    plan = models.ForeignKey(
        InkishafPlani, on_delete=models.CASCADE,
        related_name="hedefler", verbose_name="İnkişaf Planı"
    )
    tesvir = models.TextField(verbose_name="Hədəfin Təsviri")
    son_tarix = models.DateField(verbose_name="Hədəfin Son İcra Tarixi")
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.BASHLANMAYIB, verbose_name="Hədəfin Statusu"
    )

    def __str__(self):
        return self.tesvir[:70]

    history = HistoricalRecords()


# --- Geri Bildirim və Şikayət Sistemi ---
class Feedback(models.Model):
    """İstifadəçilərdən gələn geri bildirimlər, təkliflər və şikayətlər"""
    
    class FeedbackType(models.TextChoices):
        COMPLAINT = "COMPLAINT", "Şikayət"
        SUGGESTION = "SUGGESTION", "Təklif"
        BUG_REPORT = "BUG_REPORT", "Texniki Problem"
        FEATURE_REQUEST = "FEATURE_REQUEST", "Yeni Funksiya Tələbi"
        GENERAL = "GENERAL", "Ümumi Geri Bildirim"
    
    class Priority(models.TextChoices):
        LOW = "LOW", "Aşağı"
        MEDIUM = "MEDIUM", "Orta"
        HIGH = "HIGH", "Yüksək"
        URGENT = "URGENT", "Təcili"
    
    class Status(models.TextChoices):
        NEW = "NEW", "Yeni"
        IN_PROGRESS = "IN_PROGRESS", "İcrada"
        RESOLVED = "RESOLVED", "Həll edilib"
        CLOSED = "CLOSED", "Bağlandı"
    
    # Əsas sahələr
    user = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="feedbacks", verbose_name="İstifadəçi"
    )
    title = models.CharField(max_length=200, verbose_name="Başlıq")
    description = models.TextField(verbose_name="Təsvir")
    feedback_type = models.CharField(
        max_length=20, choices=FeedbackType.choices,
        default=FeedbackType.GENERAL, verbose_name="Növ"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name="Prioritet"
    )
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.NEW, verbose_name="Status"
    )
    
    # Tarixlər
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə Tarixi")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Həll Tarixi")
    
    # Admin cavabı
    admin_response = models.TextField(
        blank=True, null=True, verbose_name="Admin Cavabı"
    )
    responded_by = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="feedback_responses", verbose_name="Cavab Verən"
    )
    response_date = models.DateTimeField(null=True, blank=True, verbose_name="Cavab Tarixi")
    
    # Əlavə məlumatlar
    attachment = models.FileField(
        upload_to="feedback_files/", null=True, blank=True,
        verbose_name="Əlavə Fayl"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Ünvanı")
    user_agent = models.TextField(blank=True, verbose_name="Brauzer Məlumatı")
    
    class Meta:
        verbose_name = "Geri Bildirim"
        verbose_name_plural = "Geri Bildirimlər"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['feedback_type', 'priority']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title[:50]}"
    
    def get_absolute_url(self):
        return f"/feedback/{self.pk}/"
    
    def mark_as_resolved(self, admin_user, response=None):
        """Geri bildirimi həll edilmiş kimi işarələ"""
        from django.utils import timezone
        
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        if response:
            self.admin_response = response
            self.responded_by = admin_user
            self.response_date = timezone.now()
        self.save()
    
    def get_status_color(self):
        """Status üçün rəng qaytarır"""
        colors = {
            self.Status.NEW: 'primary',
            self.Status.IN_PROGRESS: 'warning',
            self.Status.RESOLVED: 'success',
            self.Status.CLOSED: 'secondary'
        }
        return colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Prioritet üçün rəng qaytarır"""
        colors = {
            self.Priority.LOW: 'info',
            self.Priority.MEDIUM: 'warning',
            self.Priority.HIGH: 'danger',
            self.Priority.URGENT: 'dark'
        }
        return colors.get(self.priority, 'secondary')
    
    history = HistoricalRecords()


# --- Bildiriş Sistemi ---
class Notification(models.Model):
    """Real-time bildiriş sistemi"""
    
    class NotificationType(models.TextChoices):
        INFO = "INFO", "Məlumat"
        SUCCESS = "SUCCESS", "Uğur"
        WARNING = "WARNING", "Xəbərdarlıq"  
        ERROR = "ERROR", "Xəta"
        TASK_ASSIGNED = "TASK_ASSIGNED", "Tapşırıq Təyin Edildi"
        DEADLINE_REMINDER = "DEADLINE_REMINDER", "Son Tarix Xatırlatması"
        EVALUATION_COMPLETED = "EVALUATION_COMPLETED", "Qiymətləndirmə Tamamlandı"
        PLAN_APPROVED = "PLAN_APPROVED", "Plan Təsdiqləndi"
        FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED", "Yeni Geri Bildirim"
        SYSTEM_UPDATE = "SYSTEM_UPDATE", "Sistem Yeniləməsi"
    
    class Priority(models.TextChoices):
        LOW = "LOW", "Aşağı"
        MEDIUM = "MEDIUM", "Orta" 
        HIGH = "HIGH", "Yüksək"
        URGENT = "URGENT", "Təcili"
    
    # Əsas sahələr
    recipient = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="notifications", verbose_name="Alıcı"
    )
    sender = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sent_notifications", verbose_name="Göndərən"
    )
    
    title = models.CharField(max_length=200, verbose_name="Başlıq")
    message = models.TextField(verbose_name="Mesaj")
    notification_type = models.CharField(
        max_length=25, choices=NotificationType.choices,
        default=NotificationType.INFO, verbose_name="Növ"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name="Prioritet"
    )
    
    # Status sahələri
    is_read = models.BooleanField(default=False, verbose_name="Oxunub")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Oxunma Tarixi")
    is_archived = models.BooleanField(default=False, verbose_name="Arxivləşdirilib")
    
    # Əlavə məlumatlar
    action_url = models.URLField(blank=True, null=True, verbose_name="Əməliyyat URL-i")
    action_text = models.CharField(max_length=100, blank=True, verbose_name="Əməliyyat Mətni")
    
    # Tarixlər
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Bitmə Tarixi")
    
    # Əlavə metadata JSON
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Əlavə Məlumatlar")
    
    class Meta:
        verbose_name = "Bildiriş"
        verbose_name_plural = "Bildirişlər"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'priority']),
            models.Index(fields=['is_archived', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title[:50]}"
    
    def mark_as_read(self):
        """Bildirişi oxunmuş kimi işarələ"""
        from django.utils import timezone
        
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_icon(self):
        """Bildiriş növünə görə ikon qaytarır"""
        icons = {
            self.NotificationType.INFO: 'fas fa-info-circle',
            self.NotificationType.SUCCESS: 'fas fa-check-circle',
            self.NotificationType.WARNING: 'fas fa-exclamation-triangle',
            self.NotificationType.ERROR: 'fas fa-times-circle',
            self.NotificationType.TASK_ASSIGNED: 'fas fa-tasks',
            self.NotificationType.DEADLINE_REMINDER: 'fas fa-clock',
            self.NotificationType.EVALUATION_COMPLETED: 'fas fa-chart-line',
            self.NotificationType.PLAN_APPROVED: 'fas fa-thumbs-up',
            self.NotificationType.FEEDBACK_RECEIVED: 'fas fa-comments',
            self.NotificationType.SYSTEM_UPDATE: 'fas fa-cog',
        }
        return icons.get(self.notification_type, 'fas fa-bell')
    
    def get_color_class(self):
        """Bildiriş növünə görə rəng sinifi qaytarır"""
        colors = {
            self.NotificationType.INFO: 'primary',
            self.NotificationType.SUCCESS: 'success', 
            self.NotificationType.WARNING: 'warning',
            self.NotificationType.ERROR: 'danger',
            self.NotificationType.TASK_ASSIGNED: 'info',
            self.NotificationType.DEADLINE_REMINDER: 'warning',
            self.NotificationType.EVALUATION_COMPLETED: 'success',
            self.NotificationType.PLAN_APPROVED: 'success',
            self.NotificationType.FEEDBACK_RECEIVED: 'primary',
            self.NotificationType.SYSTEM_UPDATE: 'secondary',
        }
        return colors.get(self.notification_type, 'primary')
    
    def get_priority_badge(self):
        """Prioritet badge-i qaytarır"""
        badges = {
            self.Priority.LOW: 'secondary',
            self.Priority.MEDIUM: 'primary',
            self.Priority.HIGH: 'warning', 
            self.Priority.URGENT: 'danger'
        }
        return badges.get(self.priority, 'secondary')
    
    def is_expired(self):
        """Bildirişin müddətinin bitib-bitmədiyini yoxlayır"""
        if not self.expires_at:
            return False
        
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @classmethod
    def cleanup_expired(cls):
        """Müddəti bitmiş bildirişləri sil"""
        from django.utils import timezone
        
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now(),
            is_archived=False
        ).update(is_archived=True)
        
        return expired_count
    
    @classmethod
    def get_unread_count(cls, user):
        """İstifadəçinin oxunmamış bildiriş sayını qaytarır"""
        return cls.objects.filter(
            recipient=user,
            is_read=False,
            is_archived=False
        ).count()
    
    @classmethod
    def create_notification(cls, recipient, title, message, notification_type=None, 
                          priority=None, sender=None, action_url=None, action_text=None, 
                          expires_in_days=None, metadata=None):
        """
        Yeni bildiriş yaratmaq üçün helper method
        
        Usage:
        Notification.create_notification(
            recipient=user,
            title="Yeni Tapşırıq",
            message="Sizə yeni performans qiymətləndirməsi tapşırığı təyin edildi",
            notification_type=Notification.NotificationType.TASK_ASSIGNED,
            priority=Notification.Priority.HIGH,
            action_url="/evaluations/123/",
            action_text="Qiymətləndirməyə Bax"
        )
        """
        from django.utils import timezone
        
        notification = cls(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            notification_type=notification_type or cls.NotificationType.INFO,
            priority=priority or cls.Priority.MEDIUM,
            action_url=action_url,
            action_text=action_text,
            metadata=metadata or {}
        )
        
        if expires_in_days:
            notification.expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)
        
        notification.save()
        return notification
    
    history = HistoricalRecords()


# --- Calendar Event Model ---
class CalendarEvent(models.Model):
    """İstifadəçi yaratdığı təqvim hadisələri"""
    
    class EventType(models.TextChoices):
        MEETING = "MEETING", "Görüş"
        TASK = "TASK", "Tapşırıq"
        REMINDER = "REMINDER", "Xatırlatma"
        DEADLINE = "DEADLINE", "Son Tarix"
        PERSONAL = "PERSONAL", "Şəxsi"
        TRAINING = "TRAINING", "Təlim"
        EVALUATION = "EVALUATION", "Qiymətləndirmə"
        OTHER = "OTHER", "Digər"
    
    class Priority(models.TextChoices):
        LOW = "LOW", "Aşağı"
        MEDIUM = "MEDIUM", "Orta"
        HIGH = "HIGH", "Yüksək"
        URGENT = "URGENT", "Təcili"
    
    # Əsas sahələr
    created_by = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="created_events", verbose_name="Yaradan"
    )
    title = models.CharField(max_length=200, verbose_name="Başlıq")
    description = models.TextField(blank=True, verbose_name="Təsvir")
    
    # Vaxt sahələri
    start_date = models.DateField(verbose_name="Başlama Tarixi")
    end_date = models.DateField(null=True, blank=True, verbose_name="Bitmə Tarixi")
    start_time = models.TimeField(null=True, blank=True, verbose_name="Başlama Vaxtı")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Bitmə Vaxtı")
    is_all_day = models.BooleanField(default=False, verbose_name="Bütün Gün")
    
    # Kategoriya və prioritet
    event_type = models.CharField(
        max_length=15, choices=EventType.choices,
        default=EventType.PERSONAL, verbose_name="Hadisə Növü"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name="Prioritet"
    )
    
    # Görünürlük və status
    is_private = models.BooleanField(default=True, verbose_name="Şəxsi")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    
    # Rəng (HEX format)
    color = models.CharField(max_length=7, default="#3788d8", verbose_name="Rəng")
    
    # Xatırlatma
    reminder_minutes = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Xatırlatma (dəqiqə əvvəl)"
    )
    
    # Metadata
    location = models.CharField(max_length=255, blank=True, verbose_name="Yer")
    attendees = models.ManyToManyField(
        Ishchi, blank=True, 
        related_name="attending_events", verbose_name="İştirakçılar"
    )
    
    # Tarixlər
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə Tarixi")
    
    class Meta:
        verbose_name = "Təqvim Hadisəsi"
        verbose_name_plural = "Təqvim Hadisələri"
        ordering = ['-start_date', '-start_time']
        indexes = [
            models.Index(fields=['created_by', 'start_date']),
            models.Index(fields=['event_type', 'priority']),
            models.Index(fields=['is_active', 'is_private']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
    
    def get_absolute_url(self):
        return f"/teqvim/hadise/{self.pk}/"
    
    def get_duration(self):
        """Hadisənin müddətini qaytarır"""
        if self.is_all_day or not self.start_time or not self.end_time:
            if self.end_date:
                return (self.end_date - self.start_date).days + 1
            return 1
        
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(self.start_date, self.start_time)
        end_datetime = datetime.combine(self.end_date or self.start_date, self.end_time)
        
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
        
        duration = end_datetime - start_datetime
        return duration.total_seconds() / 3600  # hours
    
    def get_color_for_type(self):
        """Hadisə növünə görə rəng qaytarır"""
        colors = {
            self.EventType.MEETING: '#667eea',
            self.EventType.TASK: '#fd7e14',
            self.EventType.REMINDER: '#ffc107',
            self.EventType.DEADLINE: '#dc3545',
            self.EventType.PERSONAL: '#6f42c1',
            self.EventType.TRAINING: '#20c997',
            self.EventType.EVALUATION: '#e83e8c',
            self.EventType.OTHER: '#6c757d',
        }
        return colors.get(self.event_type, self.color)
    
    def get_priority_badge(self):
        """Prioritet badge-i qaytarır"""
        badges = {
            self.Priority.LOW: 'secondary',
            self.Priority.MEDIUM: 'primary',
            self.Priority.HIGH: 'warning',
            self.Priority.URGENT: 'danger'
        }
        return badges.get(self.priority, 'secondary')
    
    def to_fullcalendar_event(self):
        """FullCalendar üçün event obyekti qaytarır"""
        event = {
            'id': f'event_{self.id}',
            'title': self.title,
            'start': self.start_date.isoformat(),
            'backgroundColor': self.get_color_for_type(),
            'borderColor': self.get_color_for_type(),
            'textColor': 'white',
            'extendedProps': {
                'type': 'custom_event',
                'description': self.description,
                'event_type': self.get_event_type_display(),
                'priority': self.get_priority_display(),
                'location': self.location,
                'created_by': self.created_by.get_full_name(),
                'is_all_day': self.is_all_day,
                'duration': self.get_duration(),
            }
        }
        
        # Bitmə tarixi əlavə et
        if self.end_date:
            event['end'] = self.end_date.isoformat()
        
        # Vaxt məlumatları əlavə et
        if not self.is_all_day and self.start_time:
            event['start'] = f"{self.start_date}T{self.start_time}"
            if self.end_time:
                end_date = self.end_date or self.start_date
                event['end'] = f"{end_date}T{self.end_time}"
        
        return event
    
    @classmethod
    def get_events_for_period(cls, user, start_date, end_date, include_private=True):
        """Müəyyən dövr üçün hadisələri qaytarır"""
        queryset = cls.objects.filter(
            start_date__lte=end_date,
            is_active=True
        ).filter(
            models.Q(start_date__gte=start_date) |
            models.Q(end_date__gte=start_date) |
            models.Q(end_date__isnull=True, start_date__lte=end_date)
        )
        
        # İstifadəçiyə görə filter
        if include_private:
            queryset = queryset.filter(
                models.Q(created_by=user) |
                models.Q(attendees=user) |
                models.Q(is_private=False)
            )
        else:
            queryset = queryset.filter(is_private=False)
        
        return queryset.distinct()
    
    history = HistoricalRecords()


# === QUICK FEEDBACK SİSTEMİ ===

class QuickFeedbackCategory(models.Model):
    """Sürətli geri bildirim kateqoriyaları"""
    
    class CategoryType(models.TextChoices):
        RECOGNITION = 'RECOGNITION', 'Tanınma / Təşəkkür'
        IMPROVEMENT = 'IMPROVEMENT', 'İnkişaf Təklifi'
        COLLABORATION = 'COLLABORATION', 'Əməkdaşlıq'
        PROJECT = 'PROJECT', 'Layihə üzrə'
        GENERAL = 'GENERAL', 'Ümumi'
    
    name = models.CharField(max_length=100, verbose_name="Kateqoriya Adı")
    description = models.TextField(blank=True, verbose_name="Təsvir")
    category_type = models.CharField(
        max_length=20, 
        choices=CategoryType.choices,
        default=CategoryType.GENERAL,
        verbose_name="Kateqoriya Növü"
    )
    icon = models.CharField(max_length=50, default="fas fa-comment", verbose_name="İkon")
    is_active = models.BooleanField(default=True, verbose_name="Aktivdir")
    
    class Meta:
        verbose_name = "Sürətli Geri Bildirim Kateqoriyası"
        verbose_name_plural = "Sürətli Geri Bildirim Kateqoriyaları"
        ordering = ['name']
    
    def __str__(self):
        return self.name

    history = HistoricalRecords()


class QuickFeedback(models.Model):
    """Sürətli geri bildirim sistemi"""
    
    class FeedbackType(models.TextChoices):
        POSITIVE = 'POSITIVE', 'Müsbət'
        CONSTRUCTIVE = 'CONSTRUCTIVE', 'Konstruktiv'
        NEUTRAL = 'NEUTRAL', 'Neytral'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Aşağı'
        MEDIUM = 'MEDIUM', 'Orta'
        HIGH = 'HIGH', 'Yüksək'
        URGENT = 'URGENT', 'Təcili'
    
    # Əsas sahələr
    from_user = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="given_quick_feedbacks", verbose_name="Verən"
    )
    to_user = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="received_quick_feedbacks", verbose_name="Alan"
    )
    
    # Məzmun
    category = models.ForeignKey(
        QuickFeedbackCategory, on_delete=models.SET_NULL, null=True,
        verbose_name="Kateqoriya"
    )
    feedback_type = models.CharField(
        max_length=15, choices=FeedbackType.choices,
        default=FeedbackType.POSITIVE, verbose_name="Geri Bildirim Növü"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name="Prioritet"
    )
    
    title = models.CharField(max_length=200, verbose_name="Başlıq")
    message = models.TextField(verbose_name="Mesaj")
    
    # Əlavə məlumatlar
    is_anonymous = models.BooleanField(default=False, verbose_name="Anonim")
    is_private = models.BooleanField(default=True, verbose_name="Şəxsi")
    
    # Tarixlər
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Oxunma Tarixi")
    
    # Status
    is_read = models.BooleanField(default=False, verbose_name="Oxunub")
    is_archived = models.BooleanField(default=False, verbose_name="Arxivləşdirilib")
    
    # Rating (5 ulduzlu sistem)
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(i, f"{i} ulduz") for i in range(1, 6)],
        verbose_name="Reytinq"
    )
    
    class Meta:
        verbose_name = "Sürətli Geri Bildirim"
        verbose_name_plural = "Sürətli Geri Bildirimlər"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', 'is_read', 'created_at']),
            models.Index(fields=['from_user', 'created_at']),
            models.Index(fields=['category', 'feedback_type']),
            models.Index(fields=['is_archived', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.from_user.get_full_name()} -> {self.to_user.get_full_name()}: {self.title[:50]}"
    
    def mark_as_read(self):
        """Geri bildirimi oxunmuş kimi işarələ"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_display_sender(self):
        """Anonim olub olmadığına görə göndərəni qaytarır"""
        if self.is_anonymous:
            return "Anonim İşçi"
        return self.from_user.get_full_name()
    
    def get_color_class(self):
        """Feedback növünə görə CSS sinifi qaytarır"""
        colors = {
            self.FeedbackType.POSITIVE: 'success',
            self.FeedbackType.CONSTRUCTIVE: 'warning',
            self.FeedbackType.NEUTRAL: 'info'
        }
        return colors.get(self.feedback_type, 'secondary')

    history = HistoricalRecords()


class PrivateNote(models.Model):
    """Rəhbərlərin işçilər haqqında məxfi qeydləri"""
    
    class NoteType(models.TextChoices):
        PERFORMANCE = 'PERFORMANCE', 'Performans Qeydi'
        DEVELOPMENT = 'DEVELOPMENT', 'İnkişaf Qeydi'
        BEHAVIOR = 'BEHAVIOR', 'Davranış Qeydi'
        ACHIEVEMENT = 'ACHIEVEMENT', 'Nailiyyət Qeydi'
        CONCERN = 'CONCERN', 'Narahatlıq Qeydi'
        FEEDBACK = 'FEEDBACK', 'Geri Bildirim'
        GENERAL = 'GENERAL', 'Ümumi Qeyd'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Aşağı'
        MEDIUM = 'MEDIUM', 'Orta'
        HIGH = 'HIGH', 'Yüksək'
        URGENT = 'URGENT', 'Təcili'
    
    # Əsas sahələr
    employee = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="private_notes", verbose_name="İşçi"
    )
    manager = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="created_private_notes", verbose_name="Rəhbər"
    )
    
    # Məzmun
    title = models.CharField(max_length=200, verbose_name="Başlıq")
    content = models.TextField(verbose_name="Məzmun")
    note_type = models.CharField(
        max_length=15, choices=NoteType.choices,
        default=NoteType.GENERAL, verbose_name="Qeyd Növü"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name="Prioritet"
    )
    
    # Metadata
    related_cycle = models.ForeignKey(
        QiymetlendirmeDovru, on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Əlaqəli Dövr"
    )
    tags = models.CharField(
        max_length=500, blank=True,
        help_text="Vergüllə ayrılmış etiketlər (məs: liderlik, kommunikasiya, təlim)",
        verbose_name="Etiketlər"
    )
    
    # Tarixlər
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə Tarixi")
    
    # Status
    is_archived = models.BooleanField(default=False, verbose_name="Arxivləşdirilib")
    is_confidential = models.BooleanField(default=True, verbose_name="Məxfidir")
    
    class Meta:
        verbose_name = "Məxfi Qeyd"
        verbose_name_plural = "Məxfi Qeydlər"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'manager', 'created_at']),
            models.Index(fields=['note_type', 'priority']),
            models.Index(fields=['is_archived', 'created_at']),
            models.Index(fields=['related_cycle']),
        ]
    
    def __str__(self):
        return f"{self.manager.get_full_name()} -> {self.employee.get_full_name()}: {self.title[:50]}"
    
    def get_tags_list(self):
        """Etiketləri siyahı şəklində qaytarır"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_list(self, tags_list):
        """Etiket siyahısını mətinə çevirir"""
        self.tags = ', '.join(tags_list)
    
    def get_color_class(self):
        """Qeyd növünə görə CSS sinifi qaytarır"""
        colors = {
            self.NoteType.PERFORMANCE: 'primary',
            self.NoteType.DEVELOPMENT: 'info',
            self.NoteType.BEHAVIOR: 'warning',
            self.NoteType.ACHIEVEMENT: 'success',
            self.NoteType.CONCERN: 'danger',
            self.NoteType.FEEDBACK: 'secondary',
            self.NoteType.GENERAL: 'light'
        }
        return colors.get(self.note_type, 'light')
    
    def get_priority_color(self):
        """Prioritetə görə rəng qaytarır"""
        colors = {
            self.Priority.LOW: 'success',
            self.Priority.MEDIUM: 'primary',
            self.Priority.HIGH: 'warning',
            self.Priority.URGENT: 'danger'
        }
        return colors.get(self.priority, 'primary')

    history = HistoricalRecords()


class IdeaCategory(models.Model):
    """İdeya kateqoriyaları"""
    
    name = models.CharField(max_length=100, verbose_name="Kateqoriya Adı")
    description = models.TextField(blank=True, verbose_name="Təsvir")
    icon = models.CharField(max_length=50, default="fas fa-lightbulb", verbose_name="İkon")
    color = models.CharField(max_length=7, default="#007bff", help_text="Hex rəng kodu", verbose_name="Rəng")
    is_active = models.BooleanField(default=True, verbose_name="Aktivdir")
    
    class Meta:
        verbose_name = "İdeya Kateqoriyası"
        verbose_name_plural = "İdeya Kateqoriyaları"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Idea(models.Model):
    """İşçilərin təklif və ideyaları"""
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Layihə'
        SUBMITTED = 'SUBMITTED', 'Təqdim Edilib'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Baxılır'
        APPROVED = 'APPROVED', 'Təsdiqlənib'
        REJECTED = 'REJECTED', 'Rədd Edilib'
        IMPLEMENTED = 'IMPLEMENTED', 'Həyata Keçirilib'
        ARCHIVED = 'ARCHIVED', 'Arxivləşdirilib'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Aşağı'
        MEDIUM = 'MEDIUM', 'Orta'
        HIGH = 'HIGH', 'Yüksək'
        CRITICAL = 'CRITICAL', 'Kritik'
    
    # Əsas məlumatlar
    title = models.CharField(max_length=200, verbose_name="Başlıq")
    description = models.TextField(verbose_name="Təsvir")
    category = models.ForeignKey(
        IdeaCategory, on_delete=models.SET_NULL, null=True,
        related_name="ideas", verbose_name="Kateqoriya"
    )
    
    # İstifadəçi məlumatları
    author = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="ideas", verbose_name="Müəllif"
    )
    is_anonymous = models.BooleanField(default=False, verbose_name="Anonim")
    
    # Status və prioritet
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.DRAFT, verbose_name="Status"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name="Prioritet"
    )
    
    # Əlavə məlumatlar
    estimated_impact = models.TextField(blank=True, verbose_name="Gözlənilən Təsir")
    implementation_notes = models.TextField(blank=True, verbose_name="İcra Qeydləri")
    budget_estimate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Büdcə Təxmini"
    )
    
    # Tarixlər
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə Tarixi")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Təqdim Tarixi")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Baxış Tarixi")
    
    # Moderasiya
    reviewer = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_ideas", verbose_name="Baxan"
    )
    review_notes = models.TextField(blank=True, verbose_name="Baxış Qeydləri")
    
    class Meta:
        verbose_name = "İdeya"
        verbose_name_plural = "İdeyalar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['author', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_author_display(self):
        """Anonim olub olmadığına görə müəllifi qaytarır"""
        if self.is_anonymous:
            return "Anonim İşçi"
        return self.author.get_full_name()
    
    def get_status_color(self):
        """Status üçün Bootstrap rəng sinifi"""
        colors = {
            self.Status.DRAFT: 'secondary',
            self.Status.SUBMITTED: 'primary',
            self.Status.UNDER_REVIEW: 'warning',
            self.Status.APPROVED: 'success',
            self.Status.REJECTED: 'danger',
            self.Status.IMPLEMENTED: 'info',
            self.Status.ARCHIVED: 'dark'
        }
        return colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Prioritet üçün Bootstrap rəng sinifi"""
        colors = {
            self.Priority.LOW: 'success',
            self.Priority.MEDIUM: 'primary',
            self.Priority.HIGH: 'warning',
            self.Priority.CRITICAL: 'danger'
        }
        return colors.get(self.priority, 'primary')
    
    def submit(self):
        """İdeyanı təqdim et"""
        if self.status == self.Status.DRAFT:
            self.status = self.Status.SUBMITTED
            self.submitted_at = timezone.now()
            self.save()
    
    def approve(self, reviewer, notes=""):
        """İdeyanı təsdiqlə"""
        self.status = self.Status.APPROVED
        self.reviewer = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject(self, reviewer, notes=""):
        """İdeyanı rədd et"""
        self.status = self.Status.REJECTED
        self.reviewer = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()

    history = HistoricalRecords()


class IdeaVote(models.Model):
    """İdeyalara verilən səslər"""
    
    class VoteType(models.TextChoices):
        UPVOTE = 'UPVOTE', 'Müsbət'
        DOWNVOTE = 'DOWNVOTE', 'Mənfi'
    
    idea = models.ForeignKey(
        Idea, on_delete=models.CASCADE,
        related_name="votes", verbose_name="İdeya"
    )
    user = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="idea_votes", verbose_name="İstifadəçi"
    )
    vote_type = models.CharField(
        max_length=10, choices=VoteType.choices,
        verbose_name="Səs Növü"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    
    class Meta:
        verbose_name = "İdeya Səsi"
        verbose_name_plural = "İdeya Səsləri"
        unique_together = ['idea', 'user']
        indexes = [
            models.Index(fields=['idea', 'vote_type']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} -> {self.idea.title} ({self.vote_type})"


# === AI RİSK ANALİZİ SİSTEMİ ===

class RiskFlag(models.Model):
    """
    Qırmızı Bayraq sistemi - AI tərəfindən aşkar edilən risklər
    """
    
    class FlagType(models.TextChoices):
        LOW_PERFORMANCE = 'LOW_PERFORMANCE', 'Aşağı Performans'
        HIGH_SCORE_VARIANCE = 'HIGH_SCORE_VARIANCE', 'Yüksək Bal Uyğunsuzluğu'
        HIGH_NEGATIVE_FEEDBACK = 'HIGH_NEGATIVE_FEEDBACK', 'Çox Neqativ Rəy'
        LOW_PEER_INTERACTION = 'LOW_PEER_INTERACTION', 'Az Həmkar Qarşılıqlı Əlaqəsi'
        LONG_ABSENCE = 'LONG_ABSENCE', 'Uzun Müddət Qeyb Olma'
        NO_DEVELOPMENT_PLAN = 'NO_DEVELOPMENT_PLAN', 'İnkişaf Planı Yoxdur'
        NO_ORGANIZATIONAL_UNIT = 'NO_ORGANIZATIONAL_UNIT', 'Təşkilati Vahidə Aid Deyil'
        INSUFFICIENT_EVALUATORS = 'INSUFFICIENT_EVALUATORS', 'Kifayətsiz Qiymətləndirici'
        NO_EVALUATION_DATA = 'NO_EVALUATION_DATA', 'Qiymətləndirmə Məlumatı Yox'
        NO_ANSWER_DATA = 'NO_ANSWER_DATA', 'Cavab Məlumatı Yox'
        STATISTICAL_ANOMALY = 'STATISTICAL_ANOMALY', 'Statistik Anomaliy'
        BEHAVIORAL_ANOMALY = 'BEHAVIORAL_ANOMALY', 'Davranış Anomaliyası'
    
    class Severity(models.TextChoices):
        LOW = 'LOW', 'Aşağı'
        MEDIUM = 'MEDIUM', 'Orta'
        HIGH = 'HIGH', 'Yüksək'
        CRITICAL = 'CRITICAL', 'Kritik'
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Aktiv'
        RESOLVED = 'RESOLVED', 'Həll edilib'
        IGNORED = 'IGNORED', 'Rədd edilib'
        REVIEWING = 'REVIEWING', 'Nəzərdən keçirilir'
    
    employee = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name='risk_flags', verbose_name='İşçi'
    )
    cycle = models.ForeignKey(
        QiymetlendirmeDovru, on_delete=models.CASCADE,
        verbose_name='Qiymətləndirmə Dövrü'
    )
    flag_type = models.CharField(
        max_length=50, choices=FlagType.choices,
        verbose_name='Bayraq Növü'
    )
    severity = models.CharField(
        max_length=20, choices=Severity.choices,
        default=Severity.MEDIUM, verbose_name='Ciddiyyət'
    )
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.ACTIVE, verbose_name='Status'
    )
    
    # Risk məlumatları
    risk_score = models.PositiveIntegerField(
        default=0, verbose_name='Risk Xalı'
    )
    details = models.JSONField(
        default=dict, verbose_name='Ətraflı Məlumat'
    )
    ai_confidence = models.FloatField(
        default=0.0, verbose_name='AI Əminlik Dərəcəsi'
    )
    
    # Tarixlər
    detected_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Aşkar Edilmə Tarixi'
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Həll Edilmə Tarixi'
    )
    resolved_by = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resolved_flags', verbose_name='Həll Edən'
    )
    
    # Qeydlər
    hr_notes = models.TextField(
        blank=True, verbose_name='HR Qeydləri'
    )
    resolution_action = models.TextField(
        blank=True, verbose_name='Həll Tədbirləri'
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Risk Bayrağı'
        verbose_name_plural = 'Risk Bayraqlari'
        ordering = ['-detected_at', '-severity']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['flag_type', 'severity']),
            models.Index(fields=['detected_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_flag_type_display()} ({self.get_severity_display()})"
    
    def resolve(self, resolved_by: 'Ishchi', action_taken: str = ""):
        """Riski həll edilmiş kimi işarələ"""
        from django.utils import timezone
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        self.resolution_action = action_taken
        self.save()
    
    def ignore(self, ignored_by: 'Ishchi', reason: str = ""):
        """Riski rədd edilmiş kimi işarələ"""
        from django.utils import timezone
        self.status = self.Status.IGNORED
        self.resolved_at = timezone.now()
        self.resolved_by = ignored_by
        self.hr_notes = f"Rədd edilmə səbəbi: {reason}"
        self.save()
    
    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE
    
    @property
    def days_active(self):
        from django.utils import timezone
        if self.resolved_at:
            return (self.resolved_at.date() - self.detected_at.date()).days
        return (timezone.now().date() - self.detected_at.date()).days


class EmployeeRiskAnalysis(models.Model):
    """
    İşçi üçün ümumi risk analizi nəticələri
    """
    
    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Aşağı'
        MEDIUM = 'MEDIUM', 'Orta'
        HIGH = 'HIGH', 'Yüksək'
        CRITICAL = 'CRITICAL', 'Kritik'
    
    employee = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name='risk_analyses', verbose_name='İşçi'
    )
    cycle = models.ForeignKey(
        QiymetlendirmeDovru, on_delete=models.CASCADE,
        verbose_name='Qiymətləndirmə Dövrü'
    )
    
    # Risk məlumatları
    total_risk_score = models.PositiveIntegerField(
        default=0, verbose_name='Ümumi Risk Xalı'
    )
    risk_level = models.CharField(
        max_length=20, choices=RiskLevel.choices,
        default=RiskLevel.LOW, verbose_name='Risk Səviyyəsi'
    )
    
    # Alt risk kateqoriyaları
    performance_risk_score = models.PositiveIntegerField(
        default=0, verbose_name='Performans Risk Xalı'
    )
    consistency_risk_score = models.PositiveIntegerField(
        default=0, verbose_name='Uyğunsuzluq Risk Xalı'
    )
    peer_feedback_risk_score = models.PositiveIntegerField(
        default=0, verbose_name='Həmkar Rəyi Risk Xalı'
    )
    behavioral_risk_score = models.PositiveIntegerField(
        default=0, verbose_name='Davranış Risk Xalı'
    )
    
    # Ətraflı analiz
    detailed_analysis = models.JSONField(
        default=dict, verbose_name='Ətraflı Analiz'
    )
    ai_recommendations = models.TextField(
        blank=True, verbose_name='AI Tövsiyələri'
    )
    
    # Tarixlər
    analyzed_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Analiz Tarixi'
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='Yenilənmə Tarixi'
    )
    
    # İdarə məlumatları
    reviewed_by_hr = models.BooleanField(
        default=False, verbose_name='HR tərəfindən nəzərdən keçirilib'
    )
    hr_action_taken = models.TextField(
        blank=True, verbose_name='HR-ın Tədbirləri'
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'İşçi Risk Analizi'
        verbose_name_plural = 'İşçi Risk Analizləri'
        unique_together = ['employee', 'cycle']
        ordering = ['-total_risk_score', '-analyzed_at']
        indexes = [
            models.Index(fields=['risk_level', 'analyzed_at']),
            models.Index(fields=['employee', 'cycle']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_risk_level_display()} ({self.total_risk_score})"
    
    @property
    def active_flags_count(self):
        return self.employee.risk_flags.filter(
            cycle=self.cycle,
            status=RiskFlag.Status.ACTIVE
        ).count()
    
    @property
    def critical_flags(self):
        return self.employee.risk_flags.filter(
            cycle=self.cycle,
            severity=RiskFlag.Severity.CRITICAL,
            status=RiskFlag.Status.ACTIVE
        )


class PsychologicalRiskSurvey(models.Model):
    """
    Psixoloji risk sorğuları - WHO-5 və digər standart sorğular
    """
    
    class SurveyType(models.TextChoices):
        WHO5_WELLBEING = 'WHO5_WELLBEING', 'WHO-5 Rifah İndeksi'
        BURNOUT_ASSESSMENT = 'BURNOUT_ASSESSMENT', 'Tükənmişlik Qiymətləndirməsi'
        STRESS_LEVEL = 'STRESS_LEVEL', 'Stress Səviyyəsi'
        JOB_SATISFACTION = 'JOB_SATISFACTION', 'İş Məmnunluğu'
        WORK_LIFE_BALANCE = 'WORK_LIFE_BALANCE', 'İş-Həyat Balansı'
    
    class RiskLevel(models.TextChoices):
        VERY_LOW = 'VERY_LOW', 'Çox Aşağı'
        LOW = 'LOW', 'Aşağı'
        MODERATE = 'MODERATE', 'Orta'
        HIGH = 'HIGH', 'Yüksək'
        VERY_HIGH = 'VERY_HIGH', 'Çox Yüksək'
    
    title = models.CharField(
        max_length=200, verbose_name='Sorğu Adı'
    )
    survey_type = models.CharField(
        max_length=50, choices=SurveyType.choices,
        verbose_name='Sorğu Növü'
    )
    questions = models.JSONField(
        verbose_name='Suallar'
    )
    is_active = models.BooleanField(
        default=True, verbose_name='Aktivdir'
    )
    is_anonymous = models.BooleanField(
        default=True, verbose_name='Anonimldir'
    )
    
    # Nəticə hesablama parametrləri
    scoring_method = models.JSONField(
        default=dict, verbose_name='Hesablama Metodu'
    )
    risk_thresholds = models.JSONField(
        default=dict, verbose_name='Risk Hədd Dəyərləri'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Yaradılma Tarixi'
    )
    created_by = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True,
        verbose_name='Yaradan'
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Psixoloji Risk Sorğusu'
        verbose_name_plural = 'Psixoloji Risk Sorğuları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_survey_type_display()})"


class PsychologicalRiskResponse(models.Model):
    """
    Psixoloji risk sorğularına cavablar
    """
    
    survey = models.ForeignKey(
        PsychologicalRiskSurvey, on_delete=models.CASCADE,
        related_name='responses', verbose_name='Sorğu'
    )
    employee = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name='psych_responses', verbose_name='İşçi'
    )
    
    # Cavablar
    answers = models.JSONField(
        verbose_name='Cavablar'
    )
    total_score = models.FloatField(
        default=0.0, verbose_name='Ümumi Bal'
    )
    risk_level = models.CharField(
        max_length=20, choices=PsychologicalRiskSurvey.RiskLevel.choices,
        default=PsychologicalRiskSurvey.RiskLevel.LOW,
        verbose_name='Risk Səviyyəsi'
    )
    
    # Anonimlik
    is_anonymous_response = models.BooleanField(
        default=True, verbose_name='Anonim Cavab'
    )
    
    # Tarixlər
    responded_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Cavab Tarixi'
    )
    
    # AI analizi
    ai_analysis = models.JSONField(
        default=dict, blank=True, verbose_name='AI Analizi'
    )
    requires_attention = models.BooleanField(
        default=False, verbose_name='Diqqət Tələb Edir'
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Psixoloji Risk Cavabı'
        verbose_name_plural = 'Psixoloji Risk Cavabları'
        unique_together = ['survey', 'employee']
        ordering = ['-responded_at']
        indexes = [
            models.Index(fields=['risk_level', 'requires_attention']),
            models.Index(fields=['survey', 'responded_at']),
        ]
    
    def __str__(self):
        employee_name = self.employee.get_full_name() if not self.is_anonymous_response else "Anonim"
        return f"{employee_name} - {self.survey.title} ({self.get_risk_level_display()})"
    
    def calculate_risk_level(self):
        """Cavablara əsasən risk səviyyəsini hesabla"""
        thresholds = self.survey.risk_thresholds
        
        if self.total_score >= thresholds.get('very_high', 80):
            return PsychologicalRiskSurvey.RiskLevel.VERY_HIGH
        elif self.total_score >= thresholds.get('high', 60):
            return PsychologicalRiskSurvey.RiskLevel.HIGH
        elif self.total_score >= thresholds.get('moderate', 40):
            return PsychologicalRiskSurvey.RiskLevel.MODERATE
        elif self.total_score >= thresholds.get('low', 20):
            return PsychologicalRiskSurvey.RiskLevel.LOW
        else:
            return PsychologicalRiskSurvey.RiskLevel.VERY_LOW


class IdeaComment(models.Model):
    """İdeyalara şərhlər"""
    
    idea = models.ForeignKey(
        Idea, on_delete=models.CASCADE,
        related_name="comments", verbose_name="İdeya"
    )
    author = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="idea_comments", verbose_name="Müəllif"
    )
    content = models.TextField(verbose_name="Məzmun")
    is_anonymous = models.BooleanField(default=False, verbose_name="Anonim")
    
    # Hierarchy (nested comments)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name="replies", verbose_name="Ana Şərh"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə Tarixi")
    
    # Moderasiya
    is_hidden = models.BooleanField(default=False, verbose_name="Gizlədilmiş")
    hidden_reason = models.CharField(max_length=200, blank=True, verbose_name="Gizlətmə Səbəbi")
    
    class Meta:
        verbose_name = "İdeya Şərhi"
        verbose_name_plural = "İdeya Şərhləri"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['idea', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.author.get_full_name()} -> {self.idea.title}"
    
    def get_author_display(self):
        """Anonim olub olmadığına görə müəllifi qaytarır"""
        if self.is_anonymous:
            return "Anonim İşçi"
        return self.author.get_full_name()

    history = HistoricalRecords()


# === LMS (LEARNING MANAGEMENT SYSTEM) MODELS ===

class TrainingCategory(models.Model):
    """Təlim kateqoriyaları"""
    
    name = models.CharField(max_length=100, verbose_name="Kateqoriya Adı")
    description = models.TextField(blank=True, verbose_name="Təsvir")
    icon = models.CharField(max_length=50, default="fas fa-graduation-cap", verbose_name="İkon")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Rəng")
    is_active = models.BooleanField(default=True, verbose_name="Aktivdir")
    
    class Meta:
        verbose_name = "Təlim Kateqoriyası"
        verbose_name_plural = "Təlim Kateqoriyaları"
        ordering = ['name']
    
    def __str__(self):
        return self.name

    history = HistoricalRecords()


class TrainingProgram(models.Model):
    """Təlim proqramları"""
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Layihə'
        ACTIVE = 'ACTIVE', 'Aktiv'
        COMPLETED = 'COMPLETED', 'Tamamlandı'
        CANCELLED = 'CANCELLED', 'Ləğv edildi'
        ARCHIVED = 'ARCHIVED', 'Arxivləşdirilib'
    
    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Başlanğıc'
        INTERMEDIATE = 'INTERMEDIATE', 'Orta'
        ADVANCED = 'ADVANCED', 'İrəli'
        EXPERT = 'EXPERT', 'Ekspert'
    
    title = models.CharField(max_length=200, verbose_name="Proqram Adı")
    description = models.TextField(verbose_name="Təsvir")
    category = models.ForeignKey(
        TrainingCategory, on_delete=models.SET_NULL, null=True,
        related_name="programs", verbose_name="Kateqoriya"
    )
    
    # Proqram məlumatları
    duration_hours = models.PositiveIntegerField(verbose_name="Müddət (saat)")
    difficulty_level = models.CharField(
        max_length=15, choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER, verbose_name="Çətinlik Səviyyəsi"
    )
    max_participants = models.PositiveIntegerField(
        default=20, verbose_name="Maksimum İştirakçı"
    )
    
    # Status və tarixlər
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.DRAFT, verbose_name="Status"
    )
    start_date = models.DateField(verbose_name="Başlama Tarixi")
    end_date = models.DateField(verbose_name="Bitmə Tarixi")
    registration_deadline = models.DateField(verbose_name="Qeydiyyat Son Tarixi")
    
    # Təlimçi məlumatları
    instructor = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True,
        related_name="taught_programs", verbose_name="Təlimçi"
    )
    external_instructor = models.CharField(
        max_length=200, blank=True, verbose_name="Xarici Təlimçi"
    )
    
    # Məkan və format
    location = models.CharField(max_length=200, blank=True, verbose_name="Məkan")
    is_online = models.BooleanField(default=False, verbose_name="Online")
    meeting_link = models.URLField(blank=True, verbose_name="Görüş Linki")
    
    # Sertifikat
    provides_certificate = models.BooleanField(default=True, verbose_name="Sertifikat Verir")
    certificate_template = models.TextField(blank=True, verbose_name="Sertifikat Şablonu")
    
    # Metadata
    prerequisites = models.TextField(blank=True, verbose_name="Ön Şərtlər")
    learning_objectives = models.TextField(blank=True, verbose_name="Öyrənmə Məqsədləri")
    materials_needed = models.TextField(blank=True, verbose_name="Lazım olan Materiallar")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    created_by = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True,
        related_name="created_programs", verbose_name="Yaradan"
    )
    
    class Meta:
        verbose_name = "Təlim Proqramı"
        verbose_name_plural = "Təlim Proqramları"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['category', 'difficulty_level']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def available_spots(self):
        """Boş yerlərin sayı"""
        enrolled_count = self.enrollments.filter(status='ENROLLED').count()
        return max(0, self.max_participants - enrolled_count)
    
    @property
    def is_full(self):
        """Proqram doludur"""
        return self.available_spots == 0
    
    @property
    def enrollment_open(self):
        """Qeydiyyat açıqdır"""
        from django.utils import timezone
        return (self.status == self.Status.ACTIVE and 
                timezone.now().date() <= self.registration_deadline)

    history = HistoricalRecords()


class TrainingEnrollment(models.Model):
    """Təlim proqramlarına qeydiyyat"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Gözləmədə'
        ENROLLED = 'ENROLLED', 'Qeydiyyatdan keçib'
        COMPLETED = 'COMPLETED', 'Tamamladı'
        FAILED = 'FAILED', 'Uğursuz'
        CANCELLED = 'CANCELLED', 'Ləğv edildi'
        NO_SHOW = 'NO_SHOW', 'Gəlmədi'
    
    program = models.ForeignKey(
        TrainingProgram, on_delete=models.CASCADE,
        related_name="enrollments", verbose_name="Proqram"
    )
    employee = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="training_enrollments", verbose_name="İşçi"
    )
    
    # Status və tarixlər
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.PENDING, verbose_name="Status"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="Qeydiyyat Tarixi")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlama Tarixi")
    
    # Nəticələr
    attendance_rate = models.FloatField(
        default=0.0, verbose_name="İştirak Faizi"
    )
    final_score = models.FloatField(
        null=True, blank=True, verbose_name="Final Balı"
    )
    feedback_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(i, f"{i} ulduz") for i in range(1, 6)],
        verbose_name="Geri Bildirim Reytinqi"
    )
    feedback_comments = models.TextField(blank=True, verbose_name="Geri Bildirim Şərhləri")
    
    # Sertifikat
    certificate_issued = models.BooleanField(default=False, verbose_name="Sertifikat Verilib")
    certificate_number = models.CharField(max_length=50, blank=True, verbose_name="Sertifikat Nömrəsi")
    
    class Meta:
        verbose_name = "Təlim Qeydiyyatı"
        verbose_name_plural = "Təlim Qeydiyyatları"
        unique_together = ['program', 'employee']
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['program', 'status']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.program.title}"
    
    def complete(self, score=None, issue_certificate=True):
        """Təlimi tamamlanmış kimi işarələ"""
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if score is not None:
            self.final_score = score
        
        if issue_certificate and self.program.provides_certificate:
            self.issue_certificate()
        
        self.save()
    
    def issue_certificate(self):
        """Sertifikat ver"""
        if not self.certificate_issued and self.status == self.Status.COMPLETED:
            import uuid
            self.certificate_number = f"CERT-{uuid.uuid4().hex[:8].upper()}"
            self.certificate_issued = True
            self.save()

    history = HistoricalRecords()


class Skill(models.Model):
    """Bacarıqlar"""
    
    class SkillType(models.TextChoices):
        TECHNICAL = 'TECHNICAL', 'Texniki'
        SOFT = 'SOFT', 'Yumşaq Bacarıq'
        LEADERSHIP = 'LEADERSHIP', 'Liderlik'
        LANGUAGE = 'LANGUAGE', 'Dil'
        DOMAIN = 'DOMAIN', 'Sahə Bilikləri'
    
    name = models.CharField(max_length=100, verbose_name="Bacarıq Adı")
   
    description = models.TextField(blank=True, verbose_name="Təsvir")
    skill_type = models.CharField(
        max_length=15, choices=SkillType.choices,
        default=SkillType.TECHNICAL, verbose_name="Bacarıq Növü"
    )
    parent_skill = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name="sub_skills", verbose_name="Ana Bacarıq"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktivdir")
    
    class Meta:
        verbose_name = "Bacarıq"
        verbose_name_plural = "Bacarıqlar"
        ordering = ['skill_type', 'name']
    
    def __str__(self):
        return self.name

    history = HistoricalRecords()


class EmployeeSkill(models.Model):
    """İşçilərin bacarıqları"""
    
    class ProficiencyLevel(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Başlanğıc (1-2)'
        INTERMEDIATE = 'INTERMEDIATE', 'Orta (3-4)'
        ADVANCED = 'ADVANCED', 'İrəli (5-6)'
        EXPERT = 'EXPERT', 'Ekspert (7-8)'
        MASTER = 'MASTER', 'Usta (9-10)'
    
    employee = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="skills", verbose_name="İşçi"
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE,
        related_name="employee_skills", verbose_name="Bacarıq"
    )
    
    # Bacarıq səviyyəsi (1-10)
    current_level = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 11)],
        default=1, verbose_name="Mövcud Səviyyə"
    )
    target_level = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 11)],
        default=5, verbose_name="Hədəf Səviyyə"
    )
    proficiency_level = models.CharField(
        max_length=15, choices=ProficiencyLevel.choices,
        default=ProficiencyLevel.BEGINNER, verbose_name="Bacarıq Səviyyəsi"
    )
    
    # Təsdiq məlumatları
    self_assessed = models.BooleanField(default=True, verbose_name="Özqiymətləndirmə")
    manager_confirmed = models.BooleanField(default=False, verbose_name="Rəhbər Təsdiqlədi")
    last_assessment_date = models.DateField(
        auto_now_add=True, verbose_name="Son Qiymətləndirmə Tarixi"
    )
    
    # Progress tracking
    improvement_notes = models.TextField(blank=True, verbose_name="İnkişaf Qeydləri")
    recommended_trainings = models.ManyToManyField(
        TrainingProgram, blank=True,
        related_name="recommended_for_skills", verbose_name="Tövsiyə olunan Təlimlər"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə Tarixi")
    
    class Meta:
        verbose_name = "İşçi Bacarığı"
        verbose_name_plural = "İşçi Bacarıqları"
        unique_together = ['employee', 'skill']
        ordering = ['-current_level', 'skill__name']
        indexes = [
            models.Index(fields=['employee', 'current_level']),
            models.Index(fields=['current_level', 'target_level']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.skill.name} ({self.current_level}/10)"
    
    @property
    def skill_type(self):
        return self.skill.skill_type
    
    @property
    def skill_gap(self):
        """Bacarıq boşluğu"""
        return max(0, self.target_level - self.current_level)
    
    @property
    def needs_improvement(self):
        """İnkişaf tələb edir"""
        return self.skill_gap > 0
    
    def update_proficiency_level(self):
        """Cari səviyyəyə əsasən bacarıq səviyyəsini yenilə"""
        if self.current_level <= 2:
            self.proficiency_level = self.ProficiencyLevel.BEGINNER
        elif self.current_level <= 4:
            self.proficiency_level = self.ProficiencyLevel.INTERMEDIATE
        elif self.current_level <= 6:
            self.proficiency_level = self.ProficiencyLevel.ADVANCED
        elif self.current_level <= 8:
            self.proficiency_level = self.ProficiencyLevel.EXPERT
        else:
            self.proficiency_level = self.ProficiencyLevel.MASTER
        self.save()

    history = HistoricalRecords()


class LearningPath(models.Model):
    """Öyrənmə yolları"""
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Layihə'
        ACTIVE = 'ACTIVE', 'Aktiv'
        COMPLETED = 'COMPLETED', 'Tamamlandı'
        PAUSED = 'PAUSED', 'Dayandırılıb'
        CANCELLED = 'CANCELLED', 'Ləğv edildi'
    
    title = models.CharField(max_length=200, verbose_name="Öyrənmə Yolu Adı")
    description = models.TextField(verbose_name="Təsvir")
    employee = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE,
        related_name="learning_paths", verbose_name="İşçi"
    )
    
    # Hədəf bacarıqlar
    target_skills = models.ManyToManyField(
        Skill, related_name="learning_paths",
        verbose_name="Hədəf Bacarıqlar"
    )
    
    # Status və progress
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.DRAFT, verbose_name="Status"
    )
    progress_percentage = models.FloatField(default=0.0, verbose_name="İrəliləyiş Faizi")
    
    # Tarixlər
    start_date = models.DateField(verbose_name="Başlama Tarixi")
    target_completion_date = models.DateField(verbose_name="Hədəf Tamamlama Tarixi")
    actual_completion_date = models.DateField(null=True, blank=True, verbose_name="Faktiki Tamamlama Tarixi")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma Tarixi")
    created_by = models.ForeignKey(
        Ishchi, on_delete=models.SET_NULL, null=True,
        related_name="created_learning_paths", verbose_name="Yaradan"
    )
    
    class Meta:
        verbose_name = "Öyrənmə Yolu"
        verbose_name_plural = "Öyrənmə Yolları"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['status', 'target_completion_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.title}"
    
    def calculate_progress(self):
        """Progress hesabla"""
        total_programs = self.programs.count()
        if total_programs == 0:
            return 0.0
        
        completed_programs = self.programs.filter(
            enrollment__status='COMPLETED'
        ).count()
        
        self.progress_percentage = (completed_programs / total_programs) * 100
        self.save()
        return self.progress_percentage
    
    @property
    def is_overdue(self):
        """Vaxtı keçib"""
        from django.utils import timezone
        return (self.status != self.Status.COMPLETED and 
                timezone.now().date() > self.target_completion_date)

    history = HistoricalRecords()


class LearningPathProgram(models.Model):
    """Öyrənmə yolundakı proqramlar"""
    
    learning_path = models.ForeignKey(
        LearningPath, on_delete=models.CASCADE,
        related_name="programs", verbose_name="Öyrənmə Yolu"
    )
    program = models.ForeignKey(
        TrainingProgram, on_delete=models.CASCADE,
        related_name="learning_paths", verbose_name="Proqram"
    )
    enrollment = models.ForeignKey(
        TrainingEnrollment, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Qeydiyyat"
    )
    
    # Sıralama və məcburiyyət
    order = models.PositiveIntegerField(default=1, verbose_name="Sıra")
    is_required = models.BooleanField(default=True, verbose_name="Məcburidir")
    prerequisite_completed = models.BooleanField(default=False, verbose_name="Ön şərt tamamlandı")
    
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Əlavə edilmə Tarixi")
    
    class Meta:
        verbose_name = "Öyrənmə Yolu Proqramı"
        verbose_name_plural = "Öyrənmə Yolu Proqramları"
        unique_together = ['learning_path', 'program']
        ordering = ['learning_path', 'order']
    
    def __str__(self):
        return f"{self.learning_path.title} - {self.program.title}"

    history = HistoricalRecords()


