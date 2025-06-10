# core/forms.py

from django import forms
from .models import QiymetlendirmeDovru, Departament

class YeniDovrForm(forms.ModelForm):
    # Bu sahə QiymetlendirmeDovru modelində yoxdur, ona görə ayrıca təyin edirik
    departamentler = forms.ModelMultipleChoiceField(
        queryset=Departament.objects.all(),
        widget=forms.CheckboxSelectMultiple, # Checkbox-lar kimi göstəririk
        required=True,
        label="Qiymətləndirməyə Daxil Ediləcək Departamentlər"
    )

    class Meta:
        model = QiymetlendirmeDovru
        fields = ['ad', 'bashlama_tarixi', 'bitme_tarixi']
        labels = {
            'ad': 'Dövrün Adı (məs: 2025 - III Rübü)',
            'bashlama_tarixi': 'Başlama Tarixi',
            'bitme_tarixi': 'Bitmə Tarixi',
        }
        # Tarix sahələri üçün HTML5 date picker istifadə edirik
        widgets = {
            'bashlama_tarixi': forms.DateInput(attrs={'type': 'date'}),
            'bitme_tarixi': forms.DateInput(attrs={'type': 'date'}),
        }