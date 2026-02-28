"""
Production environment settings.
Inherits from base settings, hardened for live traffic.

Usage:
    export DJANGO_SETTINGS_MODULE=config.settings_production
    python manage.py <command>

Required environment variables (no defaults — will raise if missing):
    DJANGO_SECRET_KEY
    DATABASE_URL
    CELERY_BROKER_URL
    CELERY_RESULT_BACKEND
    DJANGO_ALLOWED_HOSTS
    CORS_ALLOWED_ORIGINS
"""

import os
from .settings import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Validate required secrets are set
# ---------------------------------------------------------------------------

_REQUIRED = [
    "DJANGO_SECRET_KEY",
    "DATABASE_URL",
    "CELERY_BROKER_URL",
]
_missing = [v for v in _REQUIRED if not os.getenv(v)]
if _missing:
    raise EnvironmentError(
        f"Production requires these env vars to be set: {', '.join(_missing)}"
    )

# ---------------------------------------------------------------------------
# Database — parse DATABASE_URL (injected by Railway PostgreSQL plugin)
# ---------------------------------------------------------------------------

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31_536_000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# ---------------------------------------------------------------------------
# Password validation — enforce strong passwords in production
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Rate limiting — tighter in production
# ---------------------------------------------------------------------------

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(  # noqa: F405
    {
        "anon": "100/hour",
        "user": "1000/hour",
        "ai_generation": "20/hour",
        "chapter_write": "50/hour",
        "payment": "30/hour",
    }
)

# ---------------------------------------------------------------------------
# CORS — production domains only
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", ""
).split(",")

CORS_ALLOW_ALL_ORIGINS = False

# ---------------------------------------------------------------------------
# Email — SMTP (e.g. SES, SendGrid)
# ---------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.sendgrid.net")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "apikey")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@ai-novel-factory.com")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", "devops@ai-novel-factory.com")

# ---------------------------------------------------------------------------
# Logging — structured JSON to stdout (captured by log aggregator)
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "django.utils.log.ServerFormatter",
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.security": {"level": "WARNING", "propagate": True},
        "celery": {"level": "INFO", "propagate": True},
        "novels": {"level": "INFO", "propagate": True},
    },
}

# ---------------------------------------------------------------------------
# Sentry — production DSN with performance tracing
# ---------------------------------------------------------------------------

import sentry_sdk  # noqa: E402
from sentry_sdk.integrations.django import DjangoIntegration  # noqa: E402
from sentry_sdk.integrations.celery import CeleryIntegration  # noqa: E402
from sentry_sdk.integrations.redis import RedisIntegration  # noqa: E402

_sentry_dsn = os.getenv("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment="production",
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.05")),
        send_default_pii=False,
        release=os.getenv("GIT_SHA", "unknown"),
    )

# ---------------------------------------------------------------------------
# Static / Media — Whitenoise serves static files directly
# ---------------------------------------------------------------------------

STATIC_ROOT = os.getenv("STATIC_ROOT", "/app/staticfiles")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/app/media")

# Whitenoise: compressed, cached static files with forever headers
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Ensure whitenoise middleware is present (insert after SecurityMiddleware)
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:  # noqa: F405
    _sec_idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")  # noqa: F405
    MIDDLEWARE.insert(_sec_idx + 1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

# ---------------------------------------------------------------------------
# Celery — production task limits
# ---------------------------------------------------------------------------

CELERY_TASK_TIME_LIMIT = 60 * 60      # 1 hour absolute max
CELERY_TASK_SOFT_TIME_LIMIT = 50 * 60  # 50-minute soft limit (raises exception)
CELERY_WORKER_MAX_TASKS_PER_CHILD = 500  # recycle workers to prevent memory leaks
