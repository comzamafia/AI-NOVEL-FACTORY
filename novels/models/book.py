"""
Book model with BookLifecycle State Machine using django-fsm.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_fsm import FSMField, transition
from .base import BaseModel


class BookLifecycleStatus:
    """Book lifecycle status choices."""
    CONCEPT_PENDING = 'concept_pending'
    KEYWORD_RESEARCH = 'keyword_research'
    KEYWORD_APPROVED = 'keyword_approved'
    DESCRIPTION_GENERATION = 'description_generation'
    DESCRIPTION_APPROVED = 'description_approved'
    BIBLE_GENERATION = 'bible_generation'
    BIBLE_APPROVED = 'bible_approved'
    WRITING_IN_PROGRESS = 'writing_in_progress'
    QA_REVIEW = 'qa_review'
    EXPORT_READY = 'export_ready'
    PUBLISHED_KDP = 'published_kdp'
    PUBLISHED_ALL = 'published_all'
    ARCHIVED = 'archived'
    
    CHOICES = [
        (CONCEPT_PENDING, 'Concept Pending'),
        (KEYWORD_RESEARCH, 'Keyword Research'),
        (KEYWORD_APPROVED, 'Keyword Approved'),
        (DESCRIPTION_GENERATION, 'Description Generation'),
        (DESCRIPTION_APPROVED, 'Description Approved'),
        (BIBLE_GENERATION, 'Bible Generation'),
        (BIBLE_APPROVED, 'Bible Approved'),
        (WRITING_IN_PROGRESS, 'Writing In Progress'),
        (QA_REVIEW, 'QA Review'),
        (EXPORT_READY, 'Export Ready'),
        (PUBLISHED_KDP, 'Published on KDP'),
        (PUBLISHED_ALL, 'Published on All Platforms'),
        (ARCHIVED, 'Archived'),
    ]


class Book(BaseModel):
    """
    Main Book model with FSM lifecycle management.
    """
    # Basic Information
    title = models.CharField(
        max_length=200,
        help_text="Primary title (max 200 chars for KDP)"
    )
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        help_text="Subtitle for SEO (max 200 chars for KDP)"
    )
    synopsis = models.TextField(
        blank=True,
        help_text="Internal synopsis/concept summary"
    )
    
    # Author
    pen_name = models.ForeignKey(
        'novels.PenName',
        on_delete=models.PROTECT,
        related_name='books'
    )
    
    # Market Research
    target_audience = models.CharField(
        max_length=255,
        blank=True,
        help_text="Target reader demographic"
    )
    comparable_titles = models.JSONField(
        default=list,
        blank=True,
        help_text="List of comparable book titles for positioning"
    )
    hook = models.TextField(
        blank=True,
        help_text="The core hook or concept that makes this book unique"
    )
    core_twist = models.TextField(
        blank=True,
        help_text="The main twist or revelation in the story"
    )
    
    # Lifecycle State Machine
    lifecycle_status = FSMField(
        default=BookLifecycleStatus.CONCEPT_PENDING,
        choices=BookLifecycleStatus.CHOICES,
        db_index=True,
        help_text="Current stage in the book production pipeline"
    )
    
    # Publishing Data
    asin = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text="Amazon Standard Identification Number"
    )
    bsr = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Best Seller Rank on Amazon"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when book was first published"
    )

    # Storefront Fields
    cover_image_url = models.URLField(
        blank=True,
        help_text="URL to book cover image (external CDN or uploaded)"
    )
    amazon_url = models.URLField(
        blank=True,
        help_text="Full Amazon product page URL"
    )
    current_price_usd = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Current retail price in USD (synced from PricingStrategy)"
    )
    
    # Quality Scores
    ai_detection_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI detection percentage from Originality.ai"
    )
    plagiarism_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Plagiarism percentage from Copyscape"
    )
    
    # Revenue Tracking
    total_revenue_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Content Stats
    target_chapter_count = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(10), MaxValueValidator(200)],
        help_text="Target number of chapters (70-90 typical)"
    )
    target_word_count = models.PositiveIntegerField(
        default=80000,
        help_text="Target total word count"
    )
    current_word_count = models.PositiveIntegerField(default=0)
    
    # KDP Compliance Flags
    is_ai_generated_disclosure = models.BooleanField(
        default=True,
        help_text="If True, content is 'AI-Generated' (must disclose to KDP)"
    )
    kdp_preflight_passed = models.BooleanField(default=False)
    copyright_registered = models.BooleanField(default=False)

    # Concept Engine (Phase 3)
    book_concepts = models.JSONField(
        default=list,
        blank=True,
        help_text='AI-generated concept options [{title, hook, core_twist}, ...]'
    )
    approved_concept = models.JSONField(
        null=True,
        blank=True,
        help_text='The approved concept selected by admin'
    )
    
    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lifecycle_status', 'is_deleted']),
            models.Index(fields=['pen_name', 'lifecycle_status']),
        ]

    def __str__(self):
        return f"{self.title} by {self.pen_name.name}"

    # ==========================================================================
    # FSM TRANSITIONS
    # ==========================================================================

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.CONCEPT_PENDING,
        target=BookLifecycleStatus.KEYWORD_RESEARCH
    )
    def start_keyword_research(self):
        """Approve concept and begin keyword research."""
        pass

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.KEYWORD_RESEARCH,
        target=BookLifecycleStatus.KEYWORD_APPROVED
    )
    def approve_keywords(self):
        """Approve keywords and metadata."""
        pass

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.KEYWORD_APPROVED,
        target=BookLifecycleStatus.DESCRIPTION_GENERATION
    )
    def start_description_generation(self):
        """Begin generating book description."""
        pass

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.DESCRIPTION_GENERATION,
        target=BookLifecycleStatus.DESCRIPTION_APPROVED
    )
    def approve_description(self):
        """Approve the book description."""
        pass

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.DESCRIPTION_APPROVED,
        target=BookLifecycleStatus.BIBLE_GENERATION
    )
    def start_bible_generation(self):
        """Begin generating story bible."""
        pass

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.BIBLE_GENERATION,
        target=BookLifecycleStatus.BIBLE_APPROVED
    )
    def approve_bible(self):
        """Approve story bible and chapter briefs."""
        pass

    @transition(
        field=lifecycle_status,
        source=[
            BookLifecycleStatus.BIBLE_APPROVED,
            BookLifecycleStatus.KEYWORD_APPROVED,
            BookLifecycleStatus.BIBLE_GENERATION,
        ],
        target=BookLifecycleStatus.WRITING_IN_PROGRESS
    )
    def start_writing(self):
        """Begin content generation."""
        pass

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.WRITING_IN_PROGRESS,
        target=BookLifecycleStatus.QA_REVIEW
    )
    def submit_for_qa(self):
        """Submit completed content for QA review."""
        pass

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.QA_REVIEW,
        target=BookLifecycleStatus.WRITING_IN_PROGRESS
    )
    def return_to_writing(self):
        """Return to writing for revisions."""
        pass

    @transition(
        field=lifecycle_status,
        source=[
            BookLifecycleStatus.QA_REVIEW,
            BookLifecycleStatus.WRITING_IN_PROGRESS,
        ],
        target=BookLifecycleStatus.EXPORT_READY
    )
    def approve_for_export(self):
        """Approve content and prepare for export."""
        self.kdp_preflight_passed = True

    # Alias for admin_views compatibility
    approve_qa = approve_for_export

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.EXPORT_READY,
        target=BookLifecycleStatus.PUBLISHED_KDP
    )
    def publish_to_kdp(self):
        """Mark as published on Amazon KDP."""
        from django.utils import timezone
        if not self.published_at:
            self.published_at = timezone.now()

    # Alias
    publish_kdp = publish_to_kdp

    @transition(
        field=lifecycle_status,
        source=BookLifecycleStatus.PUBLISHED_KDP,
        target=BookLifecycleStatus.PUBLISHED_ALL
    )
    def publish_to_all_platforms(self):
        """Mark as published on all platforms."""
        pass

    @transition(
        field=lifecycle_status,
        source=[
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL
        ],
        target=BookLifecycleStatus.ARCHIVED
    )
    def archive(self):
        """Archive the book."""
        pass

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def get_progress_percentage(self):
        """Calculate overall progress percentage based on lifecycle status."""
        status_progress = {
            BookLifecycleStatus.CONCEPT_PENDING: 5,
            BookLifecycleStatus.KEYWORD_RESEARCH: 10,
            BookLifecycleStatus.KEYWORD_APPROVED: 15,
            BookLifecycleStatus.DESCRIPTION_GENERATION: 20,
            BookLifecycleStatus.DESCRIPTION_APPROVED: 25,
            BookLifecycleStatus.BIBLE_GENERATION: 30,
            BookLifecycleStatus.BIBLE_APPROVED: 35,
            BookLifecycleStatus.WRITING_IN_PROGRESS: 50,
            BookLifecycleStatus.QA_REVIEW: 80,
            BookLifecycleStatus.EXPORT_READY: 90,
            BookLifecycleStatus.PUBLISHED_KDP: 95,
            BookLifecycleStatus.PUBLISHED_ALL: 100,
            BookLifecycleStatus.ARCHIVED: 100,
        }
        return status_progress.get(self.lifecycle_status, 0)

    def get_chapter_completion_percentage(self):
        """Calculate percentage of chapters completed."""
        if self.target_chapter_count == 0:
            return 0
        completed = self.chapters.filter(status='approved').count()
        return round((completed / self.target_chapter_count) * 100, 1)

    def update_word_count(self):
        """Recalculate total word count from all chapters."""
        from django.db.models import Sum
        total = self.chapters.filter(
            is_deleted=False
        ).aggregate(
            total=Sum('word_count')
        )['total']
        self.current_word_count = total or 0
        self.save(update_fields=['current_word_count', 'updated_at'])
