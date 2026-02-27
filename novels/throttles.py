"""
Custom DRF throttle classes for AI Novel Factory.

Scope matrix
───────────────────────────────────────────────────────────
Scope               Limit        Usage
───────────────────────────────────────────────────────────
anon                100/hour     Public read endpoints (default)
user                1000/hour    Authenticated reads (default)
ai_generation       20/hour      per-user: book concept / description / bible
chapter_write       50/hour      per-user: chapter write / rewrite triggers
payment             30/hour      per-user: Stripe checkout / subscription
webhook             exempt*      Stripe inbound webhooks (whitelisted by DRF)
burst               60/minute    per-user: burst protection on any action
───────────────────────────────────────────────────────────

Register in settings.REST_FRAMEWORK:
    DEFAULT_THROTTLE_CLASSES  — anon + user
    Per-view: throttle_classes = [AIGenerationThrottle]
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


# ---------------------------------------------------------------------------
# Public / anonymous
# ---------------------------------------------------------------------------

class PublicReadThrottle(AnonRateThrottle):
    """Generous rate for storefront read traffic."""
    scope = "public_read"


# ---------------------------------------------------------------------------
# Authenticated users — default
# ---------------------------------------------------------------------------

class BurstThrottle(UserRateThrottle):
    """Short-window burst cap — applied to any action endpoint."""
    scope = "burst"


# ---------------------------------------------------------------------------
# AI generation endpoints
# (book concept, description, story bible, chapter briefs)
# ---------------------------------------------------------------------------

class AIGenerationThrottle(UserRateThrottle):
    """
    Limits: 20 AI generation requests per user per hour.
    Apply on:  start_description_generation, start_bible_generation,
               generate_chapter_briefs, generate_book_concepts actions.
    """
    scope = "ai_generation"


# ---------------------------------------------------------------------------
# Chapter write / rewrite triggers
# ---------------------------------------------------------------------------

class ChapterWriteThrottle(UserRateThrottle):
    """50 chapter write/rewrite triggers per user per hour."""
    scope = "chapter_write"


# ---------------------------------------------------------------------------
# Payment  / subscriptions
# ---------------------------------------------------------------------------

class PaymentThrottle(UserRateThrottle):
    """30 payment-related requests per user per hour."""
    scope = "payment"


# ---------------------------------------------------------------------------
# Stripe webhooks — no throttling (verified by Stripe signature)
# ---------------------------------------------------------------------------

class WebhookThrottle(AnonRateThrottle):
    """
    Effectively unlimited — Stripe delivers from a known IP range.
    Set very high so it never blocks; signature validation is the real gate.
    """
    scope = "webhook"
