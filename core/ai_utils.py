# core/ai_utils.py

import google.generativeai as genai
from django.conf import settings

# API açarını konfiqurasiya edirik
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Gemini AI konfiqurasiya edilərkən xəta baş verdi: {e}")
    model = None


def generate_recommendations(feedback_list):
    """Verilən rəylər siyahısı əsasında Gemini AI ilə inkişaf tövsiyələri yaradır."""
    
    if not model or not feedback_list:
        return None

    # Rəyləri vahid bir mətnə birləşdiririk
    formatted_feedback = "\n- ".join(filter(None, feedback_list))
    
    # Süni intellektə göndərəcəyimiz təlimat (prompt)
    prompt = f"""
    Bir işçinin 360 dərəcə performans qiymətləndirməsi zamanı onun haqqında aşağıdakı yazılı rəylər toplanıb.
    Bu rəyləri diqqətlə analiz et. İşçinin özünü inkişaf etdirməsi üçün 3-4 bənddən ibarət, konkret, peşəkar və pozitiv dildə yazılmış tövsiyə hazırla.
    Tövsiyələri nömrələnmiş siyahı (1., 2., 3.) şəklində, Azərbaycan dilində qaytar. Cavabında heç bir əlavə başlıq və ya mətn olmasın, yalnız siyahını qaytar.

    Rəylər:
    - {formatted_feedback}

    İnkişaf Tövsiyələri:
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API-dan cavab alınarkən xəta baş verdi: {e}")
        return "Tövsiyələr yaradıla bilmədi. Zəhmət olmasa, daha sonra yenidən cəhd edin."