# core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Departament, Shobe, Sektor, Ishchi, 
    SualKateqoriyasi, Sual, 
    QiymetlendirmeDovru, Qiymetlendirme, Cavab
)

# --- İstifadəçi Admin Panelini Tənzimləmək ---
# Bizim xüsusi Ishchi modelimiz üçün admin panelini genişləndiririk
class IshchiAdmin(UserAdmin):
    # Siyahıda görünəcək sahələr
    list_display = ('username', 'first_name', 'last_name', 'rol', 'sektor', 'is_staff')
    # Filtrləmə üçün istifadə olunacaq sahələr
    list_filter = ('rol', 'sektor__shobe__departament', 'sektor__shobe', 'sektor', 'is_staff')
    # Axtarış üçün istifadə olunacaq sahələr
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    # İstifadəçi redaktə səhifəsindəki sahələri qruplaşdırmaq
    # Orijinal UserAdmin fieldsets-i götürüb özümüzünküləri əlavə edirik
    fieldsets = UserAdmin.fieldsets + (
        ('Təşkilati Məlumatlar', {'fields': ('rol', 'vezife', 'sektor')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Təşkilati Məlumatlar', {'fields': ('rol', 'vezife', 'sektor')}),
    )

admin.site.register(Ishchi, IshchiAdmin)


# --- İyerarxiya Modellərini "Inline" Göstərmək ---
# Bu, bir departamentə baxanda onun altındakı şöbələri görməyə imkan verir

class ShobeInline(admin.TabularInline):
    model = Shobe
    extra = 1  # Əlavə boş sətir sayı

class SektorInline(admin.TabularInline):
    model = Sektor
    extra = 1

@admin.register(Departament)
class DepartamentAdmin(admin.ModelAdmin):
    list_display = ('ad',)
    search_fields = ('ad',)
    inlines = [ShobeInline]

@admin.register(Shobe)
class ShobeAdmin(admin.ModelAdmin):
    list_display = ('ad', 'departament')
    list_filter = ('departament',)
    search_fields = ('ad', 'departament__ad')
    inlines = [SektorInline]
    
@admin.register(Sektor)
class SektorAdmin(admin.ModelAdmin):
    list_display = ('ad', 'shobe')
    list_filter = ('shobe__departament', 'shobe')
    search_fields = ('ad', 'shobe__ad')


# --- Sual Hovuzu Admin Paneli ---
@admin.register(Sual)
class SualAdmin(admin.ModelAdmin):
    list_display = ('metn', 'kateqoriya', 'yaradan', 'departament', 'shobe', 'sektor')
    list_filter = ('kateqoriya', 'departament', 'shobe', 'sektor')
    search_fields = ('metn',)

admin.site.register(SualKateqoriyasi)


# --- Qiymətləndirmə Paneli ---

class CavabInline(admin.TabularInline):
    model = Cavab
    extra = 0 # Mövcud olmayan cavabları göstərməsin
    readonly_fields = ('sual', 'xal', 'metnli_rey') # Cavabları admin panelindən redaktə etməyə qoymuruq

@admin.register(Qiymetlendirme)
class QiymetlendirmeAdmin(admin.ModelAdmin):
    list_display = ('dovr', 'qiymetlendirilen', 'qiymetlendiren', 'status')
    list_filter = ('dovr', 'status')
    inlines = [CavabInline]

admin.site.register(QiymetlendirmeDovru)