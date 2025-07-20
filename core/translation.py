# core/translation.py - Model Translation konfiqurasiyası

from modeltranslation.translator import register, TranslationOptions
from .models import (
    OrganizationUnit, SualKateqoriyasi, Sual, QiymetlendirmeDovru,
    QuickFeedbackCategory, IdeaCategory
)


@register(OrganizationUnit)
class OrganizationUnitTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(SualKateqoriyasi) 
class SualKateqoriyasiTranslationOptions(TranslationOptions):
    fields = ('ad',)


@register(Sual)
class SualTranslationOptions(TranslationOptions):
    fields = ('metn',)


@register(QiymetlendirmeDovru)
class QiymetlendirmeDovruTranslationOptions(TranslationOptions):
    fields = ('ad',)


@register(QuickFeedbackCategory)
class QuickFeedbackCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(IdeaCategory)
class IdeaCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')