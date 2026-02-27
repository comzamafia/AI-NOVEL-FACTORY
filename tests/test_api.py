"""
DRF API endpoint tests for AI Novel Factory.
Phase 17 — Test Suite
"""

import pytest


API = '/api'


# ─────────────────────────────────────────────
# PenName API
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestPenNameAPI:

    def test_list_pen_names_unauthenticated(self, api_client, pen_name):
        """Storefront reads should be public."""
        r = api_client.get(f'{API}/pen-names/')
        assert r.status_code == 200

    def test_list_pen_names_returns_results(self, api_client, pen_name):
        r = api_client.get(f'{API}/pen-names/')
        assert r.json()['count'] >= 1

    def test_retrieve_pen_name(self, api_client, pen_name):
        r = api_client.get(f'{API}/pen-names/{pen_name.pk}/')
        assert r.status_code == 200
        data = r.json()
        assert data['name'] == 'Test Author'
        assert data['niche_genre'] == 'Thriller'

    def test_pen_name_response_has_book_count(self, api_client, pen_name):
        r = api_client.get(f'{API}/pen-names/{pen_name.pk}/')
        data = r.json()
        assert 'book_count' in data

    def test_create_pen_name_requires_auth(self, api_client):
        # IsAuthenticatedOrReadOnly returns 403 for anonymous write attempts
        r = api_client.post(f'{API}/pen-names/', {'name': 'Anon', 'niche_genre': 'Mystery'})
        assert r.status_code == 403

    def test_create_pen_name_authenticated(self, auth_client):
        r = auth_client.post(f'{API}/pen-names/', {
            'name': 'New Author',
            'niche_genre': 'Romance',
            'bio': 'Bio here.',
        })
        assert r.status_code == 201
        assert r.json()['name'] == 'New Author'

    def test_search_pen_names(self, api_client, pen_name):
        r = api_client.get(f'{API}/pen-names/?search=Test+Author')
        assert r.status_code == 200
        assert r.json()['count'] >= 1


# ─────────────────────────────────────────────
# Book API
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestBookAPI:

    def test_list_books_unauthenticated(self, api_client, book):
        """Storefront reads must be public."""
        r = api_client.get(f'{API}/books/')
        assert r.status_code == 200

    def test_list_books_returns_results(self, api_client, book):
        r = api_client.get(f'{API}/books/')
        assert r.json()['count'] >= 1

    def test_list_books_contains_cover_image_url(self, api_client, published_book):
        r = api_client.get(f'{API}/books/')
        books = r.json()['results']
        pbook = next(b for b in books if b['id'] == published_book.pk)
        assert 'cover_image_url' in pbook
        assert pbook['cover_image_url'] == 'https://example.com/cover.jpg'

    def test_list_books_contains_pen_name_object(self, api_client, book):
        r = api_client.get(f'{API}/books/')
        first = r.json()['results'][0]
        assert isinstance(first['pen_name'], dict)
        assert 'name' in first['pen_name']

    def test_retrieve_book_unauthenticated(self, api_client, book):
        r = api_client.get(f'{API}/books/{book.pk}/')
        assert r.status_code == 200

    def test_retrieve_book_detail_has_chapters(self, api_client, book, chapter):
        r = api_client.get(f'{API}/books/{book.pk}/')
        data = r.json()
        assert 'chapters' in data

    def test_create_book_requires_auth(self, api_client, pen_name):
        # IsAuthenticatedOrReadOnly returns 403 for anonymous write attempts
        r = api_client.post(f'{API}/books/', {'title': 'Sneaky Book', 'pen_name': pen_name.pk})
        assert r.status_code == 403

    def test_create_book_authenticated(self, auth_client, pen_name):
        r = auth_client.post(f'{API}/books/', {
            'title': 'Auth Book',
            'synopsis': 'A properly created book.',
            'pen_name': pen_name.pk,
            'target_chapter_count': 20,
            'target_word_count': 50000,
        })
        assert r.status_code == 201
        assert r.json()['title'] == 'Auth Book'

    def test_filter_books_by_pen_name(self, api_client, book, pen_name):
        r = api_client.get(f'{API}/books/?pen_name={pen_name.pk}')
        assert r.status_code == 200
        assert r.json()['count'] >= 1

    def test_filter_books_by_lifecycle_status(self, api_client, book, published_book):
        r = api_client.get(f'{API}/books/?lifecycle_status=published_kdp')
        assert r.status_code == 200
        ids = [b['id'] for b in r.json()['results']]
        assert published_book.pk in ids

    def test_search_books(self, api_client, book):
        r = api_client.get(f'{API}/books/?search=Test+Book+One')
        assert r.status_code == 200
        assert r.json()['count'] >= 1

    def test_book_does_not_expose_deleted(self, api_client, book):
        book.soft_delete()
        r = api_client.get(f'{API}/books/')
        ids = [b['id'] for b in r.json()['results']]
        assert book.pk not in ids


# ─────────────────────────────────────────────
# Chapter API
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestChapterAPI:

    def test_list_chapters_unauthenticated(self, api_client, chapter):
        r = api_client.get(f'{API}/chapters/')
        assert r.status_code == 200

    def test_list_chapters_returns_results(self, api_client, chapter):
        r = api_client.get(f'{API}/chapters/')
        assert r.json()['count'] >= 1

    def test_chapter_list_has_is_published_field(self, api_client, chapter):
        r = api_client.get(f'{API}/chapters/')
        first = r.json()['results'][0]
        assert 'is_published' in first
        assert 'is_free' in first

    def test_filter_chapters_by_is_published(self, api_client, chapter, published_chapter):
        r = api_client.get(f'{API}/chapters/?is_published=true')
        assert r.status_code == 200
        ids = [c['id'] for c in r.json()['results']]
        assert published_chapter.pk in ids
        assert chapter.pk not in ids

    def test_filter_chapters_by_book(self, api_client, chapter, book):
        r = api_client.get(f'{API}/chapters/?book={book.pk}')
        assert r.status_code == 200
        assert r.json()['count'] >= 1

    def test_create_chapter_requires_auth(self, api_client, book):
        # IsAuthenticatedOrReadOnly returns 403 for anonymous write attempts
        r = api_client.post(f'{API}/chapters/', {'book': book.pk, 'chapter_number': 99})
        assert r.status_code == 403

    def test_create_chapter_authenticated(self, auth_client, book):
        r = auth_client.post(f'{API}/chapters/', {
            'book': book.pk,
            'chapter_number': 5,
            'title': 'A New Chapter',
        })
        assert r.status_code == 201

    def test_chapter_does_not_expose_deleted(self, api_client, chapter):
        chapter.soft_delete()
        r = api_client.get(f'{API}/chapters/')
        ids = [c['id'] for c in r.json()['results']]
        assert chapter.pk not in ids


# ─────────────────────────────────────────────
# BookDescription API
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestBookDescriptionAPI:

    def test_list_book_descriptions_unauthenticated(self, api_client, book_description):
        r = api_client.get(f'{API}/book-descriptions/')
        assert r.status_code == 200

    def test_list_book_descriptions_returns_results(self, api_client, book_description):
        r = api_client.get(f'{API}/book-descriptions/')
        assert r.json()['count'] >= 1

    def test_filter_by_book(self, api_client, book_description, book):
        r = api_client.get(f'{API}/book-descriptions/?book={book.pk}')
        assert r.status_code == 200
        assert r.json()['count'] >= 1

    def test_filter_by_is_active(self, api_client, book_description):
        r = api_client.get(f'{API}/book-descriptions/?is_active=true')
        assert r.status_code == 200
        for desc in r.json()['results']:
            assert desc['is_active'] is True

    def test_book_description_is_read_only(self, auth_client, book):
        """Endpoint is ReadOnlyModelViewSet — POST must return 405."""
        r = auth_client.post(f'{API}/book-descriptions/', {
            'book': book.pk,
            'description_html': '<p>Test</p>',
        })
        assert r.status_code == 405

    def test_retrieve_book_description(self, api_client, book_description):
        r = api_client.get(f'{API}/book-descriptions/{book_description.pk}/')
        assert r.status_code == 200
        data = r.json()
        assert data['hook_line'] == "You won't be able to put it down."

    def test_description_does_not_expose_deleted(self, api_client, book_description):
        book_description.soft_delete()
        r = api_client.get(f'{API}/book-descriptions/')
        ids = [d['id'] for d in r.json()['results']]
        assert book_description.pk not in ids


# ─────────────────────────────────────────────
# StoryBible API
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestStoryBibleAPI:

    def test_list_story_bibles_unauthenticated(self, api_client, story_bible):
        r = api_client.get(f'{API}/story-bibles/')
        assert r.status_code == 200

    def test_filter_by_book(self, api_client, story_bible, book):
        r = api_client.get(f'{API}/story-bibles/?book={book.pk}')
        assert r.status_code == 200
        assert r.json()['count'] >= 1

    def test_create_story_bible_requires_auth(self, api_client, book):
        # IsAuthenticatedOrReadOnly returns 403 for anonymous write attempts
        r = api_client.post(f'{API}/story-bibles/', {'book': book.pk})
        assert r.status_code == 403
