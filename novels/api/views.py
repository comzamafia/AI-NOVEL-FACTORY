"""
DRF ViewSets for AI Novel Factory API.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from novels.models import (
    PenName,
    Book,
    BookDescription,
    StoryBible,
    Chapter,
    BookLifecycleStatus,
    ChapterStatus,
)
from novels.tasks.keywords import run_keyword_research
from novels.tasks.content import generate_book_description, generate_story_bible, rewrite_chapter
from novels.throttles import AIGenerationThrottle, BurstThrottle, ChapterWriteThrottle
from .serializers import (
    PenNameSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BookCreateSerializer,
    BookDescriptionSerializer,
    ChapterListSerializer,
    ChapterDetailSerializer,
    StoryBibleSerializer,
)


class PenNameViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Pen Name (Author) management.
    """
    serializer_class = PenNameSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'niche_genre', 'bio']
    ordering_fields = ['name', 'total_books_published', 'total_revenue_usd', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return PenName.objects.filter(is_deleted=False)

    @action(detail=True, methods=['post'])
    def update_stats(self, request, pk=None):
        """Recalculate stats for a pen name."""
        pen_name = self.get_object()
        pen_name.update_stats()
        serializer = self.get_serializer(pen_name)
        return Response(serializer.data)


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Book management with lifecycle actions.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['pen_name', 'lifecycle_status']
    search_fields = ['title', 'subtitle', 'synopsis', 'pen_name__name']
    ordering_fields = ['title', 'created_at', 'published_at', 'bsr']
    ordering = ['-created_at']

    # Actions that trigger expensive AI generation get a tighter throttle
    _AI_ACTIONS = {
        'start_description_generation',
        'start_bible_generation',
        'generate_chapter_briefs',
        'generate_book_concepts',
    }

    def get_throttles(self):
        if self.action in self._AI_ACTIONS:
            return [AIGenerationThrottle(), BurstThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return Book.objects.filter(is_deleted=False).select_related('pen_name')

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        elif self.action == 'create':
            return BookCreateSerializer
        return BookDetailSerializer

    # =========================================================================
    # LIFECYCLE TRANSITIONS
    # =========================================================================

    @action(detail=True, methods=['post'])
    def start_keyword_research(self, request, pk=None):
        """Transition: concept_pending -> keyword_research"""
        book = self.get_object()
        try:
            book.start_keyword_research()
            book.save()
            # Trigger keyword research task
            run_keyword_research.delay(book.id)
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Keyword research started'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve_keywords(self, request, pk=None):
        """Transition: keyword_research -> keyword_approved"""
        book = self.get_object()
        try:
            book.approve_keywords()
            book.save()
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Keywords approved'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def start_description_generation(self, request, pk=None):
        """Transition: keyword_approved -> description_generation"""
        book = self.get_object()
        try:
            book.start_description_generation()
            book.save()
            generate_book_description.delay(book.id)
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Description generation started'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve_description(self, request, pk=None):
        """Transition: description_generation -> description_approved"""
        book = self.get_object()
        try:
            book.approve_description()
            book.save()
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Description approved'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def start_bible_generation(self, request, pk=None):
        """Transition: description_approved -> bible_generation"""
        book = self.get_object()
        try:
            book.start_bible_generation()
            book.save()
            generate_story_bible.delay(book.id)
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Story bible generation started'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve_bible(self, request, pk=None):
        """Transition: bible_generation -> bible_approved"""
        book = self.get_object()
        try:
            book.approve_bible()
            book.save()
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Story bible approved'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def start_writing(self, request, pk=None):
        """Transition: bible_approved -> writing_in_progress"""
        book = self.get_object()
        try:
            book.start_writing()
            book.save()
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Writing started'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def submit_for_qa(self, request, pk=None):
        """Transition: writing_in_progress -> qa_review"""
        book = self.get_object()
        try:
            book.submit_for_qa()
            book.save()
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Submitted for QA review'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve_for_export(self, request, pk=None):
        """Transition: qa_review -> export_ready"""
        book = self.get_object()
        try:
            book.approve_for_export()
            book.save()
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Approved for export'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def publish_to_kdp(self, request, pk=None):
        """Transition: export_ready -> published_kdp"""
        book = self.get_object()
        try:
            book.publish_to_kdp()
            book.save()
            return Response({
                'status': 'success',
                'lifecycle_status': book.lifecycle_status,
                'message': 'Published to KDP'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChapterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Chapter management.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book', 'status', 'is_published', 'chapter_number']
    ordering_fields = ['chapter_number', 'status', 'created_at']
    ordering = ['book', 'chapter_number']

    def get_queryset(self):
        return Chapter.objects.filter(is_deleted=False).select_related('book')

    def get_serializer_class(self):
        if self.action == 'list':
            return ChapterListSerializer
        return ChapterDetailSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a chapter after QA."""
        chapter = self.get_object()
        chapter.approve()
        return Response({
            'status': 'success',
            'chapter_status': chapter.status,
            'message': 'Chapter approved'
        })

    def get_throttles(self):
        if self.action in ('mark_ready_to_write', 'reject'):
            return [ChapterWriteThrottle(), BurstThrottle()]
        return super().get_throttles()

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a chapter and mark for rewrite."""
        chapter = self.get_object()
        notes = request.data.get('notes', '')
        if not notes:
            return Response(
                {'error': 'Notes are required for rejection'},
                status=status.HTTP_400_BAD_REQUEST
            )
        chapter.reject(notes)
        rewrite_chapter.delay(chapter.id, notes)
        return Response({
            'status': 'success',
            'chapter_status': chapter.status,
            'message': 'Chapter rejected for rewrite'
        })

    @action(detail=True, methods=['post'])
    def mark_ready_to_write(self, request, pk=None):
        """Mark a chapter as ready for AI writing."""
        chapter = self.get_object()
        chapter.mark_ready_to_write()
        return Response({
            'status': 'success',
            'chapter_status': chapter.status,
            'message': 'Chapter marked ready to write'
        })


class BookDescriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Book Descriptions (storefront copy).
    """
    serializer_class = BookDescriptionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book', 'is_active', 'version']
    ordering_fields = ['book', 'version', 'created_at']
    ordering = ['book', 'version']

    def get_queryset(self):
        return BookDescription.objects.filter(is_deleted=False).select_related('book')


class StoryBibleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Story Bible management.
    """
    serializer_class = StoryBibleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book']
    ordering_fields = ['book', 'created_at']
    ordering = ['book']

    def get_queryset(self):
        return StoryBible.objects.filter(is_deleted=False).select_related('book')

    @action(detail=True, methods=['post'])
    def generate_summary(self, request, pk=None):
        """Generate AI summary for prompt injection."""
        story_bible = self.get_object()
        story_bible.generate_ai_summary()
        return Response({
            'status': 'success',
            'summary': story_bible.summary_for_ai,
            'message': 'AI summary generated'
        })
