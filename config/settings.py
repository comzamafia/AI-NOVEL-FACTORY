"""
Django settings for AI Novel Factory project.

Full configuration with:
- Django REST Framework
- Celery + Redis
- PostgreSQL
- django-fsm State Machine
- Sentry Error Tracking
- CORS Headers
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'django_fsm',
    'django_celery_beat',
]

LOCAL_APPS = [
    'novels.apps.NovelsConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =============================================================================
# URL CONFIGURATION
# =============================================================================

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# =============================================================================
# DATABASE - PostgreSQL (with SQLite fallback for development)
# =============================================================================

DATABASE_ENGINE = os.getenv('DB_ENGINE', 'sqlite')  # 'postgresql' or 'sqlite'

if DATABASE_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'ai_novel_factory'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
else:
    # SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Built-in scopes
        'anon': '200/hour',
        'user': '2000/hour',
        # Custom scopes (novels/throttles.py)
        'public_read': '500/hour',
        'burst': '60/minute',
        'ai_generation': '20/hour',
        'chapter_write': '50/hour',
        'payment': '30/hour',
        'webhook': '10000/hour',  # effectively unlimited — Stripe sig is the gate
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}


# =============================================================================
# CORS HEADERS
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
]

CORS_ALLOW_CREDENTIALS = True


# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Static fallback schedule — seeded into DB on first run if not already present
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    # ── Maintenance ─────────────────────────────────────────────────────────
    'daily-db-backup': {
        'task': 'novels.tasks.maintenance.backup_database',
        'schedule': crontab(hour=2, minute=0),   # 02:00 UTC every day
        'options': {'queue': 'default'},
    },
    'weekly-cleanup-old-backups': {
        'task': 'novels.tasks.maintenance.cleanup_old_backups',
        'schedule': crontab(hour=3, minute=0, day_of_week='monday'),
        'options': {'queue': 'default'},
    },
    # ── Content pipeline ─────────────────────────────────────────────────────
    'daily-content-generation': {
        'task': 'novels.tasks.content.run_daily_content_generation',
        'schedule': crontab(hour=6, minute=0),
        'options': {'queue': 'ai_generation'},
    },
    # ── Pricing ──────────────────────────────────────────────────────────────
    'daily-pricing-transitions': {
        'task': 'novels.tasks.pricing.auto_transition_pricing',
        'schedule': crontab(hour=7, minute=0),
        'options': {'queue': 'default'},
    },
    # ── Ads ───────────────────────────────────────────────────────────────────
    'daily-ads-sync': {
        'task': 'novels.tasks.ads.sync_ads_performance',
        'schedule': crontab(hour=8, minute=0),
        'options': {'queue': 'default'},
    },
    'weekly-ads-optimization': {
        'task': 'novels.tasks.ads.optimize_ads_keywords',
        'schedule': crontab(hour=8, minute=0, day_of_week='monday'),
        'options': {'queue': 'default'},
    },
    # ── Reviews ───────────────────────────────────────────────────────────────
    'daily-review-scrape': {
        'task': 'novels.tasks.reviews.scrape_all_books_reviews',
        'schedule': crontab(hour=9, minute=0),
        'options': {'queue': 'default'},
    },
}


# =============================================================================
# REDIS CONFIGURATION
# =============================================================================

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Use Redis if available, otherwise fall back to local memory cache (safe for dev)
def _build_cache_config():
    if os.getenv('USE_REDIS', 'auto').lower() == 'false':
        return {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    if os.getenv('USE_REDIS', 'auto').lower() == 'true':
        return {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': REDIS_URL}}
    # auto: probe Redis — if not reachable, fall back silently
    try:
        import redis as _redis
        _redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1).ping()
        return {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': REDIS_URL}}
    except Exception:
        return {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

CACHES = _build_cache_config()


# =============================================================================
# AI API KEYS
# =============================================================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# LLM Provider selection ('ollama' for local dev, 'gemini' for production)
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')

# Ollama (local)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '300'))

# Gemini (cloud)
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')


# =============================================================================
# STRIPE PAYMENT
# =============================================================================

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')


# =============================================================================
# AMAZON ADVERTISING API
# =============================================================================

AMAZON_ADVERTISING_CLIENT_ID = os.getenv('AMAZON_ADVERTISING_CLIENT_ID', '')
AMAZON_ADVERTISING_CLIENT_SECRET = os.getenv('AMAZON_ADVERTISING_CLIENT_SECRET', '')
AMAZON_ADVERTISING_REFRESH_TOKEN = os.getenv('AMAZON_ADVERTISING_REFRESH_TOKEN', '')


# =============================================================================
# SEO / SCRAPING APIS
# =============================================================================

DATAFORSEO_LOGIN = os.getenv('DATAFORSEO_LOGIN', '')
DATAFORSEO_PASSWORD = os.getenv('DATAFORSEO_PASSWORD', '')
SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY', '')


# =============================================================================
# QUALITY CHECK APIS
# =============================================================================

ORIGINALITY_AI_API_KEY = os.getenv('ORIGINALITY_AI_API_KEY', '')
COPYSCAPE_API_KEY = os.getenv('COPYSCAPE_API_KEY', '')
COPYSCAPE_USERNAME = os.getenv('COPYSCAPE_USERNAME', '')


# =============================================================================
# SENTRY ERROR TRACKING
# =============================================================================

SENTRY_DSN = os.getenv('SENTRY_DSN', '')

if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment='production' if not DEBUG else 'development',
    )


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)


# =============================================================================
# FRONTEND URL (for CORS and links)
# =============================================================================

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'celery.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'novels': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)
