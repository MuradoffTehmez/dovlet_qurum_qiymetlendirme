# core/forms.py
from django import forms
from .models import QiymetlendirmeDovru, Departament, Ishchi  # Ishchi modelini import edirik
from django.contrib.auth.forms import UserCreationForm  # Django-nun daxili formunu import edirik

class YeniDovrForm(forms.ModelForm):
    # Bu sahə QiymetlendirmeDovru modelində yoxdur, ona görə ayrıca təyin edirik
    departamentler = forms.ModelMultipleChoiceField(
        queryset=Departament.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Checkbox-lar kimi göstəririk
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

# YENİ QEYDİYYAT FORMU
class IshchiCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Ishchi  # Qeydiyyat zamanı istifadəçinin daxil edəcəyi sahələr
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'sektor', 'vezife')
        labels = {
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-poçt',
            'sektor': 'Sektor',
            'vezife': 'Vəzifəniz',
        }