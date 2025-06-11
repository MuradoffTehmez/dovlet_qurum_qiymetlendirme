# core/forms.py - YENİDƏN TƏŞKİL EDİLMİŞ VƏ DÜZƏLİŞ EDİLMİŞ VERSİYA

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory

# Crispy Forms üçün importlar
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

# Modelləri bir yerdə import edirik
from .models import (
    QiymetlendirmeDovru, Departament, Ishchi, 
    Hedef, InkishafPlani, Sektor
)
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm

# --- Qeydiyyat Formu ---

class IshchiCreationForm(UserCreationForm):
    """Yeni istifadəçilərin qeydiyyatı üçün istifadə olunan forma."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='form-group col-md-12 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                 Column('email', css_class='form-group col-md-12 mb-3'),
                css_class='form-row'
            ),
             Row(
                Column('sektor', css_class='form-group col-md-6 mb-3'),
                Column('vezife', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'password1',
            'password2',
            Submit('submit', 'Qeydiyyatdan Keç', css_class='btn-primary w-100 mt-3')
        )

    class Meta(UserCreationForm.Meta):
        model = Ishchi
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'sektor', 'vezife')
        labels = {
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-poçt',
            'sektor': 'Sektor',
            'vezife': 'Vəzifəniz',
        }


# --- Superadmin üçün Formalar ---

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
            Row(
                Column('ad', css_class='form-group col-md-12 mb-3'),
            ),
            Row(
                Column('bashlama_tarixi', css_class='form-group col-md-6 mb-3'),
                Column('bitme_tarixi', css_class='form-group col-md-6 mb-3'),
            ),
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


# --- Fərdi İnkişaf Planı üçün Formalar ---

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
    extra=1,        # Varsayılan olaraq 1 ədəd boş hədəf formu göstər
    can_delete=True,
    min_num=1,
    validate_min=True,
)