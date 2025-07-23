"""
Extended i18n template tags and filters
"""

from django import template
from django.utils.translation import gettext as _
from django.utils import translation
from django.conf import settings
from core.i18n_utils import i18n_manager, translation_manager

register = template.Library()


@register.filter
def localize_number(value, decimal_places=None):
    """Localize number formatting"""
    try:
        return i18n_manager.format_number(value, decimal_places)
    except (ValueError, TypeError):
        return value


@register.filter
def localize_currency(value, currency='AZN'):
    """Localize currency formatting"""
    try:
        return i18n_manager.format_currency(value, currency)
    except (ValueError, TypeError):
        return value


@register.filter
def localize_date(value, format_type='DATE_FORMAT'):
    """Localize date formatting"""
    try:
        return i18n_manager.format_date(value, format_type)
    except (ValueError, TypeError):
        return value


@register.filter
def relative_time(value):
    """Format relative time"""
    try:
        return i18n_manager.format_relative_time(value)
    except (ValueError, TypeError):
        return value


@register.simple_tag
def get_language_info():
    """Get current language information"""
    return i18n_manager.get_language_info()


@register.simple_tag
def get_available_languages():
    """Get all available languages"""
    return settings.LANGUAGES


@register.simple_tag
def is_rtl():
    """Check if current language is RTL"""
    return i18n_manager.is_rtl_language()


@register.simple_tag
def language_direction():
    """Get text direction for current language"""
    return i18n_manager.get_language_direction()


@register.inclusion_tag('components/language_switcher.html', takes_context=True)
def language_switcher(context):
    """Render language switcher component"""
    request = context['request']
    current_lang = translation.get_language()
    
    languages = []
    for code, name in settings.LANGUAGES:
        languages.append({
            'code': code,
            'name': name,
            'is_current': code == current_lang,
            'url': request.build_absolute_uri().replace(f'/{current_lang}/', f'/{code}/')
        })
    
    return {
        'languages': languages,
        'current_language': current_lang,
        'request': request
    }


@register.simple_tag
def translate_choices(choices):
    """Translate model choices"""
    return i18n_manager.get_translated_choices(choices)


@register.simple_tag
def pluralize_text(count, singular, plural=None):
    """Handle pluralization"""
    return i18n_manager.pluralize(count, singular, plural)


@register.simple_tag(takes_context=True)
def localized_url(context, lang_code):
    """Generate URL for different language"""
    request = context['request']
    current_path = request.get_full_path()
    current_lang = translation.get_language()
    
    # Replace language code in URL
    if current_path.startswith(f'/{current_lang}/'):
        new_path = current_path.replace(f'/{current_lang}/', f'/{lang_code}/', 1)
    else:
        new_path = f'/{lang_code}{current_path}'
    
    return new_path


@register.inclusion_tag('components/rtl_support.html')
def rtl_support():
    """Include RTL support CSS and JS"""
    return {
        'is_rtl': i18n_manager.is_rtl_language(),
        'direction': i18n_manager.get_language_direction()
    }


@register.simple_tag
def get_translations_json():
    """Get translations as JSON for frontend"""
    current_lang = translation.get_language()
    return translation_manager.export_translations_json(current_lang)