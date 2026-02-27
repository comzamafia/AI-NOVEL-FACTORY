"""
AI Novel Factory Configuration Package.

This module ensures that the Celery app is always imported when
Django starts so that shared_task will use this app.
"""

# Import celery app for Django to use
from .celery import app as celery_app

__all__ = ('celery_app',)
