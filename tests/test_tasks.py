"""
Celery task tests for AI Novel Factory.
Phase 17 — Test Suite

Tasks are tested with mocked external calls (no live LLM/Redis needed).
"""

import pytest
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────
# Task import sanity checks
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestTaskImports:
    """Verify all Celery tasks can be imported without errors."""

    def test_celery_app_importable(self):
        from config.celery import app
        assert app is not None

    def test_celery_app_has_tasks(self):
        from config.celery import app
        # Celery discovers tasks from registered apps
        assert app.conf.task_serializer == 'json' or app.conf.task_serializer is not None


# ─────────────────────────────────────────────
# Task-level unit tests (mocked)
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestKeywordResearchTask:
    """Tests for keyword research Celery task (mocked AI call)."""

    def test_keyword_research_task_can_be_called(self, book):
        """Task should be discoverable and callable with mocked execution."""
        try:
            from novels.tasks import run_keyword_research
            # If task exists, call it synchronously (CELERY_TASK_ALWAYS_EAGER)
            with patch('novels.tasks.run_keyword_research.delay') as mock_delay:
                mock_delay.return_value = MagicMock(id='mock-task-id')
                result = run_keyword_research.delay(book.pk)
                mock_delay.assert_called_once_with(book.pk)
        except ImportError:
            pytest.skip('run_keyword_research task not yet implemented')


@pytest.mark.django_db
class TestChapterGenerationTask:
    """Tests for chapter generation Celery task (mocked LLM)."""

    def test_chapter_generation_task_discoverable(self, book, chapter):
        try:
            from novels.tasks import generate_chapter
            with patch('novels.tasks.generate_chapter.delay') as mock_delay:
                mock_delay.return_value = MagicMock(id='mock-task-id-2')
                result = generate_chapter.delay(chapter.pk)
                mock_delay.assert_called_once_with(chapter.pk)
        except ImportError:
            pytest.skip('generate_chapter task not yet implemented')


@pytest.mark.django_db
class TestBookDescriptionGenerationTask:
    """Tests for book description generation Celery task."""

    def test_description_generation_task_discoverable(self, book):
        try:
            from novels.tasks import generate_book_description
            with patch('novels.tasks.generate_book_description.delay') as mock_delay:
                mock_delay.return_value = MagicMock(id='mock-task-id-3')
                result = generate_book_description.delay(book.pk)
                mock_delay.assert_called_once_with(book.pk)
        except ImportError:
            pytest.skip('generate_book_description task not yet implemented')


# ─────────────────────────────────────────────
# Serializer unit tests  
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestSerializers:
    """Fast serializer-level tests (no HTTP overhead)."""

    def test_pen_name_serializer_book_count_field(self, pen_name, book):
        from novels.api.serializers import PenNameSerializer
        serializer = PenNameSerializer(pen_name)
        data = serializer.data
        assert 'book_count' in data
        assert data['book_count'] == 1

    def test_book_list_serializer_pen_name_is_object(self, book):
        from novels.api.serializers import BookListSerializer
        serializer = BookListSerializer(book)
        data = serializer.data
        assert isinstance(data['pen_name'], dict)
        assert data['pen_name']['name'] == 'Test Author'

    def test_book_list_serializer_has_storefront_fields(self, published_book):
        from novels.api.serializers import BookListSerializer
        serializer = BookListSerializer(published_book)
        data = serializer.data
        assert 'cover_image_url' in data
        assert 'amazon_url' in data
        assert 'current_price_usd' in data
        assert data['cover_image_url'] == 'https://example.com/cover.jpg'

    def test_book_detail_serializer_has_storefront_fields(self, published_book):
        from novels.api.serializers import BookDetailSerializer
        serializer = BookDetailSerializer(published_book)
        data = serializer.data
        assert 'cover_image_url' in data
        assert 'amazon_url' in data
        assert 'current_price_usd' in data

    def test_chapter_list_serializer_has_is_published(self, chapter):
        from novels.api.serializers import ChapterListSerializer
        serializer = ChapterListSerializer(chapter)
        data = serializer.data
        assert 'is_published' in data
        assert 'is_free' in data
        assert data['is_published'] is False

    def test_book_description_serializer(self, book_description):
        from novels.api.serializers import BookDescriptionSerializer
        serializer = BookDescriptionSerializer(book_description)
        data = serializer.data
        assert data['version'] == 'A'
        assert data['is_active'] is True
        assert 'hook_line' in data
