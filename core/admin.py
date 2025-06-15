from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Cavab, Ishchi, Qiymetlendirme, QiymetlendirmeDovru,
    Sual, SualKateqoriyasi, Hedef, InkishafPlani, OrganizationUnit
)

# --- Ishchi modeli üçün admin ---
@admin.register(Ishchi)
class IshchiHistoryAdmin(UserAdmin, SimpleHistoryAdmin):
    list_display = ("username", "first_name", "last_name", "rol", "organization_unit")
    list_filter = (
        "rol",
        "organization_unit",
        "is_staff",
        "is_active",
    )
    fieldsets = UserAdmin.fieldsets + (
        ("Təşkilati Məlumatlar", {"fields": ("rol", "vezife", "organization_unit", "elaqe_nomresi", "dogum_tarixi", "profil_sekli")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Təşkilati Məlumatlar", {"fields": ("rol", "vezife", "organization_unit")}),
    )


# --- Yeni Struktur Vahidi modeli üçün admin ---
@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(SimpleHistoryAdmin):
    list_display = ("name", "type", "parent")
    list_filter = ("type", "parent")
    search_fields = ("name",)


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
    list_display = ("dovr", "qiymetlendirilen", "qiymetlendiren", "status")
    list_filter = ("dovr", "status")
    search_fields = ("qiymetlendirilen__username", "qiymetlendiren__username")
    inlines = [CavabInline]


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
    list_display = ("ishchi", "dovr", "status", "yaradilma_tarixi")
    list_filter = ("status", "dovr")
    search_fields = ("ishchi__username", "ishchi__first_name", "ishchi__last_name")
    inlines = [HedefInline]
