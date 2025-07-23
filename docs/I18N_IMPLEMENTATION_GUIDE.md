# Q360 Internationalization Implementation Guide

## Overview

This guide provides comprehensive instructions for implementing and managing internationalization (i18n) in the Q360 Performance Management System.

## 🌍 Supported Languages

- **Azerbaijani (az)** - Primary language
- **English (en)** - International support
- **Turkish (tr)** - Regional support
- **Russian (ru)** - Regional support

## 🛠 Implementation Strategy

### 1. Backend Implementation (Django)

#### Settings Configuration
```python
# config/settings.py
LANGUAGE_CODE = "az"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("az", _("Azərbaycan")),
    ("en", _("English")),
    ("tr", _("Türkçe")),
    ("ru", _("Русский")),
]

LOCALE_PATHS = [BASE_DIR / "locale"]
```

#### Middleware Setup
```python
MIDDLEWARE = [
    # ... other middleware
    "core.middleware.LanguageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # ... other middleware
    "core.middleware.LocaleMiddleware",
    "core.middleware.RTLMiddleware",
]
```

### 2. Frontend Implementation

#### JavaScript I18n Manager
```javascript
// Usage examples
window.i18n.translate('welcome_message', {name: 'John'});
window.i18n.formatNumber(1234.56, {decimals: 2});
window.i18n.formatCurrency(100, 'USD');
window.i18n.formatDate(new Date(), 'long');
```

#### Template Usage
```django
{% load i18n i18n_extras %}

<!-- Basic translation -->
{% trans "Hello World" %}

<!-- With context -->
{% blocktrans with name=user.name %}Hello {{ name }}{% endblocktrans %}

<!-- Number formatting -->
{{ price|localize_currency:"USD" }}

<!-- Date formatting -->
{{ date|localize_date:"long" }}

<!-- Language switcher -->
{% language_switcher %}

<!-- RTL support -->
{% rtl_support %}
```

## 📝 Translation Workflow

### 1. Extract Messages
```bash
# Extract all translatable strings
python manage.py makemessages --all --ignore=node_modules --ignore=venv

# Extract for specific language
python manage.py makemessages -l tr
```

### 2. Translate Messages
Edit the `.po` files in `locale/{language}/LC_MESSAGES/django.po`:

```po
#: templates/core/dashboard.html:15
msgid "Welcome to Q360"
msgstr "Q360-a xoş gəlmisiniz"
```

### 3. Compile Messages
```bash
# Compile all languages
python manage.py compilemessages

# Update and compile
python manage.py update_translations --compile
```

### 4. Build Frontend Assets
```bash
npm run build:i18n
```

## 🎨 RTL Language Support

### Automatic RTL Detection
The system automatically detects RTL languages and applies appropriate styles:

```css
html[dir="rtl"] {
    direction: rtl;
    text-align: right;
}

html[dir="rtl"] .navbar-nav {
    flex-direction: row-reverse;
}
```

### RTL-Specific Components
```django
{% if IS_RTL %}
    <div class="text-end">RTL Content</div>
{% else %}
    <div class="text-start">LTR Content</div>
{% endif %}
```

## 🔢 Number and Currency Formatting

### Backend Formatting
```python
from core.i18n_utils import i18n_manager

# Format numbers
formatted = i18n_manager.format_number(1234.56, decimal_places=2)

# Format currency
price = i18n_manager.format_currency(100, 'AZN')
```

### Frontend Formatting
```javascript
// Format numbers
const formatted = window.i18n.formatNumber(1234.56, {decimals: 2});

// Format currency
const price = window.i18n.formatCurrency(100, 'AZN');
```

### Template Filters
```django
{{ 1234.56|localize_number:2 }}
{{ 100|localize_currency:"AZN" }}
```

## 📅 Date and Time Formatting

### Locale-Specific Formats
```python
# Azerbaijani: 15.01.2025
# English: 01/15/2025
# Turkish: 15.01.2025
# Russian: 15.01.2025
```

### Usage Examples
```django
<!-- Short date -->
{{ date|localize_date:"short" }}

<!-- Long date -->
{{ date|localize_date:"long" }}

<!-- Relative time -->
{{ date|relative_time }}
```

## 🔧 Advanced Features

### 1. Pluralization
```python
# Backend
count = 5
message = i18n_manager.pluralize(count, "item", "items")

# Frontend
const message = window.i18n.pluralize(5, 'notification');
```

### 2. Context-Aware Translations
```django
{% blocktrans context "navigation" %}Home{% endblocktrans %}
{% blocktrans context "building" %}Home{% endblocktrans %}
```

### 3. Lazy Translations
```python
from django.utils.translation import gettext_lazy as _

# For model fields, form labels, etc.
class MyModel(models.Model):
    name = models.CharField(_("Name"), max_length=100)
```

## 🛠 Tools and Libraries

### Recommended Tools

1. **Poedit** - GUI editor for .po files
2. **Django Rosetta** - Web-based translation interface
3. **Weblate** - Collaborative translation platform
4. **Crowdin** - Professional translation management

### Installation
```bash
# For web-based editing
pip install django-rosetta

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'rosetta',
]

# Add to URLs
urlpatterns = [
    # ...
    path('rosetta/', include('rosetta.urls')),
]
```

## 📊 Translation Management

### Check Translation Status
```bash
python manage.py update_translations --check-missing
```

### Export Translations
```python
from core.i18n_utils import translation_manager

# Get missing translations
missing = translation_manager.get_missing_translations('tr')

# Export as JSON
translations = translation_manager.export_translations_json('az')
```

## 🎯 Best Practices

### 1. String Extraction
- Use meaningful context for translators
- Avoid concatenating translated strings
- Use placeholders for dynamic content

```python
# Good
_("Welcome, {name}!").format(name=user.name)

# Bad
_("Welcome, ") + user.name + "!"
```

### 2. Pluralization
- Always use proper pluralization functions
- Consider different plural rules for each language

```python
# Good
ngettext("%(count)d item", "%(count)d items", count) % {'count': count}

# Bad
f"{count} item{'s' if count != 1 else ''}"
```

### 3. Date and Number Formatting
- Always use locale-aware formatting
- Don't hardcode separators or formats

```python
# Good
from django.utils.formats import date_format
formatted_date = date_format(date, "SHORT_DATE_FORMAT")

# Bad
formatted_date = date.strftime("%d.%m.%Y")
```

### 4. RTL Support
- Test all layouts in RTL mode
- Use logical properties instead of physical ones
- Consider text expansion/contraction

## 🧪 Testing

### Test Different Languages
```python
from django.test import TestCase
from django.utils import translation

class I18nTestCase(TestCase):
    def test_translation(self):
        with translation.override('tr'):
            response = self.client.get('/')
            self.assertContains(response, 'Merhaba')
```

### Test RTL Layout
```javascript
// Test RTL layout
document.documentElement.dir = 'rtl';
// Run your tests
```

## 🚀 Deployment Considerations

### 1. Static Files
```bash
# Collect static files including translations
python manage.py collectstatic

# Compile messages for production
python manage.py compilemessages
```

### 2. CDN Configuration
- Ensure translation files are properly cached
- Set appropriate cache headers for .mo files

### 3. Performance
- Use translation caching
- Preload critical translations
- Lazy load non-critical translations

## 📈 Monitoring and Analytics

### Track Language Usage
```python
# Add to your analytics
def track_language_usage(request):
    language = request.LANGUAGE_CODE
    # Send to analytics service
```

### Monitor Translation Quality
- Set up alerts for missing translations
- Track user language switching patterns
- Monitor page load times for different locales

## 🔄 Maintenance

### Regular Tasks
1. **Weekly**: Check for new translatable strings
2. **Monthly**: Review translation quality
3. **Quarterly**: Update language packs
4. **Annually**: Review supported languages

### Automation
```bash
# Set up cron job for translation updates
0 2 * * 1 cd /path/to/project && python manage.py update_translations --compile
```

This comprehensive i18n implementation provides a solid foundation for multilingual support in your Q360 application, ensuring accessibility and usability for users across different languages and cultures.