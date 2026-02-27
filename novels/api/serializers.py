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
    DistributionChannel,
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
