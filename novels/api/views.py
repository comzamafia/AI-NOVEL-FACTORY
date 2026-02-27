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
    BookCover,
    CoverType,
)
from novels.utils.kdp_calculator import calc_ebook, calc_paperback, get_trim_size_choices, get_paper_type_choices
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
    BookCoverSerializer,
    BookCoverListSerializer,
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


class BookCoverViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing KDP Book Cover versions.

    Endpoints:
      GET    /api/covers/                     — list all covers (filterable)
      POST   /api/covers/                     — create new cover version
      GET    /api/covers/{id}/                — retrieve a cover
      PATCH  /api/covers/{id}/                — update cover metadata / upload file
      DELETE /api/covers/{id}/                — soft delete
      POST   /api/covers/{id}/activate/       — mark this version as active
      GET    /api/covers/calculate/           — KDP dimension calculator
      GET    /api/covers/choices/             — return trim/paper choices
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book', 'cover_type', 'is_active']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']

    def get_queryset(self):
        return BookCover.objects.filter(is_deleted=False).select_related('book')

    def get_serializer_class(self):
        if self.action == 'list':
            return BookCoverListSerializer
        return BookCoverSerializer

    def perform_create(self, serializer):
        """Auto-calculate KDP dims on create if enough info is provided."""
        instance = serializer.save()
        self._apply_calculated_dims(instance)
        instance.save()

    def perform_update(self, serializer):
        """Recalculate dims whenever metadata changes."""
        instance = serializer.save()
        self._apply_calculated_dims(instance)
        instance.save()

    def _apply_calculated_dims(self, cover: BookCover):
        """Fill in KDP-calculated dimension fields on the cover instance."""
        if cover.cover_type == CoverType.EBOOK:
            dims = calc_ebook()
            cover.ebook_width_px  = dims.width_px
            cover.ebook_height_px = dims.height_px
        elif cover.cover_type == CoverType.PAPERBACK:
            if cover.trim_size and cover.paper_type and cover.page_count:
                dims = calc_paperback(
                    trim_size=cover.trim_size,
                    paper_type=cover.paper_type,
                    page_count=cover.page_count,
                )
                if dims:
                    cover.spine_width_in  = dims.spine_width_in
                    cover.total_width_in  = dims.total_width_in
                    cover.total_height_in = dims.total_height_in
                    cover.total_width_px  = dims.total_width_px
                    cover.total_height_px = dims.total_height_px

    # ── Custom Actions ────────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Set this cover version as the active cover for its type."""
        cover = self.get_object()
        cover.activate()
        return Response(BookCoverSerializer(cover, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def calculate(self, request):
        """
        KDP dimension calculator.

        Query params for eBook:
          cover_type=ebook

        Query params for Paperback:
          cover_type=paperback
          trim_size=6x9
          paper_type=bw_white
          page_count=300
        """
        cover_type = request.query_params.get('cover_type', 'ebook')

        if cover_type == CoverType.EBOOK:
            return Response(calc_ebook().to_dict())

        # Paperback
        trim_size  = request.query_params.get('trim_size', '6x9')
        paper_type = request.query_params.get('paper_type', 'bw_white')
        try:
            page_count = int(request.query_params.get('page_count', 300))
        except ValueError:
            return Response({'error': 'page_count must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        dims = calc_paperback(trim_size, paper_type, page_count)
        if not dims:
            return Response(
                {'error': f'Unknown trim_size "{trim_size}" or paper_type "{paper_type}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(dims.to_dict())

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Return all valid trim size and paper type choices."""
        return Response({
            'trim_sizes':   get_trim_size_choices(),
            'paper_types':  get_paper_type_choices(),
            'cover_types':  [{'value': v, 'label': l} for v, l in [('ebook', 'eBook'), ('paperback', 'Paperback')]],
        })
