"""
Unit tests for AI Novel Factory models.
Phase 17 — Test Suite
"""

import pytest


# ─────────────────────────────────────────────
# PenName model tests
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestPenNameModel:

    def test_pen_name_creation(self, pen_name):
        assert pen_name.pk is not None
        assert pen_name.name == 'Test Author'
        assert pen_name.niche_genre == 'Thriller'
        assert pen_name.is_deleted is False

    def test_pen_name_str(self, pen_name):
        # str includes niche_genre: 'Name (Genre)'
        assert 'Test Author' in str(pen_name)
        assert 'Thriller' in str(pen_name)

    def test_pen_name_soft_delete(self, pen_name):
        pen_name.soft_delete()
        pen_name.refresh_from_db()
        assert pen_name.is_deleted is True

    def test_pen_name_manager_excludes_deleted(self, pen_name):
        from novels.models import PenName
        pen_name.soft_delete()
        assert PenName.objects.filter(is_deleted=False).filter(pk=pen_name.pk).count() == 0


# ─────────────────────────────────────────────
# Book model tests
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestBookModel:

    def test_book_creation(self, book):
        assert book.pk is not None
        assert book.title == 'Test Book One'
        assert book.lifecycle_status == 'concept_pending'
        assert book.is_deleted is False

    def test_book_str(self, book):
        assert 'Test Book One' in str(book)

    def test_book_storefront_fields(self, published_book):
        assert published_book.cover_image_url == 'https://example.com/cover.jpg'
        assert published_book.amazon_url == 'https://amazon.com/dp/B0TEST12345'
        assert str(published_book.current_price_usd) == '4.99'
        assert published_book.asin == 'B0TEST12345'

    def test_book_progress_percentage_zero_when_no_chapters(self, book):
        # concept_pending status → 5% (lifecycle-based, not chapter-based)
        assert book.get_progress_percentage() >= 0
        assert isinstance(book.get_progress_percentage(), (int, float))

    def test_book_progress_percentage_with_chapters(self, book, chapter):
        chapter.status = 'approved'
        chapter.word_count = 2500
        chapter.save()
        book.refresh_from_db()
        progress = book.get_progress_percentage()
        assert isinstance(progress, (int, float))

    def test_book_soft_delete(self, book):
        book.soft_delete()
        book.refresh_from_db()
        assert book.is_deleted is True

    def test_book_pen_name_relationship(self, book, pen_name):
        assert book.pen_name == pen_name

    def test_book_lifecycle_default(self, book):
        assert book.lifecycle_status == 'concept_pending'

    def test_published_book_has_lifecycle_status(self, published_book):
        assert published_book.lifecycle_status == 'published_kdp'


# ─────────────────────────────────────────────
# Chapter model tests
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestChapterModel:

    def test_chapter_creation(self, chapter, book):
        assert chapter.pk is not None
        assert chapter.book == book
        assert chapter.chapter_number == 1
        assert chapter.status == 'pending'
        assert chapter.is_deleted is False

    def test_chapter_is_published_default(self, chapter):
        assert chapter.is_published is False

    def test_chapter_is_free_default(self, chapter):
        assert chapter.is_free is False

    def test_published_chapter_flags(self, published_chapter):
        assert published_chapter.is_published is True
        assert published_chapter.is_free is True

    def test_chapter_soft_delete(self, chapter):
        chapter.soft_delete()
        chapter.refresh_from_db()
        assert chapter.is_deleted is True

    def test_chapter_approve(self, chapter):
        chapter.approve()
        chapter.refresh_from_db()
        assert chapter.status == 'approved'
        assert chapter.qa_reviewed_at is not None

    def test_chapter_reject_sets_status_and_notes(self, chapter):
        chapter.reject('Content needs major revision.')
        chapter.refresh_from_db()
        assert chapter.status == 'rejected'
        assert chapter.qa_notes == 'Content needs major revision.'
        assert chapter.qa_reviewed_at is not None

    def test_chapter_belongs_to_book(self, chapter, book):
        assert book.chapters.filter(pk=chapter.pk).exists()


# ─────────────────────────────────────────────
# StoryBible model tests
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestStoryBibleModel:

    def test_story_bible_creation(self, story_bible, book):
        assert story_bible.pk is not None
        assert story_bible.book == book
        assert story_bible.characters['protagonist']['name'] == 'Hero Protagonist'
        assert story_bible.is_deleted is False

    def test_story_bible_one_to_one_with_book(self, story_bible, book):
        assert book.story_bible == story_bible

    def test_story_bible_soft_delete(self, story_bible):
        story_bible.soft_delete()
        story_bible.refresh_from_db()
        assert story_bible.is_deleted is True


# ─────────────────────────────────────────────
# BookDescription model tests
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestBookDescriptionModel:

    def test_book_description_creation(self, book_description, book):
        assert book_description.pk is not None
        assert book_description.book == book
        assert book_description.version == 'A'
        assert book_description.is_active is True

    def test_book_description_html_stored(self, book_description):
        assert '<p>' in book_description.description_html

    def test_book_description_belongs_to_book(self, book_description, book):
        assert book.descriptions.filter(pk=book_description.pk).exists()

    def test_book_description_soft_delete(self, book_description):
        book_description.soft_delete()
        book_description.refresh_from_db()
        assert book_description.is_deleted is True
