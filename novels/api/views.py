"""
DRF ViewSets for AI Novel Factory API.
"""

import os
import mimetypes
from django.http import FileResponse
from django.db.models import Sum, Count, Avg, Q

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
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
    KeywordResearch,
    ReviewTracker,
    AdsPerformance,
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
    KeywordResearchSerializer,
    ReviewTrackerSerializer,
    AdsPerformanceSerializer,
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

    # =========================================================================
    # EXPORT
    # =========================================================================

    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """
        Generate and download a .docx or .epub export.

        POST body: { "format": "docx" }  or  { "format": "epub" }
        Returns the file as a download, or error if exporter is unavailable.
        """
        book = self.get_object()
        fmt = request.data.get('format', 'docx').lower().strip('.')

        if fmt not in ('docx', 'epub'):
            return Response({'error': 'format must be "docx" or "epub"'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from novels.exporters import BookExporter
            exporter = BookExporter(book)

            if fmt == 'docx':
                file_path = exporter.export_docx()
            else:
                file_path = exporter.export_epub()

            if not file_path or not os.path.exists(file_path):
                return Response({'error': 'Export failed — no file generated'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            mime, _ = mimetypes.guess_type(file_path)
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(file_path),
                content_type=mime or 'application/octet-stream',
            )
            return response

        except ImportError:
            return Response(
                {'error': 'Export dependencies not installed (python-docx / ebooklib)'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def pipeline_stats(self, request):
        """
        Aggregate stats for the production pipeline dashboard.
        Returns book counts per lifecycle status + revenue + quality scores.
        """
        qs = Book.objects.filter(is_deleted=False)

        # Count per lifecycle status
        status_counts = {}
        for s, _ in BookLifecycleStatus.CHOICES:
            status_counts[s] = qs.filter(lifecycle_status=s).count()

        # Aggregate quality + revenue
        agg = qs.aggregate(
            total_books=Count('id'),
            total_revenue=Sum('total_revenue_usd'),
            total_words=Sum('current_word_count'),
            avg_ai_score=Avg('ai_detection_score'),
            avg_plagiarism=Avg('plagiarism_score'),
            published_count=Count('id', filter=Q(
                lifecycle_status__in=[
                    BookLifecycleStatus.PUBLISHED_KDP,
                    BookLifecycleStatus.PUBLISHED_ALL,
                ]
            )),
        )

        # Recent 5 books
        recent_books = qs.select_related('pen_name').order_by('-updated_at')[:5]
        recent = [
            {
                'id': b.id,
                'title': b.title,
                'pen_name': b.pen_name.name,
                'lifecycle_status': b.lifecycle_status,
                'progress': b.get_progress_percentage(),
                'current_word_count': b.current_word_count,
                'updated_at': b.updated_at.isoformat(),
            }
            for b in recent_books
        ]

        # Chapter stats
        chapter_agg = Chapter.objects.filter(is_deleted=False).aggregate(
            total=Count('id'),
            approved=Count('id', filter=Q(status=ChapterStatus.APPROVED)),
            published=Count('id', filter=Q(is_published=True)),
            in_review=Count('id', filter=Q(status=ChapterStatus.QA_REVIEW)),
        )

        return Response({
            'status_counts': status_counts,
            'totals': {
                'books': agg['total_books'] or 0,
                'published': agg['published_count'] or 0,
                'revenue_usd': float(agg['total_revenue'] or 0),
                'words': agg['total_words'] or 0,
                'avg_ai_detection': round(agg['avg_ai_score'] or 0, 1),
                'avg_plagiarism': round(agg['avg_plagiarism'] or 0, 1),
            },
            'chapters': chapter_agg,
            'recent_books': recent,
        })

    @action(detail=False, methods=['get'])
    def analytics_summary(self, request):
        """
        Aggregated analytics data for the analytics dashboard.
        Returns per-book revenue, review, and ads summaries.
        """
        qs = Book.objects.filter(is_deleted=False).select_related('pen_name').prefetch_related(
            'review_tracker', 'ads_performance'
        ).order_by('-total_revenue_usd')

        books_data = []
        for b in qs:
            # Review tracker
            try:
                rt = b.review_tracker
                review_data = {
                    'total_reviews': rt.total_reviews,
                    'avg_rating': float(rt.avg_rating or 0),
                    'arc_reviews_received': rt.arc_reviews_received,
                }
            except Exception:
                review_data = {'total_reviews': 0, 'avg_rating': 0, 'arc_reviews_received': 0}

            # Ads aggregation (last 30 days)
            from django.utils import timezone
            import datetime
            thirty_ago = timezone.now().date() - datetime.timedelta(days=30)
            ads_agg = b.ads_performance.filter(report_date__gte=thirty_ago).aggregate(
                total_spend=Sum('spend_usd'),
                total_sales=Sum('sales_usd'),
                total_clicks=Sum('clicks'),
                total_impressions=Sum('impressions'),
                total_orders=Sum('orders'),
            )

            books_data.append({
                'id': b.id,
                'title': b.title,
                'pen_name': b.pen_name.name if b.pen_name else '',
                'lifecycle_status': b.lifecycle_status,
                'asin': b.asin,
                'bsr': b.bsr,
                'total_revenue_usd': float(b.total_revenue_usd or 0),
                'current_price_usd': float(b.current_price_usd or 0),
                'reviews': review_data,
                'ads_30d': {
                    'spend': float(ads_agg['total_spend'] or 0),
                    'sales': float(ads_agg['total_sales'] or 0),
                    'clicks': ads_agg['total_clicks'] or 0,
                    'impressions': ads_agg['total_impressions'] or 0,
                    'orders': ads_agg['total_orders'] or 0,
                    'acos': round(
                        float(ads_agg['total_spend'] or 0) / float(ads_agg['total_sales'] or 1) * 100, 1
                    ) if (ads_agg['total_sales'] or 0) > 0 else None,
                },
            })

        # Totals
        total_revenue = sum(b['total_revenue_usd'] for b in books_data)
        total_ads_spend = sum(b['ads_30d']['spend'] for b in books_data)
        total_ads_sales = sum(b['ads_30d']['sales'] for b in books_data)

        return Response({
            'books': books_data,
            'totals': {
                'revenue_usd': total_revenue,
                'ads_spend_30d': total_ads_spend,
                'ads_sales_30d': total_ads_sales,
                'overall_acos': round(total_ads_spend / total_ads_sales * 100, 1) if total_ads_sales > 0 else None,
                'total_books': len(books_data),
            },
        })


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


# =============================================================================
# KEYWORD RESEARCH VIEWSET
# =============================================================================

class KeywordResearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Keyword Research management.

    Endpoints:
      GET    /api/keyword-research/?book={id}  — get research for a book
      PATCH  /api/keyword-research/{id}/       — update keywords manually
      POST   /api/keyword-research/{id}/approve/      — approve the research
      POST   /api/keyword-research/{id}/re_run/       — trigger new research run
      GET    /api/keyword-research/{id}/validate/     — validate backend keywords
    """
    serializer_class = KeywordResearchSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book', 'is_approved']
    ordering_fields = ['book', 'created_at', 'last_research_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return KeywordResearch.objects.filter(is_deleted=False).select_related('book')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Mark keyword research as approved."""
        from django.utils import timezone
        kw = self.get_object()
        kw.is_approved = True
        kw.approved_at = timezone.now()
        kw.save(update_fields=['is_approved', 'approved_at', 'updated_at'])
        return Response({
            'status': 'success',
            'is_approved': kw.is_approved,
            'message': 'Keyword research approved',
        })

    @action(detail=True, methods=['post'])
    def re_run(self, request, pk=None):
        """Trigger a fresh keyword research run via Celery."""
        kw = self.get_object()
        from novels.tasks.keywords import run_keyword_research
        run_keyword_research.delay(kw.book_id)
        return Response({
            'status': 'queued',
            'message': 'Keyword research task queued',
        })

    @action(detail=True, methods=['get'])
    def validate(self, request, pk=None):
        """Validate KDP backend keywords and return any errors."""
        kw = self.get_object()
        errors = kw.validate_backend_keywords()
        return Response({
            'valid': len(errors) == 0,
            'errors': errors,
            'keyword_count': len(kw.kdp_backend_keywords),
        })


# =============================================================================
# REVIEW TRACKER VIEWSET
# =============================================================================

class ReviewTrackerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Review Tracker data.
    """
    serializer_class = ReviewTrackerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book']
    ordering_fields = ['book', 'total_reviews', 'avg_rating', 'last_scraped']
    ordering = ['-total_reviews']

    def get_queryset(self):
        return ReviewTracker.objects.filter(is_deleted=False).select_related('book')


# =============================================================================
# ADS PERFORMANCE VIEWSET
# =============================================================================

class AdsPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Ads Performance daily records.
    """
    serializer_class = AdsPerformanceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book', 'report_date']
    ordering_fields = ['report_date', 'spend_usd', 'sales_usd', 'acos']
    ordering = ['-report_date']

    def get_queryset(self):
        return AdsPerformance.objects.filter(is_deleted=False).select_related('book')

