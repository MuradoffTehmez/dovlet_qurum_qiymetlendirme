# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

# --- İyerarxiya Modelləri ---

class Departament(models.Model):
    ad = models.CharField(max_length=255, verbose_name="Departamentin Adı")

    def __str__(self):
        return self.ad

class Shobe(models.Model):
    ad = models.CharField(max_length=255, verbose_name="Şöbənin Adı")
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE, related_name='shobeler')

    def __str__(self):
        return f"{self.departament.ad} / {self.ad}"

class Sektor(models.Model):
    ad = models.CharField(max_length=255, verbose_name="Sektorun Adı")
    shobe = models.ForeignKey(Shobe, on_delete=models.CASCADE, related_name='sektorler')

    def __str__(self):
        return f"{self.shobe.ad} / {self.ad}"

# --- Genişləndirilmiş İstifadəçi Modeli ---

class Ishchi(AbstractUser):
    class Rol(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', 'Superadmin'
        ADMIN = 'ADMIN', 'Admin'
        REHBER = 'REHBER', 'Rəhbər'
        ISHCHI = 'ISHCHI', 'İşçi'

    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.ISHCHI, verbose_name="İstifadəçi Rolu")
    vezife = models.CharField(max_length=255, verbose_name="Vəzifəsi", blank=True)
    sektor = models.ForeignKey(Sektor, on_delete=models.SET_NULL, null=True, blank=True, related_name='ishchiler')

# --- Sual Hovuzu Modelləri ---

class SualKateqoriyasi(models.Model):
    ad = models.CharField(max_length=255, verbose_name="Kompetensiya / Kateqoriya Adı")

    def __str__(self):
        return self.ad

class Sual(models.Model):
    metn = models.TextField(verbose_name="Sualın Mətni")
    kateqoriya = models.ForeignKey(SualKateqoriyasi, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Sualın ümumi və ya spesifik olduğunu təyin edir
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE, null=True, blank=True)
    shobe = models.ForeignKey(Shobe, on_delete=models.CASCADE, null=True, blank=True)
    sektor = models.ForeignKey(Sektor, on_delete=models.CASCADE, null=True, blank=True)
    
    yaradan = models.ForeignKey('Ishchi', on_delete=models.SET_NULL, null=True, verbose_name="Sualı Yaradan")

    def __str__(self):
        return self.metn[:50] + "..."

# --- Qiymətləndirmə Prosesi Modelləri ---

class QiymetlendirmeDovru(models.Model):
    ad = models.CharField(max_length=255, verbose_name="Dövrün Adı (məs: 2025 Q1)")
    bashlama_tarixi = models.DateField()
    bitme_tarixi = models.DateField()
    aktivdir = models.BooleanField(default=True)

    def __str__(self):
        return self.ad

class Qiymetlendirme(models.Model):
    class Status(models.TextChoices):
        GOZLEMEDE = 'GOZLEMEDE', 'Gözləmədə'
        TAMAMLANDI = 'TAMAMLANDI', 'Tamamlandı'
    
    dovr = models.ForeignKey(QiymetlendirmeDovru, on_delete=models.CASCADE)
    qiymetlendirilen = models.ForeignKey('Ishchi', on_delete=models.CASCADE, related_name='verilen_qiymetler')
    qiymetlendiren = models.ForeignKey('Ishchi', on_delete=models.CASCADE, related_name='etdiyi_qiymetler')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.GOZLEMEDE)
    
    class Meta:
        # Bir qiymətləndirən eyni dövrdə bir nəfəri yalnız bir dəfə qiymətləndirə bilər
        unique_together = ('dovr', 'qiymetlendirilen', 'qiymetlendiren')

    def __str__(self):
        return f"{self.qiymetlendiren} -> {self.qiymetlendirilen} ({self.dovr.ad})"

class Cavab(models.Model):
    qiymetlendirme = models.ForeignKey(Qiymetlendirme, on_delete=models.CASCADE, related_name='cavablar')
    sual = models.ForeignKey(Sual, on_delete=models.CASCADE)
    xal = models.PositiveSmallIntegerField(verbose_name="Verilən Xal (1-10)")
    metnli_rey = models.TextField(verbose_name="Əlavə Rəy", blank=True, null=True)

    def __str__(self):
        return f"{self.qiymetlendirme}: Sual {self.sual.id} - {self.xal} xal"