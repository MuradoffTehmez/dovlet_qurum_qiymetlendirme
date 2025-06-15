# core/forms.py - BÜTÜN FORMALARLA BİRLİKDƏ YEKUN VERSİYA

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
    """Yeni istifadəçi qeydiyyat formu"""
    class Meta(UserCreationForm.Meta):
        model = Ishchi
        fields = UserCreationForm.Meta.fields + (
            'first_name', 'last_name', 'email', 'organization_unit', 
            'vezife', 'elaqe_nomresi', 'dogum_tarixi'
        )
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt',
            'organization_unit': 'Təşkilati Vahid', 'vezife': 'Vəzifə',
            'elaqe_nomresi': 'Əlaqə Nömrəsi', 'dogum_tarixi': 'Doğum Tarixi',
        }
        widgets = {
            'dogum_tarixi': forms.DateInput(attrs={'type': 'date'}),
        }

class IshchiUpdateForm(UserChangeForm):
    """Profil yeniləmə formu"""
    password = None
    profil_sekli = forms.ImageField(label="Profil Şəklini Yenilə", required=False, widget=forms.FileInput)
    dogum_tarixi = forms.DateField(label="Doğum Tarixi", widget=forms.DateInput(attrs={"type": "date"}), required=False)

    class Meta:
        model = Ishchi
        fields = ('first_name', 'last_name', 'email', 'organization_unit', 'vezife', 'elaqe_nomresi', 'dogum_tarixi', 'profil_sekli')
        labels = {
            'first_name': 'Ad', 'last_name': 'Soyad', 'email': 'E-poçt',
            'vezife': 'Vəzifə', 'organization_unit': 'Təşkilati Vahid',
            'elaqe_nomresi': 'Əlaqə Nömrəsi',
        }

# --- ƏSKİK OLAN HİSSƏ ---
class IshchiPasswordChangeForm(PasswordChangeForm):
    """Şifrə dəyişmə formu"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit("change_password", "Şifrəni Dəyişdir", css_class="btn-danger w-100 mt-3"))
# --- /ƏSKİK OLAN HİSSƏ ---

class YeniDovrForm(forms.ModelForm):
    """Yeni qiymətləndirmə dövrü formu"""
    units = forms.ModelMultipleChoiceField(
        queryset=OrganizationUnit.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Qiymətləndirməyə Daxil Ediləcək Təşkilati Vahidlər"
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(); self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(Column("ad", css_class="form-group col-md-12 mb-3")),
            Row(Column("bashlama_tarixi", css_class="form-group col-md-6 mb-3"), Column("bitme_tarixi", css_class="form-group col-md-6 mb-3")),
            "units",
            Submit("submit", "Dövrü Yarat və Başlat", css_class="btn-primary mt-4")
        )
    class Meta:
        model = QiymetlendirmeDovru
        fields = ["ad", "bashlama_tarixi", "bitme_tarixi"]
        widgets = {"bashlama_tarixi": forms.DateInput(attrs={"type": "date"}), "bitme_tarixi": forms.DateInput(attrs={"type": "date"})}

class HedefForm(forms.ModelForm):
    """İnkişaf planı hədəfləri formu"""
    class Meta:
        model = Hedef
        fields = ["tesvir", "son_tarix", "status"]
        labels = {"tesvir": "Hədəfin Təsviri", "son_tarix": "Son Tarix", "status": "Status"}
        widgets = {
            "tesvir": forms.Textarea(attrs={"rows": 2, "placeholder": "Hədəfi aydın və ölçülə bilən şəkildə təsvir edin..."}),
            "son_tarix": forms.DateInput(attrs={"type": "date"}),
        }

HedefFormSet = inlineformset_factory(
    InkishafPlani, Hedef, form=HedefForm,
    extra=1, can_delete=True, min_num=1, validate_min=True
)