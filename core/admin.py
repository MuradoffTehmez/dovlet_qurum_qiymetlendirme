# core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import (Cavab, Departament, Ishchi, Qiymetlendirme,
                     QiymetlendirmeDovru, Sektor, Shobe, Sual,
                     SualKateqoriyasi)


# Ishchi modeli üçün UserAdmin-i SimpleHistoryAdmin ilə birləşdiririk
# Bu, həm standart istifadəçi panelini, həm də tarixçə funksionallığını təmin edir.
@admin.register(Ishchi)
class IshchiHistoryAdmin(UserAdmin, SimpleHistoryAdmin):
    list_display = ('username', 'first_name', 'last_name', 'rol', 'sektor')
    list_filter = ('rol', 'sektor__shobe__departament', 'sektor__shobe', 'is_staff', 'is_active')
    
    # Redaktə səhifəsinə bizim xüsusi sahələrimizi əlavə edirik
    fieldsets = UserAdmin.fieldsets + (
        ('Təşkilati Məlumatlar', {'fields': ('rol', 'vezife', 'sektor')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Təşkilati Məlumatlar', {'fields': ('rol', 'vezife', 'sektor')}),
    )

# --- İyerarxiya modelləri ---
class ShobeInline(admin.TabularInline):
    model = Shobe
    extra = 1

class SektorInline(admin.TabularInline):
    model = Sektor
    extra = 1

@admin.register(Departament)
class DepartamentAdmin(SimpleHistoryAdmin):
    list_display = ('ad',)
    search_fields = ('ad',)
    inlines = [ShobeInline]

@admin.register(Shobe)
class ShobeAdmin(SimpleHistoryAdmin):
    list_display = ('ad', 'departament')
    list_filter = ('departament',)
    search_fields = ('ad', 'departament__ad')
    inlines = [SektorInline]
    
@admin.register(Sektor)
class SektorAdmin(SimpleHistoryAdmin):
    list_display = ('ad', 'shobe')
    list_filter = ('shobe__departament', 'shobe')
    search_fields = ('ad', 'shobe__ad')

# --- Sual hovuzu modelləri ---
@admin.register(Sual)
class SualAdmin(SimpleHistoryAdmin):
    list_display = ('metn', 'kateqoriya', 'yaradan')
    list_filter = ('kateqoriya', 'departament', 'shobe', 'sektor')
    search_fields = ('metn',)

@admin.register(SualKateqoriyasi)
class SualKateqoriyasiAdmin(SimpleHistoryAdmin):
    list_display = ('ad',)

# --- Qiymətləndirmə prosesi modelləri ---
@admin.register(QiymetlendirmeDovru)
class QiymetlendirmeDovruAdmin(SimpleHistoryAdmin):
    list_display = ('ad', 'bashlama_tarixi', 'bitme_tarixi', 'aktivdir')
    list_filter = ('aktivdir',)

class CavabInline(admin.TabularInline):
    model = Cavab
    extra = 0
    readonly_fields = ('sual', 'xal', 'metnli_rey')

@admin.register(Qiymetlendirme)
class QiymetlendirmeAdmin(SimpleHistoryAdmin):
    list_display = ('dovr', 'qiymetlendirilen', 'qiymetlendiren', 'status')
    list_filter = ('dovr', 'status')
    search_fields = ('qiymetlendirilen__username', 'qiymetlendiren__username')
    inlines = [CavabInline]

@admin.register(Cavab)
class CavabAdmin(SimpleHistoryAdmin):
    list_display = ('sual', 'xal', 'qiymetlendirme')
    search_fields = ('qiymetlendirme__qiymetlendirilen__username',)


from .models import Hedef, InkishafPlani  # Yeni modelləri import edirik


class HedefInline(admin.TabularInline):
    """Hədəfləri birbaşa İnkişaf Planının içində göstərmək üçün inline."""
    model = Hedef
    extra = 1 # Varsayılan olaraq 1 ədəd boş hədəf sahəsi göstərir
    fields = ('tesvir', 'son_tarix', 'status')


@admin.register(InkishafPlani)
class InkishafPlaniAdmin(SimpleHistoryAdmin):
    """Fərdi İnkişaf Planı üçün admin paneli."""
    list_display = ('ishchi', 'dovr', 'status', 'yaradilma_tarixi')
    list_filter = ('status', 'dovr')
    search_fields = ('ishchi__username', 'ishchi__first_name', 'ishchi__last_name')
    inlines = [HedefInline] # Hədəfləri bura daxil edirik