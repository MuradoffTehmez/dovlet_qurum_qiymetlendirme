# core/forms.py - Modern və İnteraktiv Formalar

from django import forms
from django.contrib.auth.forms import (PasswordChangeForm, UserChangeForm, UserCreationForm)
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div, HTML, Field
from crispy_forms.bootstrap import PrependedText, AppendedText
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

# --- Lokal Modellər ---
from .models import (Hedef, InkishafPlani, Ishchi, OrganizationUnit, QiymetlendirmeDovru, Feedback)


# --- Modern Widget Sinifləri ---

class ModernTextInput(forms.TextInput):
    """Müasir text input widget"""
    def __init__(self, placeholder="", icon=None, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'form-control')
        attrs.setdefault('placeholder', placeholder)
        if icon:
            attrs.setdefault('data-icon', icon)
        super().__init__(*args, **kwargs)

class ModernEmailInput(forms.EmailInput):
    """Müasir email input widget"""
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'form-control')
        attrs.setdefault('placeholder', 'email@example.com')
        attrs.setdefault('data-icon', 'fas fa-envelope')
        super().__init__(*args, **kwargs)

class ModernPasswordInput(forms.PasswordInput):
    """Müasir password input widget"""
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'form-control')
        attrs.setdefault('data-icon', 'fas fa-lock')
        attrs.setdefault('data-toggle', 'password')
        super().__init__(*args, **kwargs)

class ModernDateInput(forms.DateInput):
    """Müasir tarix input widget"""
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('type', 'date')
        attrs.setdefault('class', 'form-control')
        attrs.setdefault('data-icon', 'fas fa-calendar')
        super().__init__(*args, **kwargs)

class ModernSelect(forms.Select):
    """Müasir select widget"""
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'form-select')
        attrs.setdefault('data-live-search', 'true')
        super().__init__(*args, **kwargs)

class ModernTextarea(forms.Textarea):
    """Müasir textarea widget"""
    def __init__(self, rows=4, placeholder="", *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'form-control')
        attrs.setdefault('rows', rows)
        attrs.setdefault('placeholder', placeholder)
        attrs.setdefault('data-autosize', 'true')
        super().__init__(*args, **kwargs)

class ModernFileInput(forms.FileInput):
    """Müasir file input widget"""
    def __init__(self, accept=None, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'form-control')
        if accept:
            attrs.setdefault('accept', accept)
        super().__init__(*args, **kwargs)


# --- 1. Qeydiyyat və Profil Formaları ---

class IshchiCreationForm(UserCreationForm):
    """Müasir qeydiyyat forması - Real-time validation və interaktiv UI"""
    
    # Telefon nömrəsi üçün validator
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Telefon nömrəsi düzgün formatda daxil edilməlidir."
    )
    
    first_name = forms.CharField(
        label='Ad',
        widget=ModernTextInput(placeholder="Adınızı daxil edin", icon="fas fa-user"),
        max_length=30
    )
    
    last_name = forms.CharField(
        label='Soyad',
        widget=ModernTextInput(placeholder="Soyadınızı daxil edin", icon="fas fa-user"),
        max_length=30
    )
    
    email = forms.EmailField(
        label='E-poçt ünvanı',
        widget=ModernEmailInput(),
        help_text="Aktiv e-poçt ünvanınızı daxil edin"
    )
    
    organization_unit = forms.ModelChoiceField(
        label='Təşkilati Vahid',
        queryset=OrganizationUnit.objects.all(),
        widget=ModernSelect(),
        empty_label="Təşkilati vahidi seçin..."
    )
    
    vezife = forms.CharField(
        label='Vəzifə',
        widget=ModernTextInput(placeholder="Vəzifənizi daxil edin", icon="fas fa-briefcase"),
        max_length=255
    )
    
    elaqe_nomresi = forms.CharField(
        label='Əlaqə Nömrəsi',
        widget=ModernTextInput(placeholder="+994501234567", icon="fas fa-phone"),
        validators=[phone_validator],
        required=False
    )
    
    dogum_tarixi = forms.DateField(
        label="Doğum Tarixi",
        widget=ModernDateInput(),
        required=False
    )

    class Meta(UserCreationForm.Meta):
        model = Ishchi
        fields = UserCreationForm.Meta.fields + (
            'first_name', 'last_name', 'email', 'organization_unit', 
            'vezife', 'elaqe_nomresi', 'dogum_tarixi'
        )
        widgets = {
            'username': ModernTextInput(placeholder="İstifadəçi adı", icon="fas fa-user"),
            'password1': ModernPasswordInput(),
            'password2': ModernPasswordInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'modern-form'
        self.helper.layout = Layout(
            HTML('<div class="form-header mb-4"><h4><i class="fas fa-user-plus me-2"></i>Yeni İstifadəçi Qeydiyyatı</h4></div>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('organization_unit', css_class='form-group col-md-6 mb-3'),
                Column('vezife', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('elaqe_nomresi', css_class='form-group col-md-6 mb-3'),
                Column('dogum_tarixi', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', 'Qeydiyyatdan Keç', css_class='btn btn-primary btn-lg w-100'),
                css_class='text-center mt-4'
            )
        )
        
        # Sahələr üçün müasir atributlar
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'data-validation': 'true',
                'autocomplete': 'off'
            })


class IshchiUpdateForm(UserChangeForm):
    """Müasir profil yeniləmə forması"""
    password = None
    
    first_name = forms.CharField(
        label='Ad',
        widget=ModernTextInput(placeholder="Adınızı daxil edin", icon="fas fa-user"),
        max_length=30
    )
    
    last_name = forms.CharField(
        label='Soyad',
        widget=ModernTextInput(placeholder="Soyadınızı daxil edin", icon="fas fa-user"),
        max_length=30
    )
    
    email = forms.EmailField(
        label='E-poçt ünvanı',
        widget=ModernEmailInput()
    )
    
    vezife = forms.CharField(
        label='Vəzifə',
        widget=ModernTextInput(placeholder="Vəzifənizi daxil edin", icon="fas fa-briefcase"),
        max_length=255
    )
    
    organization_unit = forms.ModelChoiceField(
        label='Təşkilati Vahid',
        queryset=OrganizationUnit.objects.all(),
        widget=ModernSelect(),
        required=False
    )
    
    elaqe_nomresi = forms.CharField(
        label='Əlaqə Nömrəsi',
        widget=ModernTextInput(placeholder="+994501234567", icon="fas fa-phone"),
        required=False
    )
    
    dogum_tarixi = forms.DateField(
        label='Doğum Tarixi',
        widget=ModernDateInput(),
        required=False
    )
    
    profil_sekli = forms.ImageField(
        label='Profil Şəkli',
        widget=ModernFileInput(accept="image/*"),
        required=False,
        help_text="JPG, PNG formatlarında yükləyin (max 5MB)"
    )
    
    class Meta:
        model = Ishchi
        fields = ('first_name', 'last_name', 'email', 'vezife', 'organization_unit', 
                 'elaqe_nomresi', 'dogum_tarixi', 'profil_sekli')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.form_class = 'modern-form'
        self.helper.layout = Layout(
            HTML('<div class="form-header mb-4"><h4><i class="fas fa-user-edit me-2"></i>Profil Məlumatlarını Yenilə</h4></div>'),
            
            # Profil şəkli bölməsi
            HTML('<div class="profile-image-section mb-4">'),
            'profil_sekli',
            HTML('</div>'),
            
            # Şəxsi məlumatlar
            HTML('<h6 class="section-title"><i class="fas fa-user me-2"></i>Şəxsi Məlumatlar</h6>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('dogum_tarixi', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            
            # İş məlumatları
            HTML('<h6 class="section-title mt-4"><i class="fas fa-briefcase me-2"></i>İş Məlumatları</h6>'),
            Row(
                Column('vezife', css_class='form-group col-md-6 mb-3'),
                Column('organization_unit', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'elaqe_nomresi',
            
            Div(
                Submit('submit', 'Məlumatları Yenilə', css_class='btn btn-success btn-lg me-3'),
                HTML('<a href="{% url \'profil\' %}" class="btn btn-outline-secondary btn-lg">Ləğv Et</a>'),
                css_class='text-center mt-4'
            )
        )


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


# --- 4. Geri Bildirim və Şikayət Sistemi ---

class FeedbackForm(forms.ModelForm):
    """İnteraktiv və istifadəçi dostu geri bildirim forması"""
    
    title = forms.CharField(
        label='Başlıq',
        widget=ModernTextInput(
            placeholder="Geri bildiriminizin qısa başlığını yazın...",
            icon="fas fa-tag"
        ),
        max_length=200,
        help_text="Problemin və ya təklifin qısa təsvirini yazın"
    )
    
    description = forms.CharField(
        label='Ətraflı Məlumat',
        widget=ModernTextarea(
            rows=6,
            placeholder="Zəhmət olmasa, məlumatları ətraflı yazın. Problem necə yaranır? Nə etmək istəyirsiniz?"
        ),
        help_text="Daha ətraflı məlumat verməyiniz problemi daha tez həll etməyimizə kömək edir"
    )
    
    feedback_type = forms.ChoiceField(
        label='Geri Bildirim Növü',
        choices=Feedback.FeedbackType.choices,
        widget=ModernSelect(),
        help_text="Geri bildiriminizin növünü seçin"
    )
    
    priority = forms.ChoiceField(
        label='Prioritet',
        choices=Feedback.Priority.choices,
        widget=ModernSelect(),
        initial=Feedback.Priority.MEDIUM,
        help_text="Bu məsələnin sizin üçün vaciblik dərəcəsi"
    )
    
    attachment = forms.FileField(
        label='Əlavə Fayl (Screenshots, Sənədlər)',
        widget=ModernFileInput(accept=".jpg,.jpeg,.png,.pdf,.doc,.docx"),
        required=False,
        help_text="Problemi göstərən ekran şəkli və ya digər fayıllar yükləyə bilərsiniz (max 10MB)"
    )
    
    class Meta:
        model = Feedback
        fields = ['title', 'description', 'feedback_type', 'priority', 'attachment']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.form_class = 'modern-form feedback-form'
        self.helper.form_id = 'feedback-form'
        
        self.helper.layout = Layout(
            HTML('''
                <div class="feedback-header text-center mb-4">
                    <h3><i class="fas fa-comments me-2"></i>Geri Bildirim Göndər</h3>
                    <p class="text-muted">Təklifləriniz və şikayətləriniz bizim üçün dəyərlidir</p>
                </div>
            '''),
            
            # Ana məlumatlar
            HTML('<div class="card mb-4"><div class="card-body">'),
            HTML('<h6 class="card-title"><i class="fas fa-info-circle me-2"></i>Əsas Məlumatlar</h6>'),
            
            Row(
                Column('feedback_type', css_class='form-group col-md-6 mb-3'),
                Column('priority', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            
            'title',
            'description',
            HTML('</div></div>'),
            
            # Fayl yükləmə
            HTML('<div class="card mb-4"><div class="card-body">'),
            HTML('<h6 class="card-title"><i class="fas fa-paperclip me-2"></i>Əlavə Fayl</h6>'),
            'attachment',
            HTML('''
                <div class="form-text">
                    <small><i class="fas fa-info-circle me-1"></i> 
                    Dəstəklənən formatlar: JPG, PNG, PDF, DOC, DOCX (max 10MB)</small>
                </div>
            '''),
            HTML('</div></div>'),
            
            # Göndər düyməsi
            HTML('<div class="text-center">'),
            Submit('submit', 'Geri Bildirimi Göndər', css_class='btn btn-primary btn-lg px-5'),
            HTML('<div class="mt-3">'),
            HTML('<small class="text-muted"><i class="fas fa-clock me-1"></i> Orta cavab müddəti: 24-48 saat</small>'),
            HTML('</div></div>')
        )
        
        # JavaScript validasiya üçün atributlar
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'data-feedback-field': field_name,
                'data-required': 'required' if field.required else 'optional'
            })
    
    def clean_attachment(self):
        """Fayl yükləmə validasiyası"""
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Fayl ölçüsü yoxlaması (10MB)
            if attachment.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Fayl ölçüsü 10MB-dan çox ola bilməz.")
            
            # Fayl formatı yoxlaması
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
            import os
            ext = os.path.splitext(attachment.name)[1].lower()
            
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"Bu fayl formatı dəstəklənmir. İcazə verilən formatlar: {', '.join(allowed_extensions)}"
                )
        
        return attachment


class FeedbackResponseForm(forms.ModelForm):
    """Admin cavabı üçün forma"""
    
    admin_response = forms.CharField(
        label='Admin Cavabı',
        widget=ModernTextarea(
            rows=5,
            placeholder="İstifadəçiyə cavabınızı yazın..."
        ),
        help_text="Bu cavab istifadəçiyə e-poçt vasitəsilə göndəriləcək"
    )
    
    status = forms.ChoiceField(
        label='Status',
        choices=Feedback.Status.choices,
        widget=ModernSelect()
    )
    
    class Meta:
        model = Feedback
        fields = ['admin_response', 'status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'modern-form'
        
        self.helper.layout = Layout(
            HTML('<div class="card"><div class="card-body">'),
            HTML('<h6 class="card-title"><i class="fas fa-reply me-2"></i>İstifadəçiyə Cavab Ver</h6>'),
            
            'status',
            'admin_response',
            
            Div(
                Submit('submit', 'Cavabı Göndər', css_class='btn btn-success me-2'),
                HTML('<a href="#" class="btn btn-outline-secondary" onclick="history.back()">Geri</a>'),
                css_class='text-end mt-3'
            ),
            HTML('</div></div>')
        )