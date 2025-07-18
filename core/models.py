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
