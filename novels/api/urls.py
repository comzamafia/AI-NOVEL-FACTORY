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
)

# Create router
router = DefaultRouter()
router.register(r'pen-names', PenNameViewSet, basename='pen-name')
router.register(r'books', BookViewSet, basename='book')
router.register(r'book-descriptions', BookDescriptionViewSet, basename='book-description')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'story-bibles', StoryBibleViewSet, basename='story-bible')

app_name = 'novels'

urlpatterns = [
    path('', include(router.urls)),
]
