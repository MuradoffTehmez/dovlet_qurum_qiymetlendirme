"""
Q360 Internationalization Utilities
Advanced i18n helpers for multilingual support
"""

from django.utils import translation
from django.utils.translation import gettext as _, ngettext, get_language
from django.utils.formats import date_format, number_format
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
import json
import os
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Union


class I18nManager:
    """Advanced internationalization manager"""
    
    def __init__(self):
        self.rtl_languages = getattr(settings, 'RTL_LANGUAGES', ['ar', 'he', 'fa', 'ur'])
        self.cache_timeout = 3600  # 1 hour
    
    def get_user_language(self, request) -> str:
        """Get user's preferred language"""
        # 1. Check URL parameter
        lang = request.GET.get('lang')
        if lang and self.is_valid_language(lang):
            return lang
        
        # 2. Check session
        if hasattr(request, 'session') and 'django_language' in request.session:
            lang = request.session['django_language']
            if self.is_valid_language(lang):
                return lang
        
        # 3. Check user profile
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'preferred_language'):
                lang = request.user.preferred_language
                if self.is_valid_language(lang):
                    return lang
        
        # 4. Check Accept-Language header
        if hasattr(request, 'META'):
            accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            for lang_code, _ in settings.LANGUAGES:
                if lang_code in accept_lang:
                    return lang_code
        
        # 5. Default language
        return settings.LANGUAGE_CODE
    
    def is_valid_language(self, lang_code: str) -> bool:
        """Check if language code is supported"""
        return lang_code in [code for code, name in settings.LANGUAGES]
    
    def is_rtl_language(self, lang_code: str = None) -> bool:
        """Check if language is RTL"""
        if not lang_code:
            lang_code = get_language()
        return lang_code in self.rtl_languages
    
    def get_language_direction(self, lang_code: str = None) -> str:
        """Get text direction for language"""
        return 'rtl' if self.is_rtl_language(lang_code) else 'ltr'
    
    def format_number(self, value: Union[int, float, Decimal], 
                     decimal_places: int = None, 
                     use_grouping: bool = True) -> str:
        """Format number according to current locale"""
        if decimal_places is not None:
            value = round(float(value), decimal_places)
        
        return number_format(
            value, 
            decimal_pos=decimal_places,
            use_l10n=True,
            force_grouping=use_grouping
        )
    
    def format_currency(self, amount: Union[int, float, Decimal], 
                       currency: str = 'AZN') -> str:
        """Format currency amount"""
        formatted_amount = self.format_number(amount, decimal_places=2)
        
        # Currency symbols mapping
        currency_symbols = {
            'AZN': '₼',
            'USD': '$',
            'EUR': '€',
            'TRY': '₺',
            'RUB': '₽'
        }
        
        symbol = currency_symbols.get(currency, currency)
        
        # RTL languages put currency after amount
        if self.is_rtl_language():
            return f"{formatted_amount} {symbol}"
        else:
            return f"{symbol} {formatted_amount}"
    
    def format_date(self, date_obj: Union[date, datetime], 
                   format_type: str = 'DATE_FORMAT') -> str:
        """Format date according to current locale"""
        if not date_obj:
            return ''
        
        return date_format(date_obj, format_type)
    
    def format_relative_time(self, date_obj: datetime) -> str:
        """Format relative time (e.g., '2 hours ago')"""
        from django.utils.timesince import timesince
        
        if not date_obj:
            return ''
        
        time_diff = timesince(date_obj)
        return _('%(time)s ago') % {'time': time_diff}
    
    def pluralize(self, count: int, singular: str, plural: str = None) -> str:
        """Handle pluralization for different languages"""
        if plural is None:
            # Auto-generate plural form for supported languages
            plural = self._auto_pluralize(singular)
        
        return ngettext(singular, plural, count)
    
    def _auto_pluralize(self, word: str) -> str:
        """Auto-generate plural forms (basic implementation)"""
        lang = get_language()
        
        if lang == 'en':
            if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
                return word + 'es'
            elif word.endswith('y') and word[-2] not in 'aeiou':
                return word[:-1] + 'ies'
            else:
                return word + 's'
        
        # For other languages, return the same word (will need proper rules)
        return word
    
    def get_translated_choices(self, choices: List[tuple]) -> List[tuple]:
        """Translate choice field options"""
        translated = []
        for value, label in choices:
            translated.append((value, _(label)))
        return translated
    
    def get_language_info(self, lang_code: str = None) -> Dict:
        """Get comprehensive language information"""
        if not lang_code:
            lang_code = get_language()
        
        cache_key = f'language_info_{lang_code}'
        info = cache.get(cache_key)
        
        if info is None:
            info = {
                'code': lang_code,
                'name': dict(settings.LANGUAGES).get(lang_code, lang_code),
                'direction': self.get_language_direction(lang_code),
                'is_rtl': self.is_rtl_language(lang_code),
                'date_format': self._get_locale_date_format(lang_code),
                'time_format': self._get_locale_time_format(lang_code),
                'decimal_separator': self._get_decimal_separator(lang_code),
                'thousand_separator': self._get_thousand_separator(lang_code),
            }
            cache.set(cache_key, info, self.cache_timeout)
        
        return info
    
    def _get_locale_date_format(self, lang_code: str) -> str:
        """Get date format for specific locale"""
        formats = {
            'az': 'd.m.Y',
            'en': 'm/d/Y',
            'tr': 'd.m.Y',
            'ru': 'd.m.Y'
        }
        return formats.get(lang_code, 'd.m.Y')
    
    def _get_locale_time_format(self, lang_code: str) -> str:
        """Get time format for specific locale"""
        formats = {
            'az': 'H:i',
            'en': 'g:i A',
            'tr': 'H:i',
            'ru': 'H:i'
        }
        return formats.get(lang_code, 'H:i')
    
    def _get_decimal_separator(self, lang_code: str) -> str:
        """Get decimal separator for locale"""
        separators = {
            'az': ',',
            'en': '.',
            'tr': ',',
            'ru': ','
        }
        return separators.get(lang_code, '.')
    
    def _get_thousand_separator(self, lang_code: str) -> str:
        """Get thousand separator for locale"""
        separators = {
            'az': ' ',
            'en': ',',
            'tr': '.',
            'ru': ' '
        }
        return separators.get(lang_code, ',')


class TranslationManager:
    """Manage translations and translation files"""
    
    def __init__(self):
        self.locale_path = settings.LOCALE_PATHS[0] if settings.LOCALE_PATHS else None
    
    def get_missing_translations(self, lang_code: str) -> List[str]:
        """Find missing translations for a language"""
        # This would scan .po files and find untranslated strings
        missing = []
        
        if not self.locale_path:
            return missing
        
        po_file = os.path.join(self.locale_path, lang_code, 'LC_MESSAGES', 'django.po')
        
        if os.path.exists(po_file):
            with open(po_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Simple check for empty msgstr
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('msgid ') and i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line.startswith('msgstr ""') or next_line.startswith('msgstr ""'):
                            # Extract the msgid
                            msgid = line[7:-1]  # Remove 'msgid "' and '"'
                            if msgid and msgid != '':
                                missing.append(msgid)
        
        return missing
    
    def export_translations_json(self, lang_code: str) -> Dict:
        """Export translations as JSON for frontend use"""
        cache_key = f'translations_json_{lang_code}'
        translations = cache.get(cache_key)
        
        if translations is None:
            translations = {}
            
            # Load from .po file and convert to JSON
            po_file = os.path.join(self.locale_path, lang_code, 'LC_MESSAGES', 'django.po')
            
            if os.path.exists(po_file):
                with open(po_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Parse .po file (simplified)
                    lines = content.split('\n')
                    current_msgid = None
                    
                    for line in lines:
                        if line.startswith('msgid '):
                            current_msgid = line[7:-1]  # Remove quotes
                        elif line.startswith('msgstr ') and current_msgid:
                            msgstr = line[8:-1]  # Remove quotes
                            if msgstr:
                                translations[current_msgid] = msgstr
                            current_msgid = None
            
            cache.set(cache_key, translations, 3600)
        
        return translations


# Global instances
i18n_manager = I18nManager()
translation_manager = TranslationManager()


# Template tags and filters
def localize_number(value, decimal_places=None):
    """Template filter for number localization"""
    return i18n_manager.format_number(value, decimal_places)


def localize_currency(value, currency='AZN'):
    """Template filter for currency localization"""
    return i18n_manager.format_currency(value, currency)


def localize_date(value, format_type='DATE_FORMAT'):
    """Template filter for date localization"""
    return i18n_manager.format_date(value, format_type)


def relative_time(value):
    """Template filter for relative time"""
    return i18n_manager.format_relative_time(value)