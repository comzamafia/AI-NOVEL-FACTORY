"""
Test settings for AI Novel Factory — no external services required.
"""
from config.settings import *  # noqa: F401, F403

# ─────────────────────────────────────────────
# Database — fast in-memory SQLite for tests
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ─────────────────────────────────────────────
# Celery — synchronous in-process execution
# ─────────────────────────────────────────────
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ─────────────────────────────────────────────
# Cache — in-memory (no Redis)
# ─────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ─────────────────────────────────────────────
# Passwords — fastest hasher for tests
# ─────────────────────────────────────────────
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ─────────────────────────────────────────────
# Email — suppress in tests
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ─────────────────────────────────────────────
# Security — disable HTTPS warnings in tests
# ─────────────────────────────────────────────
DEBUG = True
SECRET_KEY = 'test-secret-key-not-for-production'

# ─────────────────────────────────────────────
# Logging — quiet in tests
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {'class': 'logging.NullHandler'},
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}
