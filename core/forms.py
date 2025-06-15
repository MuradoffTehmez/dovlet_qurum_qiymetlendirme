# core/forms.py - CAPTCHA ƏLAVƏ EDİLMİŞ VERSİYA

from django import forms
from django.contrib.auth.forms import (PasswordChangeForm, UserChangeForm, UserCreationForm)
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

# --- Captcha üçün yeni importlar ---
# from captcha.fields import ReCaptchaField
# from captcha.widgets import ReCaptchaV2Checkbox

# --- Lokal Modellər ---
from .models import (Hedef, InkishafPlani, Ishchi, OrganizationUnit, QiymetlendirmeDovru)


# --- 1. Qeydiyyat və Profil Formaları ---

class IshchiCreationForm(UserCreationForm):
    """Yeni istifadəçilərin qeydiyyatı üçün istifadə olunan forma."""
    dogum_tarixi = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Doğum Tarixi")
    
    # Captcha
    # captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox, label='')

    class Meta(UserCreationForm.Meta):
        model = Ishchi
        fields = UserCreationForm.Meta.fields + (
            'first_name', 'last_name', 'email', 'organization_unit', 
            'vezife', 'elaqe_nomresi', 
            # 'captcha', 
            'dogum_tarixi' 
        )
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt',
            'organization_unit': 'Təşkilati Vahid', 'vezife': 'Vəzifə',
            'elaqe_nomresi': 'Əlaqə Nömrəsi',
        }


class IshchiUpdateForm(UserChangeForm):
    """İstifadəçinin profil məlumatlarını yeniləməsi üçün forma."""
    password = None 
    profil_sekli = forms.ImageField(label='Profil Şəklini Yenilə', required=False, widget=forms.FileInput)
    dogum_tarixi = forms.DateField(label='Doğum Tarixi', widget=forms.DateInput(attrs={"type": "date"}), required=False)
    
    class Meta:
        model = Ishchi
        fields = ('first_name', 'last_name', 'email', 'vezife', 'organization_unit', 'elaqe_nomresi', 'dogum_tarixi', 'profil_sekli')
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt Ünvanı',
            'vezife': 'Vəzifəniz', 'organization_unit': 'Təşkilati Vahid', 'elaqe_nomresi': 'Əlaqə Nömrəsi',
        }


class IshchiPasswordChangeForm(PasswordChangeForm):
    """İstifadəçinin öz profilindən şifrəsini dəyişməsi üçün forma."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('change_password', 'Şifrəni Dəyişdir', css_class='btn-danger w-100 mt-3'))


# --- 2. Superadmin üçün Formalar ---

class YeniDovrForm(forms.ModelForm):
    """Superadminin yeni qiymətləndirmə dövrü yaratması üçün forma."""
    units = forms.ModelMultipleChoiceField(
        queryset=OrganizationUnit.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Qiymətləndirməyə Daxil Ediləcək Təşkilati Vahidlər",
    )
    class Meta:
        model = QiymetlendirmeDovru
        fields = ['ad', 'bashlama_tarixi', 'bitme_tarixi']
        labels = {'ad': 'Dövrün Adı (məs: 2025 - I Rübü)','bashlama_tarixi': 'Başlama Tarixi','bitme_tarixi': 'Bitmə Tarixi'}
        widgets = {'bashlama_tarixi': forms.DateInput(attrs={'type': 'date'}), 'bitme_tarixi': forms.DateInput(attrs={'type': 'date'})}


# --- 3. Fərdi İnkişaf Planı üçün Formalar ---

class HedefForm(forms.ModelForm):
    """Bir ədəd inkişaf hədəfi üçün istifadə olunan alt-forma."""
    class Meta:
        model = Hedef
        fields = ['tesvir', 'son_tarix', 'status']
        labels = {'tesvir': 'Hədəfin Təsviri', 'son_tarix': 'Son İcra Tarixi', 'status': 'Status'}
        widgets = {'tesvir': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Konkret və ölçüləbilən bir hədəf yazın...'}), 'son_tarix': forms.DateInput(attrs={'type': 'date'})}

HedefFormSet = inlineformset_factory(
    InkishafPlani, Hedef, form=HedefForm,
    extra=1, can_delete=True, min_num=1, validate_min=True
)