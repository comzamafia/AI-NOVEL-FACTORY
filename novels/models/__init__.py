"""
AI Novel Factory Models Package.

All models are organized into separate modules for better maintainability.
"""

# Base models
from .base import TimeStampedModel, SoftDeleteModel, BaseModel

# Core models
from .pen_name import PenName
from .book import Book, BookLifecycleStatus
from .story import StoryBible, Chapter, ChapterStatus

# SEO & Keywords
from .keywords import KeywordResearch, BookDescription, BookDescriptionVersion

# Marketing & Sales
from .marketing import (
    PricingStrategy,
    PricingPhase,
    PromotionType,
    AdsPerformance,
    ReviewTracker,
    ARCReader,
)

# Distribution & Intelligence
from .distribution import (
    DistributionChannel,
    DistributionPlatform,
    CompetitorBook,
    StyleFingerprint,
)

# Payments & Subscriptions
from .subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    ChapterPurchase,
    WebhookEvent,
)

# KDP Covers
from .cover import BookCover, CoverType, PaperType, TrimSize

__all__ = [
    # Base
    'TimeStampedModel',
    'SoftDeleteModel',
    'BaseModel',
    # Core
    'PenName',
    'Book',
    'BookLifecycleStatus',
    'StoryBible',
    'Chapter',
    'ChapterStatus',
    # Keywords
    'KeywordResearch',
    'BookDescription',
    'BookDescriptionVersion',
    # Marketing
    'PricingStrategy',
    'PricingPhase',
    'PromotionType',
    'AdsPerformance',
    'ReviewTracker',
    'ARCReader',
    # Distribution
    'DistributionChannel',
    'DistributionPlatform',
    'CompetitorBook',
    'StyleFingerprint',
    # Subscription
    'Subscription',
    'SubscriptionPlan',
    'SubscriptionStatus',
    'ChapterPurchase',
    'WebhookEvent',
    # KDP Covers
    'BookCover',
    'CoverType',
    'PaperType',
    'TrimSize',
]
