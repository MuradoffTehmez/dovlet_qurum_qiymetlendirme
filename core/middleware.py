"""
Q360 Custom Middleware
"""

from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import is_valid_path
from django.conf import settings
from django.http import HttpResponseRedirect
from core.i18n_utils import i18n_manager


class LanguageMiddleware(MiddlewareMixin):
    """
    Enhanced language detection and handling middleware
    """
    
    def process_request(self, request):
        # Get user's preferred language
        user_language = i18n_manager.get_user_language(request)
        
        # Activate the language
        translation.activate(user_language)
        request.LANGUAGE_CODE = user_language
        
        # Set RTL flag
        request.IS_RTL = i18n_manager.is_rtl_language(user_language)
        request.TEXT_DIRECTION = i18n_manager.get_language_direction(user_language)
        
        # Store in session
        if hasattr(request, 'session'):
            request.session['django_language'] = user_language
    
    def process_response(self, request, response):
        # Ensure language is deactivated
        translation.deactivate()
        return response


class LocaleMiddleware(MiddlewareMixin):
    """
    Set locale-specific formatting
    """
    
    def process_request(self, request):
        # Set locale information in request
        lang_code = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
        request.LOCALE_INFO = i18n_manager.get_language_info(lang_code)


class RTLMiddleware(MiddlewareMixin):
    """
    Handle RTL layout adjustments
    """
    
    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            # Add RTL context to all templates
            if response.context_data is None:
                response.context_data = {}
            
            response.context_data.update({
                'IS_RTL': getattr(request, 'IS_RTL', False),
                'TEXT_DIRECTION': getattr(request, 'TEXT_DIRECTION', 'ltr'),
                'LANGUAGE_INFO': getattr(request, 'LOCALE_INFO', {}),
            })
        
        return response