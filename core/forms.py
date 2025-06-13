# core/forms.py

# --- Django-nun Daxili Modulları ---
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.forms import inlineformset_factory

# --- Xarici Paketlər ---
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
# from captcha.fields import ReCaptchaField
# from captcha.widgets import ReCaptchaV2Checkbox


# --- Lokal Modellər ---
from .models import (
    QiymetlendirmeDovru, Departament, Ishchi, 
    Hedef, InkishafPlani, Sektor
)


# --- 1. Qeydiyyat və Profil Formaları ---

class IshchiCreationForm(UserCreationForm):
    dogum_tarixi = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Doğum Tarixi")

    class Meta(UserCreationForm.Meta):
        model = Ishchi
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'sektor', 'vezife', 'elaqe_nomresi', 'dogum_tarixi')
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt',
            'sektor': 'Sektor', 'vezife': 'Vəzifəniz',
            'elaqe_nomresi': 'Əlaqə Nömrəsi',
        }


class IshchiUpdateForm(UserChangeForm):
    """İstifadəçinin profil məlumatlarını yeniləməsi üçün forma."""
    password = None  # Bu formada şifrəni göstərmirik
    profil_sekli = forms.ImageField(label='Profil Şəklini Yenilə', required=False, widget=forms.FileInput)
    dogum_tarixi = forms.DateField(label='Doğum Tarixi', widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    class Meta:
        model = Ishchi
        fields = ('first_name', 'last_name', 'email', 'vezife', 'elaqe_nomresi', 'dogum_tarixi', 'profil_sekli')
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt Ünvanı',
            'vezife': 'Vəzifəniz', 'elaqe_nomresi': 'Əlaqə Nömrəsi',
        }

class IshchiPasswordChangeForm(PasswordChangeForm):
    """İstifadəçinin öz profilindən şifrəsini dəyişməsi üçün forma."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # Düyməyə ad veririk ki, view-da hansı formanın göndərildiyini bilək
        self.helper.add_input(Submit('change_password', 'Şifrəni Dəyişdir', css_class='btn-danger w-100 mt-3'))


# --- 2. Superadmin üçün Formalar ---

class YeniDovrForm(forms.ModelForm):
    """Superadminin yeni qiymətləndirmə dövrü yaratması üçün forma."""
    departamentler = forms.ModelMultipleChoiceField(
        queryset=Departament.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Qiymətləndirməyə Daxil Ediləcək Departamentlər"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(Column('ad', css_class='form-group col-md-12 mb-3')),
            Row(Column('bashlama_tarixi', css_class='form-group col-md-6 mb-3'), Column('bitme_tarixi', css_class='form-group col-md-6 mb-3')),
            'departamentler',
            Submit('submit', 'Dövrü Yarat və Başlat', css_class='btn-primary mt-4')
        )

    class Meta:
        model = QiymetlendirmeDovru
        fields = ['ad', 'bashlama_tarixi', 'bitme_tarixi']
        labels = {
            'ad': 'Dövrün Adı (məs: 2025 - III Rübü)',
            'bashlama_tarixi': 'Başlama Tarixi',
            'bitme_tarixi': 'Bitmə Tarixi',
        }
        widgets = {
            'bashlama_tarixi': forms.DateInput(attrs={'type': 'date'}),
            'bitme_tarixi': forms.DateInput(attrs={'type': 'date'}),
        }


# --- 3. Fərdi İnkişaf Planı üçün Formalar ---

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

# Bir İnkişaf Planına bir neçə hədəfi eyni anda əlavə etmək üçün FormSet
HedefFormSet = inlineformset_factory(
    InkishafPlani,
    Hedef,
    form=HedefForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
