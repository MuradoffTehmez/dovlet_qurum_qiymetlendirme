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
    ad = models.CharField(max_length=255, verbose_name="Dövrün Adı (məs: 2025 Q1)")
    bashlama_tarixi = models.DateField()
    bitme_tarixi = models.DateField()
    aktivdir = models.BooleanField(default=True)

    def __str__(self):
        return self.ad

    history = HistoricalRecords()


class Qiymetlendirme(models.Model):
    class Status(models.TextChoices):
        GOZLEMEDE = "GOZLEMEDE", "Gözləmədə"
        TAMAMLANDI = "TAMAMLANDI", "Tamamlandı"

    dovr = models.ForeignKey(QiymetlendirmeDovru, on_delete=models.CASCADE)
    qiymetlendirilen = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE, related_name="verilen_qiymetler"
    )
    qiymetlendiren = models.ForeignKey(
        Ishchi, on_delete=models.CASCADE, related_name="etdiyi_qiymetler"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.GOZLEMEDE
    )

    class Meta:
        unique_together = ("dovr", "qiymetlendirilen", "qiymetlendiren")

    def __str__(self):
        return f"{self.qiymetlendiren} -> {self.qiymetlendirilen} ({self.dovr.ad})"

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
