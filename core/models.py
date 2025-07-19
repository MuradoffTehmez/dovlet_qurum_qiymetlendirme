from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords


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
        cavablar = self.cavablar.all()
        if not cavablar.exists():
            return 0
        
        total_score = sum(cavab.xal for cavab in cavablar)
        return round(total_score / cavablar.count(), 2)

    def get_completion_percentage(self):
        """Qiymətləndirmənin tamamlanma faizini hesablayır"""
        total_questions = self.dovr.suallar.count() if hasattr(self.dovr, 'suallar') else 0
        answered_questions = self.cavablar.count()
        
        if total_questions == 0:
            return 0
        
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


