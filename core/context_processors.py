# core/context_processors.py

from django.utils.translation import get_language


def language_switcher_context(request):
    """
    Bütün şablonlara dil dəyişdirmə menyusu üçün
    hazır məlumat ötürən kontekst prosessoru.
    """
    current_lang_code = get_language()
    
    languages = [
        {'code': 'az', 'name': 'Azərbaycan'},
        {'code': 'en', 'name': 'English'},
    ]
    
    processed_languages = []
    for lang in languages:
        processed_languages.append({
            'code': lang['code'],
            'name': lang['name'],
            'is_current': lang['code'] == current_lang_code
        })

    return {
        'language_switcher_data': processed_languages
    }