# --- Django-nun Daxili Modulları ---
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django import forms
from django.contrib.auth.forms import (PasswordChangeForm, UserChangeForm,
                                     UserCreationForm)
from django.forms import inlineformset_factory

# --- Lokal Modellər ---
from .models import (Hedef, InkishafPlani, Ishchi, OrganizationUnit,
                    QiymetlendirmeDovru)

class IshchiCreationForm(UserCreationForm):
    dogum_tarixi = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
        label="Doğum Tarixi",
    )
    organization_unit = forms.ModelChoiceField(
        queryset=OrganizationUnit.objects.all(),
        required=False,
        label="Təşkilati Vahid"
    )

    class Meta(UserCreationForm.Meta):
        model = Ishchi
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "organization_unit",  # sektor əvəzinə
            "vezife",
            "elaqe_nomresi",
            "dogum_tarixi",
        )
        labels = {
            "first_name": "Ad",
            "last_name": "Soyad",
            "email": "E-poçt",
            "organization_unit": "Təşkilati Vahid",
            "vezife": "Vəzifəniz",
            "elaqe_nomresi": "Əlaqə Nömrəsi",
        }


class IshchiUpdateForm(UserChangeForm):
    """İstifadəçinin profil məlumatlarını yeniləməsi üçün forma."""
    password = None
    profil_sekli = forms.ImageField(
        label="Profil Şəklini Yenilə", 
        required=False, 
        widget=forms.FileInput
    )
    dogum_tarixi = forms.DateField(
        label="Doğum Tarixi",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    organization_unit = forms.ModelChoiceField(
        queryset=OrganizationUnit.objects.all(),
        required=False,
        label="Təşkilati Vahid"
    )

    class Meta:
        model = Ishchi
        fields = (
            "first_name",
            "last_name",
            "email",
            "organization_unit",  # sektor əvəzinə
            "vezife",
            "elaqe_nomresi",
            "dogum_tarixi",
            "profil_sekli",
        )
        labels = {
            "organization_unit": "Təşkilati Vahid",
            # digər label'lər eyni qalır
        }


class YeniDovrForm(forms.ModelForm):
    """Superadminin yeni qiymətləndirmə dövrü yaratması üçün forma."""
    units = forms.ModelMultipleChoiceField(
        queryset=OrganizationUnit.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Qiymətləndirməyə Daxil Ediləcək Təşkilati Vahidlər",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(Column("ad", css_class="form-group col-md-12 mb-3")),
            Row(
                Column("bashlama_tarixi", css_class="form-group col-md-6 mb-3"),
                Column("bitme_tarixi", css_class="form-group col-md-6 mb-3"),
            ),
            "units",  # departamentler əvəzinə
            Submit("submit", "Dövrü Yarat və Başlat", css_class="btn-primary mt-4"),
        )

    class Meta:
        model = QiymetlendirmeDovru
        fields = ["ad", "bashlama_tarixi", "bitme_tarixi"]
        widgets = {
            "bashlama_tarixi": forms.DateInput(attrs={"type": "date"}),
            "bitme_tarixi": forms.DateInput(attrs={"type": "date"}),
        }


class HedefForm(forms.ModelForm):
    """Bir ədəd inkişaf hədəfi üçün istifadə olunan alt-forma."""
    class Meta:
        model = Hedef
        fields = ["tesvir", "son_tarix", "status"]
        widgets = {
            "son_tarix": forms.DateInput(attrs={"type": "date"}),
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