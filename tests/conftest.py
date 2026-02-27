"""
Shared pytest fixtures for AI Novel Factory test suite.
"""

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from novels.models import PenName, Book, Chapter, StoryBible, BookDescription

User = get_user_model()


# ─────────────────────────────────────────────
# Auth fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com',
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


# ─────────────────────────────────────────────
# Domain fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def pen_name(db):
    return PenName.objects.create(
        name='Test Author',
        niche_genre='Thriller',
        bio='A test author for unit tests.',
        writing_style_prompt='Write in a tense, fast-paced style.',
    )


@pytest.fixture
def book(db, pen_name):
    return Book.objects.create(
        title='Test Book One',
        subtitle='A Testing Subtitle',
        synopsis='A book created for automated testing purposes.',
        pen_name=pen_name,
        target_chapter_count=20,
        target_word_count=50000,
    )


@pytest.fixture
def published_book(db, pen_name):
    return Book.objects.create(
        title='Published Book',
        synopsis='A published book for storefront tests.',
        pen_name=pen_name,
        lifecycle_status='published_kdp',
        asin='B0TEST12345',
        cover_image_url='https://example.com/cover.jpg',
        amazon_url='https://amazon.com/dp/B0TEST12345',
        current_price_usd='4.99',
        target_chapter_count=15,
        target_word_count=40000,
    )


@pytest.fixture
def chapter(db, book):
    return Chapter.objects.create(
        book=book,
        chapter_number=1,
        title='Chapter One',
    )


@pytest.fixture
def published_chapter(db, book):
    return Chapter.objects.create(
        book=book,
        chapter_number=2,
        title='Chapter Two',
        is_published=True,
        is_free=True,
    )


@pytest.fixture
def story_bible(db, book):
    return StoryBible.objects.create(
        book=book,
        characters={
            'protagonist': {
                'name': 'Hero Protagonist',
                'age': 35,
                'occupation': 'Detective',
                'personality': 'Tenacious',
                'goal': 'Solve the mystery',
            }
        },
        world_rules={
            'setting': 'Modern New York City',
            'time_period': 'Present day',
        },
    )


@pytest.fixture
def book_description(db, book):
    return BookDescription.objects.create(
        book=book,
        description_html='<p>An amazing book for testing.</p>',
        description_plain='An amazing book for testing.',
        version='A',
        hook_line='You won\'t be able to put it down.',
        is_active=True,
    )
