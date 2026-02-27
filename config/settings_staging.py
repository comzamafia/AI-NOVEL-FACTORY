"""
Staging environment settings.
Inherits everything from base settings, overrides for staging behaviour.

Usage:
    export DJANGO_SETTINGS_MODULE=config.settings_staging
    python manage.py <command>

Or in docker-compose.staging.yml:
    environment:
      DJANGO_SETTINGS_MODULE: config.settings_staging
"""

from .settings import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core overrides
# ---------------------------------------------------------------------------

DEBUG = False

ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "staging.ai-novel-factory.com,localhost,127.0.0.1",
).split(",")

# ---------------------------------------------------------------------------
# Security (staging — slightly relaxed vs prod, but hardened vs dev)
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"
SECURE_HSTS_SECONDS = 3600            # shorter than prod for testing
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# DATABASE_URL env var is the single source of truth in staging

# ---------------------------------------------------------------------------
# Throttling: more permissive on staging so QA testers aren't blocked
# ---------------------------------------------------------------------------

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(  # noqa: F405
    {
        "anon": "500/hour",
        "user": "5000/hour",
        "ai_generation": "100/hour",
        "chapter_write": "200/hour",
    }
)

# ---------------------------------------------------------------------------
# Email — log in console (no real sends on staging)
# ---------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# Logging — more verbose
# ---------------------------------------------------------------------------

LOGGING["handlers"]["console"]["level"] = "DEBUG"  # noqa: F405
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405

# ---------------------------------------------------------------------------
# CORS — allow staging frontend domain
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "https://staging.ai-novel-factory.com,http://localhost:3000",
).split(",")

# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------

import sentry_sdk  # noqa: E402

_sentry_dsn = os.getenv("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment="staging",
        traces_sample_rate=1.0,  # 100% on staging — capture all perf issues
        send_default_pii=False,
    )

# ---------------------------------------------------------------------------
# AI — allow full LLM calls on staging
# ---------------------------------------------------------------------------

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# ---------------------------------------------------------------------------
# Static / Media
# ---------------------------------------------------------------------------

STATIC_ROOT = os.getenv("STATIC_ROOT", "/app/staticfiles")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/app/media")
