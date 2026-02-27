"""
Celery configuration for AI Novel Factory project.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')


# =============================================================================
# CELERY BEAT SCHEDULE
# =============================================================================
# Scheduled tasks configuration
# The schedule is managed through django-celery-beat in the database,
# but we can define some defaults here.

app.conf.beat_schedule = {
    # Daily content generation - runs at 06:00 AM
    'daily-content-generation': {
        'task': 'novels.tasks.content.run_daily_content_generation',
        'schedule': {
            'hour': 6,
            'minute': 0,
        },
    },
    # Daily keyword research sync
    'daily-keyword-sync': {
        'task': 'novels.tasks.keywords.sync_keyword_data',
        'schedule': {
            'hour': 4,
            'minute': 0,
        },
    },
    # Daily ads performance sync
    'daily-ads-sync': {
        'task': 'novels.tasks.ads.sync_ads_performance',
        'schedule': {
            'hour': 3,
            'minute': 0,
        },
    },
    # Daily review tracking
    'daily-review-tracking': {
        'task': 'novels.tasks.reviews.scrape_amazon_reviews',
        'schedule': {
            'hour': 2,
            'minute': 0,
        },
    },
    # Daily pricing transitions
    'daily-pricing-check': {
        'task': 'novels.tasks.pricing.auto_transition_pricing',
        'schedule': {
            'hour': 1,
            'minute': 0,
        },
    },
    # Weekly competitor data update
    'weekly-competitor-update': {
        'task': 'novels.tasks.competitors.update_competitor_data',
        'schedule': {
            'day_of_week': 0,  # Monday
            'hour': 5,
            'minute': 0,
        },
    },
    # Weekly ads optimization
    'weekly-ads-optimization': {
        'task': 'novels.tasks.ads.optimize_ads_keywords',
        'schedule': {
            'day_of_week': 0,  # Monday
            'hour': 8,
            'minute': 0,
        },
    },
    # Weekly platform revenue sync
    'weekly-platform-revenue': {
        'task': 'novels.tasks.distribution.sync_platform_revenue',
        'schedule': {
            'day_of_week': 1,  # Tuesday
            'hour': 6,
            'minute': 0,
        },
    },
    # Monthly content theft check
    'monthly-content-theft-check': {
        'task': 'novels.tasks.legal.check_content_theft',
        'schedule': {
            'day_of_month': 1,
            'hour': 7,
            'minute': 0,
        },
    },
}

# Task route configuration
app.conf.task_routes = {
    'novels.tasks.content.*': {'queue': 'content'},
    'novels.tasks.ai.*': {'queue': 'ai'},
    'novels.tasks.scraping.*': {'queue': 'scraping'},
    'novels.tasks.export.*': {'queue': 'export'},
    'novels.tasks.email.*': {'queue': 'email'},
    'novels.tasks.*': {'queue': 'default'},
}

# Task retry policy
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_max_retries = 3
