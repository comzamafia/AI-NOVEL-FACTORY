"""
DRF Serializers for AI Novel Factory API.
"""

from rest_framework import serializers
from novels.models import (
    PenName,
    Book,
    StoryBible,
    Chapter,
    KeywordResearch,
    BookDescription,
    PricingStrategy,
    ReviewTracker,
    AdsPerformance,
    DistributionChannel,
    BookCover,
    CompetitorBook,
    ARCReader,
    StyleFingerprint,
)


class PenNameSerializer(serializers.ModelSerializer):
    """Serializer for PenName model."""
    book_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PenName
        fields = [
            'id',
            'name',
            'niche_genre',
            'bio',
            'writing_style_prompt',
            'profile_image',
            'website_url',
            'amazon_author_url',
            'total_books_published',
            'total_revenue_usd',
            'book_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['total_books_published', 'total_revenue_usd', 'created_at', 'updated_at']

    def get_book_count(self, obj):
        return obj.books.filter(is_deleted=False).count()


class ChapterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for chapter lists."""
    
    class Meta:
        model = Chapter
        fields = [
            'id',
            'book',
            'chapter_number',
            'title',
            'status',
            'word_count',
            'is_published',
            'is_free',
            'published_at',
        ]


class ChapterDetailSerializer(serializers.ModelSerializer):
    """Full serializer for chapter details."""
    
    class Meta:
        model = Chapter
        fields = [
            'id',
            'book',
            'chapter_number',
            'title',
            'brief',
            'content',
            'word_count',
            'status',
            'is_published',
            'is_free',
            'ai_detection_score',
            'plagiarism_score',
            'qa_notes',
            'qa_reviewed_at',
            'generation_model',
            'generation_tokens_used',
            'generation_cost_usd',
            'generation_attempts',
            'published_at',
            'drip_scheduled_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'word_count',
            'ai_detection_score',
            'plagiarism_score',
            'qa_reviewed_at',
            'generation_tokens_used',
            'generation_cost_usd',
            'generation_attempts',
            'created_at',
            'updated_at',
        ]


class StoryBibleSerializer(serializers.ModelSerializer):
    """Serializer for StoryBible model."""
    
    class Meta:
        model = StoryBible
        fields = [
            'id',
            'book',
            'characters',
            'world_rules',
            'timeline',
            'four_act_outline',
            'clues_tracker',
            'themes',
            'tone',
            'pov',
            'tense',
            'summary_for_ai',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class KeywordResearchSerializer(serializers.ModelSerializer):
    """Serializer for KeywordResearch model."""
    
    class Meta:
        model = KeywordResearch
        fields = [
            'id',
            'book',
            'primary_keywords',
            'kdp_backend_keywords',
            'kdp_category_1',
            'kdp_category_2',
            'suggested_title',
            'suggested_subtitle',
            'competitor_asins',
            'avg_competitor_reviews',
            'keyword_search_volume',
            'is_approved',
            'approved_at',
            'last_research_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['approved_at', 'last_research_at', 'created_at', 'updated_at']


class BookDescriptionSerializer(serializers.ModelSerializer):
    """Serializer for BookDescription model."""
    
    class Meta:
        model = BookDescription
        fields = [
            'id',
            'book',
            'version',
            'description_html',
            'description_plain',
            'hook_line',
            'setup_paragraph',
            'stakes_paragraph',
            'twist_tease',
            'call_to_action',
            'comparable_authors',
            'is_active',
            'is_approved',
            'character_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['description_plain', 'character_count', 'approved_at', 'created_at', 'updated_at']


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for book lists."""
    pen_name_name = serializers.CharField(source='pen_name.name', read_only=True)
    pen_name = PenNameSerializer(read_only=True)
    progress = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    published_chapter_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'subtitle',
            'synopsis',
            'pen_name',
            'pen_name_name',
            'lifecycle_status',
            'progress',
            'target_chapter_count',
            'current_word_count',
            'asin',
            'bsr',
            'published_at',
            'cover_image_url',
            'amazon_url',
            'current_price_usd',
            'avg_rating',
            'review_count',
            'published_chapter_count',
            'created_at',
        ]

    def get_progress(self, obj):
        return obj.get_progress_percentage()

    def get_avg_rating(self, obj):
        try:
            tracker = obj.review_tracker
            return float(tracker.avg_rating) if tracker.avg_rating else None
        except Exception:
            return None

    def get_review_count(self, obj):
        try:
            return obj.review_tracker.total_reviews
        except Exception:
            return 0

    def get_published_chapter_count(self, obj):
        return obj.chapters.filter(is_published=True, is_deleted=False).count()


class BookDetailSerializer(serializers.ModelSerializer):
    """Full serializer for book details."""
    pen_name_data = PenNameSerializer(source='pen_name', read_only=True)
    chapters = ChapterListSerializer(many=True, read_only=True)
    story_bible = StoryBibleSerializer(read_only=True)
    keyword_research = KeywordResearchSerializer(read_only=True)
    descriptions = BookDescriptionSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    chapter_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'subtitle',
            'synopsis',
            'pen_name',
            'pen_name_data',
            'target_audience',
            'comparable_titles',
            'hook',
            'core_twist',
            'lifecycle_status',
            'progress',
            'asin',
            'bsr',
            'published_at',
            'cover_image_url',
            'amazon_url',
            'current_price_usd',
            'ai_detection_score',
            'plagiarism_score',
            'total_revenue_usd',
            'target_chapter_count',
            'target_word_count',
            'current_word_count',
            'chapter_completion',
            'is_ai_generated_disclosure',
            'kdp_preflight_passed',
            'copyright_registered',
            'chapters',
            'story_bible',
            'keyword_research',
            'descriptions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'current_word_count',
            'ai_detection_score',
            'plagiarism_score',
            'total_revenue_usd',
            'published_at',
            'created_at',
            'updated_at',
        ]

    def get_progress(self, obj):
        return obj.get_progress_percentage()

    def get_chapter_completion(self, obj):
        return obj.get_chapter_completion_percentage()


class BookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new books."""
    
    class Meta:
        model = Book
        fields = [
            'title',
            'subtitle',
            'synopsis',
            'pen_name',
            'target_audience',
            'comparable_titles',
            'hook',
            'core_twist',
            'target_chapter_count',
            'target_word_count',
            'is_ai_generated_disclosure',
        ]


# =============================================================================
# MARKETING / ANALYTICS SERIALIZERS
# =============================================================================

class ReviewTrackerSerializer(serializers.ModelSerializer):
    """Serializer for ReviewTracker model."""

    class Meta:
        model = ReviewTracker
        fields = [
            'id',
            'book',
            'total_reviews',
            'avg_rating',
            'reviews_week_1',
            'reviews_week_2',
            'reviews_week_3',
            'reviews_week_4',
            'positive_themes',
            'negative_themes',
            'arc_emails_sent',
            'arc_reviews_received',
            'arc_conversion_rate',
            'rating_distribution',
            'last_scraped',
            'scrape_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['arc_conversion_rate', 'last_scraped', 'created_at', 'updated_at']


class AdsPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for AdsPerformance daily records."""

    class Meta:
        model = AdsPerformance
        fields = [
            'id',
            'book',
            'report_date',
            'impressions',
            'clicks',
            'spend_usd',
            'sales_usd',
            'acos',
            'ctr',
            'cpc',
            'orders',
            'units_sold',
            'top_keywords',
            'keywords_to_pause',
            'keywords_to_scale',
            'created_at',
        ]
        read_only_fields = ['acos', 'ctr', 'cpc', 'created_at']


# =============================================================================
# KDP COVER SERIALIZERS
# =============================================================================

class BookCoverSerializer(serializers.ModelSerializer):
    """Full serializer for BookCover — used in create/update/retrieve."""
    cover_type_display  = serializers.CharField(source='get_cover_type_display',  read_only=True)
    paper_type_display  = serializers.CharField(source='get_paper_type_display',  read_only=True)
    trim_size_display   = serializers.CharField(source='get_trim_size_display',   read_only=True)
    front_cover_url = serializers.SerializerMethodField()
    full_cover_url  = serializers.SerializerMethodField()
    back_cover_url  = serializers.SerializerMethodField()

    class Meta:
        model = BookCover
        fields = [
            'id',
            'book',
            'cover_type',
            'cover_type_display',
            'version_number',
            'version_note',
            'is_active',
            # Paperback
            'trim_size',
            'trim_size_display',
            'paper_type',
            'paper_type_display',
            'page_count',
            # Calculated dimensions
            'ebook_width_px',
            'ebook_height_px',
            'spine_width_in',
            'total_width_in',
            'total_height_in',
            'total_width_px',
            'total_height_px',
            # Files
            'front_cover',
            'front_cover_url',
            'full_cover',
            'full_cover_url',
            'back_cover',
            'back_cover_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'version_number',
            'created_at',
            'updated_at',
        ]

    def get_front_cover_url(self, obj):
        request = self.context.get('request')
        if obj.front_cover and request:
            return request.build_absolute_uri(obj.front_cover.url)
        return None

    def get_full_cover_url(self, obj):
        request = self.context.get('request')
        if obj.full_cover and request:
            return request.build_absolute_uri(obj.full_cover.url)
        return None

    def get_back_cover_url(self, obj):
        request = self.context.get('request')
        if obj.back_cover and request:
            return request.build_absolute_uri(obj.back_cover.url)
        return None


class BookCoverListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for cover lists."""
    cover_type_display = serializers.CharField(source='get_cover_type_display', read_only=True)
    front_cover_url    = serializers.SerializerMethodField()

    class Meta:
        model = BookCover
        fields = [
            'id',
            'book',
            'cover_type',
            'cover_type_display',
            'version_number',
            'version_note',
            'is_active',
            'trim_size',
            'paper_type',
            'page_count',
            'total_width_px',
            'total_height_px',
            'front_cover_url',
            'created_at',
        ]

    def get_front_cover_url(self, obj):
        request = self.context.get('request')
        if obj.front_cover and request:
            return request.build_absolute_uri(obj.front_cover.url)
        return None


# =============================================================================
# PRICING STRATEGY SERIALIZER
# =============================================================================

class PricingStrategySerializer(serializers.ModelSerializer):
    """Serializer for PricingStrategy model."""
    current_phase_display = serializers.CharField(
        source='get_current_phase_display', read_only=True
    )
    next_promotion_type_display = serializers.CharField(
        source='get_next_promotion_type_display', read_only=True
    )

    class Meta:
        model = PricingStrategy
        fields = [
            'id',
            'book',
            'current_phase',
            'current_phase_display',
            'current_price_usd',
            'reviews_threshold_for_growth',
            'days_in_launch_phase',
            'is_kdp_select',
            'kdp_select_enrollment_date',
            'next_promotion_date',
            'next_promotion_type',
            'next_promotion_type_display',
            'last_promotion_date',
            'days_between_promotions',
            'auto_price_enabled',
            'price_history',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# =============================================================================
# DISTRIBUTION CHANNEL SERIALIZER
# =============================================================================

class DistributionChannelSerializer(serializers.ModelSerializer):
    """Serializer for DistributionChannel model."""
    platform_display = serializers.CharField(
        source='get_platform_display', read_only=True
    )

    class Meta:
        model = DistributionChannel
        fields = [
            'id',
            'book',
            'platform',
            'platform_display',
            'asin_or_id',
            'published_url',
            'units_sold',
            'pages_read',
            'revenue_usd',
            'royalty_rate',
            'is_active',
            'published_at',
            'unpublished_at',
            'last_synced_at',
            'sync_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['last_synced_at', 'created_at', 'updated_at']


# =============================================================================
# COMPETITOR BOOK SERIALIZER
# =============================================================================

class CompetitorBookSerializer(serializers.ModelSerializer):
    """Serializer for CompetitorBook model."""

    class Meta:
        model = CompetitorBook
        fields = [
            'id',
            'asin',
            'title',
            'author',
            'genre',
            'subgenre',
            'bsr',
            'review_count',
            'avg_rating',
            'price_usd',
            'cover_style',
            'description_hooks',
            'themes',
            'estimated_monthly_units',
            'estimated_monthly_revenue',
            'last_updated',
            'tracking_start_date',
            'bsr_history',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['last_updated', 'estimated_monthly_units', 'estimated_monthly_revenue', 'created_at', 'updated_at']


# =============================================================================
# ARC READER SERIALIZER
# =============================================================================

class ARCReaderSerializer(serializers.ModelSerializer):
    """Serializer for ARCReader model."""
    reliability_rate = serializers.SerializerMethodField()

    class Meta:
        model = ARCReader
        fields = [
            'id',
            'name',
            'email',
            'genres_interested',
            'reviews_left_count',
            'arc_copies_received',
            'avg_rating_given',
            'is_reliable',
            'unreliable_count',
            'reliability_rate',
            'last_email_sent',
            'email_opt_out',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['reliability_rate', 'created_at', 'updated_at']

    def get_reliability_rate(self, obj):
        if obj.arc_copies_received == 0:
            return None
        return round((obj.reviews_left_count / obj.arc_copies_received) * 100, 1)


# =============================================================================
# STYLE FINGERPRINT SERIALIZER
# =============================================================================

class StyleFingerprintSerializer(serializers.ModelSerializer):
    """Serializer for StyleFingerprint model."""
    pen_name_name = serializers.CharField(source='pen_name.name', read_only=True)

    class Meta:
        model = StyleFingerprint
        fields = [
            'id',
            'pen_name',
            'pen_name_name',
            'avg_sentence_length',
            'avg_paragraph_length',
            'avg_chapter_length',
            'dialogue_ratio',
            'adverb_frequency',
            'passive_voice_ratio',
            'common_word_patterns',
            'forbidden_words',
            'style_system_prompt',
            'chapters_analyzed',
            'last_recalculated',
            'needs_recalculation',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['pen_name_name', 'style_system_prompt', 'last_recalculated', 'created_at', 'updated_at']


# =============================================================================
# BOOK DESCRIPTION FULL SERIALIZER
# =============================================================================

class BookDescriptionFullSerializer(serializers.ModelSerializer):
    """Full serializer for Book Description including all formula components."""

    class Meta:
        model = BookDescription
        fields = [
            'id',
            'book',
            'version',
            'description_html',
            'description_plain',
            'hook_line',
            'setup_paragraph',
            'stakes_paragraph',
            'twist_tease',
            'call_to_action',
            'comparable_authors',
            'is_active',
            'is_approved',
            'approved_at',
            'character_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['description_plain', 'character_count', 'approved_at', 'created_at', 'updated_at']
