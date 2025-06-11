# core/forms.py

from django import forms
from .models import QiymetlendirmeDovru, Departament, Ishchi
from django.contrib.auth.forms import UserCreationForm

# Crispy Forms üçün importlar
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit


from .models import Hedef
from django.forms import inlineformset_factory



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


# YENİ QEYDİYYAT FORMU - CRISPY HELPER İLƏ
class IshchiCreationForm(UserCreationForm):
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
            # Şifrə sahələri avtomatik olaraq UserCreationForm-dan gəlir
            # və crispy onları səliqəli şəkildə əlavə edəcək.
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


# Hədəf modeli üçün sadə bir ModelForm
class HedefForm(forms.ModelForm):
    class Meta:
        model = Hedef
        fields = ['tesvir', 'son_tarix', 'status']
        widgets = {
            'tesvir': forms.Textarea(attrs={'rows': 2}),
            'son_tarix': forms.DateInput(attrs={'type': 'date'}),
        }

# InkishafPlani və Hedef arasında əlaqə quran bir FormSet yaradırıq.
# Bu, bir plana bir neçə hədəfi eyni anda əlavə etməyə imkan verəcək.
HedefFormSet = inlineformset_factory(
    InkishafPlani,  # Əsas (valideyn) model
    Hedef,          # Inline (övlad) model
    form=HedefForm,
    extra=2,        # Varsayılan olaraq 2 ədəd boş hədəf formu göstər
    can_delete=True,# Hədəfləri silmək imkanı olsunmu?
    min_num=1,      # Ən azı 1 hədəf olmalıdır
)