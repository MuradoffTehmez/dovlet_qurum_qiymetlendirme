# core/forms.py

from django import forms
from .models import QiymetlendirmeDovru, Departament, Ishchi
from django.contrib.auth.forms import UserCreationForm

# Crispy Forms üçün importlar
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

class YeniDovrForm(forms.ModelForm):
    departamentler = forms.ModelMultipleChoiceField(
        queryset=Departament.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Qiymətləndirməyə Daxil Ediləcək Departamentlər"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formun görünüşünü təyin edən helper yaradırıq
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('ad', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('bashlama_tarixi', css_class='form-group col-md-6 mb-0'),
                Column('bitme_tarixi', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'departamentler',
            Submit('submit', 'Dövrü Yarat və Başlat', css_class='btn-primary mt-3')
        )

    class Meta:
        model = QiymetlendirmeDovru
        fields = ['ad', 'bashlama_tarixi', 'bitme_tarixi']
        labels = {
            'ad': 'Dövrün Adı (məs: 2025 - III Rübü)',
        }
        widgets = {
            'bashlama_tarixi': forms.DateInput(attrs={'type': 'date'}),
            'bitme_tarixi': forms.DateInput(attrs={'type': 'date'}),
        }


class IshchiCreationForm(UserCreationForm):
    # ... bu hissə olduğu kimi qalır ...
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