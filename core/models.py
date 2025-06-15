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
