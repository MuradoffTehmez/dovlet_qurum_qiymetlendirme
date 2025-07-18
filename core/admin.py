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
