"""
API URLs for AI Novel Factory.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PenNameViewSet,
    BookViewSet,
    BookDescriptionViewSet,
    ChapterViewSet,
    StoryBibleViewSet,
    BookCoverViewSet,
    KeywordResearchViewSet,
    ReviewTrackerViewSet,
    AdsPerformanceViewSet,
    PricingStrategyViewSet,
    DistributionChannelViewSet,
    CompetitorBookViewSet,
    ARCReaderViewSet,
    StyleFingerprintViewSet,
    BookDescriptionFullViewSet,
)

# Create router
router = DefaultRouter()
router.register(r'pen-names', PenNameViewSet, basename='pen-name')
router.register(r'books', BookViewSet, basename='book')
router.register(r'book-descriptions', BookDescriptionViewSet, basename='book-description')
router.register(r'book-descriptions-full', BookDescriptionFullViewSet, basename='book-description-full')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'story-bibles', StoryBibleViewSet, basename='story-bible')
router.register(r'covers', BookCoverViewSet, basename='cover')
router.register(r'keyword-research', KeywordResearchViewSet, basename='keyword-research')
router.register(r'review-trackers', ReviewTrackerViewSet, basename='review-tracker')
router.register(r'ads-performance', AdsPerformanceViewSet, basename='ads-performance')
router.register(r'pricing-strategies', PricingStrategyViewSet, basename='pricing-strategy')
router.register(r'distribution-channels', DistributionChannelViewSet, basename='distribution-channel')
router.register(r'competitor-books', CompetitorBookViewSet, basename='competitor-book')
router.register(r'arc-readers', ARCReaderViewSet, basename='arc-reader')
router.register(r'style-fingerprints', StyleFingerprintViewSet, basename='style-fingerprint')

app_name = 'novels'

urlpatterns = [
    path('', include(router.urls)),
]
