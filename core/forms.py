# core/forms.py - YENİ STRUKTURA UYĞUNLAŞDIRILMIŞ VƏ TƏMİZLƏNMİŞ

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

# Yeni struktura uyğun modelləri import edirik
from .models import (
    QiymetlendirmeDovru, Ishchi, OrganizationUnit, 
    Hedef, InkishafPlani
)


class IshchiCreationForm(UserCreationForm):
    """Yeni istifadəçilərin qeydiyyatı üçün forma."""
    organization_unit = forms.ModelChoiceField(
        queryset=OrganizationUnit.objects.all(),
        required=True, # Qeydiyyatda bu sahə məcburidir
        label="Təşkilati Vahid"
    )

    class Meta(UserCreationForm.Meta):
        model = Ishchi
        fields = UserCreationForm.Meta.fields + (
            'first_name', 'last_name', 'email', 'vezife', 
            'organization_unit', 'elaqe_nomresi', 'dogum_tarixi'
        )
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt',
            'vezife': 'Vəzifəniz', 'elaqe_nomresi': 'Əlaqə Nömrəsi',
            'dogum_tarixi': 'Doğum Tarixi',
        }


class IshchiUpdateForm(UserChangeForm):
    """İstifadəçinin profil məlumatlarını yeniləməsi üçün forma."""
    password = None # Bu formada şifrəni göstərmirik
    profil_sekli = forms.ImageField(label='Profil Şəklini Yenilə', required=False, widget=forms.FileInput)
    dogum_tarixi = forms.DateField(label='Doğum Tarixi', widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    class Meta:
        model = Ishchi
        fields = ('first_name', 'last_name', 'email', 'vezife', 'elaqe_nomresi', 'dogum_tarixi', 'profil_sekli', 'organization_unit')
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt Ünvanı',
            'vezife': 'Vəzifəniz', 'elaqe_nomresi': 'Əlaqə Nömrəsi',
            'organization_unit': 'Təşkilati Vahid',
        }


class YeniDovrForm(forms.ModelForm):
    """Superadminin yeni qiymətləndirmə dövrü yaratması üçün forma."""
    # Artıq "departamentler" deyil, "units" adlandırırıq
    units = forms.ModelMultipleChoiceField(
        queryset=OrganizationUnit.objects.all(), # Bütün unitləri seçmək olar
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Qiymətləndirməyə Daxil Ediləcək Təşkilati Vahidlər",
    )

    class Meta:
        model = QiymetlendirmeDovru
        fields = ['ad', 'bashlama_tarixi', 'bitme_tarixi']
        labels = {
            'ad': 'Dövrün Adı (məs: 2025 - I Rübü)',
            'bashlama_tarixi': 'Başlama Tarixi',
            'bitme_tarixi': 'Bitmə Tarixi',
        }
        widgets = {
            'bashlama_tarixi': forms.DateInput(attrs={'type': 'date'}),
            'bitme_tarixi': forms.DateInput(attrs={'type': 'date'}),
        }


class HedefForm(forms.ModelForm):
    """Bir ədəd inkişaf hədəfi üçün istifadə olunan alt-forma."""
    class Meta:
        model = Hedef
        fields = ['tesvir', 'son_tarix', 'status']
        labels = {
            'tesvir': 'Hədəfin Təsviri',
            'son_tarix': 'Son İcra Tarixi',
            'status': 'Status',
        }
        widgets = {
            'tesvir': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Konkret və ölçüləbilən bir hədəf yazın...'}),
            'son_tarix': forms.DateInput(attrs={'type': 'date'}),
        }


HedefFormSet = inlineformset_factory(
    InkishafPlani,
    Hedef,
    form=HedefForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)