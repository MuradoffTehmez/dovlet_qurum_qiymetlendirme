from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _
import datetime

# ===================================================================
# ƏSAS QURĞULAR VƏ YOLLAR (BASE CONFIGURATIONS & PATHS)
# ===================================================================

load_dotenv()  # .env faylından dəyişənləri yükləmək üçün

BASE_DIR = Path(__file__).resolve().parent.parent  # Layihənin əsas direktoriyası

# ===================================================================
# TƏHLÜKƏSİZLİK (SECURITY SETTINGS)
# ===================================================================

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

AUTHENTICATION_BACKENDS = [
    'core.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ===================================================================
# TƏTBİQLƏR (INSTALLED APPLICATIONS)
# ===================================================================

INSTALLED_APPS = [
    # Üçüncü tərəf paketləri
    'jazzmin',
    'crispy_forms',
    'crispy_bootstrap5',
    'simple_history',

    # Django daxilində olanlar
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Öz tətbiqlər
    'core.apps.CoreConfig',
]

# ===================================================================
# MİDDLEWARE (ORTA QAT FUNKSİYALARI)
# ===================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

# ===================================================================
# URL, WSGI
# ===================================================================

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ===================================================================
# VERİLƏNLƏR BAZASI (DATABASE)
# ===================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ===================================================================
# ŞİFRƏ TƏHLÜKƏSİZLİYİ (PASSWORD VALIDATORS)
# ===================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===================================================================
# DİL VƏ SAAT ZONU (INTERNATIONALIZATION)
# ===================================================================

LANGUAGE_CODE = 'az'
TIME_ZONE = 'Asia/Baku'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('az', _('Azərbaycan')),
    ('en', _('English')),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ===================================================================
# STATİK FAYLLAR (STATIC FILES)
# ===================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# ===================================================================
# AUTHENTICATION VƏ USER MODEL
# ===================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.Ishchi'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ===================================================================
# E-MAIL TƏNZİMLƏMƏLƏRİ (EMAIL CONFIGURATION)
# ===================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ===================================================================
# CRISPY FORMS TƏNZİMLƏRİ
# ===================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ===================================================================
# JAZZMIN – ADMIN PANELİ DİZAYNI
# ===================================================================

JAZZMIN_SETTINGS = {
    "site_title": "360° Qiymətləndirmə Paneli",
    "site_header": "İşçi Dəyərləndirmə Sistemi",
    "site_brand": "360° Dəyərləndirmə",
    "welcome_sign": "360° Qiymətləndirmə Sisteminizə Xoş Gəlmisiniz",
    "site_header_short": "Dəyərləndirmə",
    "site_url": "/",
    "show_sidebar": True,
    "navigation_expanded": True,
    "topmenu_links": [
        {"name": "Ana Səhifə", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
        {"app": "your_app_label"},
    ],
    "custom_links": {
        "auth": [
            {
                "name": "İstifadəçi əlavə et",
                "url": "add_user",
                "icon": "fas fa-user-plus",
                "permissions": ["auth.add_user"]
            }
        ]
    },
    "copyright": "© 2025 Muradov İT MMC",
    "show_ui_builder": True,
    "order_with_respect_to": ["Qiymetlendirme", "Ishci", "Rehber"],
    "user_avatar": None,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-lime",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "slate",
    "dark_mode_theme": "slate",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-outline-success"
    },
    "actions_sticky_top": False
}

# ===================================================================
# TEMPLATES (ŞABLONLARIN KONFİQURASİYASI)
# ===================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.language_switcher_context',
            ],
        },
    },
]

# ===================================================================
# CACHE (MÜVƏQQƏTİ YADDAŞ)
# ===================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ===================================================================
# LOGGING (GÜNLÜK GÖZƏTİM SİSTEMİ)
# ===================================================================

# Hər server başlananda ayrıca log faylı yaratmaq üçün tarixi fayl adı kimi istifadə edirik.
LOG_FILE_NAME = BASE_DIR / f'logs/django_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname}: {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_NAME,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
}

# ===================================================================
# CELERY KONFİQURASİYASI
# ===================================================================

CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'send_reminder_emails': {
        'task': 'core.tasks.send_reminder_emails',
        'schedule': datetime.timedelta(hours=1),  # Hər saat
    },
}