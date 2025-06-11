# core/context_processors.py

from django.utils.translation import get_language, get_language_info

def language_switcher_context(request):
    """
    Bütün şablonlara dil dəyişdirmə menyusu üçün
    hazır məlumat ötürən kontekst prosessoru.
    """
    # Mövcud aktiv dilin kodunu alır (məs: 'az')
    current_lang_code = get_language()
    
    # settings.py-də təyin etdiyimiz dillər
    # (Bu hissəni gələcəkdə birbaşa settings-dən də oxuya bilərik)
    languages = [
        {'code': 'az', 'name': 'Azərbaycan'},
        {'code': 'en', 'name': 'English'},
    ]
    
    # Hər bir dil üçün, onun aktiv olub-olmadığını yoxlayırıq
    processed_languages = []
    for lang in languages:
        processed_languages.append({
            'code': lang['code'],
            'name': lang['name'],
            'is_current': lang['code'] == current_lang_code
        })

    # Şablona göndəriləcək məlumat
    return {
        'language_switcher_data': processed_languages
    }