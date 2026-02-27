"""
Distribution, Competitor Intelligence, and Style Fingerprint models.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseModel


class DistributionPlatform:
    """Distribution platform choices."""
    KDP = 'kdp'
    DRAFT2DIGITAL = 'draft2digital'
    ACX = 'acx'
    PUBLISHDRIVE = 'publishdrive'
    WEBSITE = 'website'
    PATREON = 'patreon'
    APPLE_BOOKS = 'apple_books'
    KOBO = 'kobo'
    BARNES_NOBLE = 'barnes_noble'
    
    CHOICES = [
        (KDP, 'Amazon KDP'),
        (DRAFT2DIGITAL, 'Draft2Digital'),
        (ACX, 'ACX (Audiobook)'),
        (PUBLISHDRIVE, 'PublishDrive'),
        (WEBSITE, 'Own Website'),
        (PATREON, 'Patreon'),
        (APPLE_BOOKS, 'Apple Books'),
        (KOBO, 'Kobo'),
        (BARNES_NOBLE, 'Barnes & Noble'),
    ]


class DistributionChannel(BaseModel):
    """
    Tracks distribution of a book across multiple platforms.
    """
    book = models.ForeignKey(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='distribution_channels'
    )
    platform = models.CharField(
        max_length=20,
        choices=DistributionPlatform.CHOICES
    )
    
    # Platform-specific IDs
    asin_or_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ASIN, ISBN, or platform-specific ID"
    )
    published_url = models.URLField(
        blank=True,
        help_text="Direct URL to the book on this platform"
    )
    
    # Sales & Revenue
    units_sold = models.PositiveIntegerField(default=0)
    pages_read = models.PositiveIntegerField(
        default=0,
        help_text="For KU/page-read platforms"
    )
    revenue_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    royalty_rate = models.FloatField(
        default=0.70,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Royalty rate (0.35, 0.70, etc.)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    unpublished_at = models.DateTimeField(null=True, blank=True)
    
    # Sync Metadata
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.TextField(blank=True)

    class Meta:
        verbose_name = "Distribution Channel"
        verbose_name_plural = "Distribution Channels"
        unique_together = ['book', 'platform']
        ordering = ['platform']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.book.title} on {self.get_platform_display()} ({status})"


class CompetitorBook(BaseModel):
    """
    Competitor book data for market intelligence.
    """
    asin = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    
    # Classification
    genre = models.CharField(max_length=100)
    subgenre = models.CharField(max_length=100, blank=True)
    
    # Performance Metrics
    bsr = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Best Seller Rank"
    )
    review_count = models.PositiveIntegerField(default=0)
    avg_rating = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    price_usd = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Analysis
    cover_style = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cover style description (e.g., 'Dark with silhouette')"
    )
    description_hooks = models.JSONField(
        default=list,
        help_text="Effective hooks found in the description"
    )
    themes = models.JSONField(
        default=list,
        help_text="Main themes identified"
    )
    
    # Revenue Estimation
    estimated_monthly_units = models.PositiveIntegerField(
        default=0,
        help_text="Estimated monthly unit sales based on BSR"
    )
    estimated_monthly_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Tracking
    last_updated = models.DateTimeField(auto_now=True)
    tracking_start_date = models.DateField(null=True, blank=True)
    
    # BSR History
    bsr_history = models.JSONField(
        default=list,
        help_text='[{"date": "2024-01-01", "bsr": 1234}, ...]'
    )

    class Meta:
        verbose_name = "Competitor Book"
        verbose_name_plural = "Competitor Books"
        ordering = ['bsr']

    def __str__(self):
        return f"{self.title} by {self.author} (BSR: {self.bsr})"

    def estimate_revenue(self):
        """
        Estimate monthly revenue based on BSR.
        Uses the TCK Publishing BSR to sales formula approximation.
        """
        if not self.bsr or not self.price_usd:
            return
        
        # Approximate formula: lower BSR = more sales
        # BSR 1 ≈ 1000+ sales/day, BSR 10000 ≈ 10 sales/day, BSR 100000 ≈ 1 sale/day
        if self.bsr <= 100:
            daily_sales = 100
        elif self.bsr <= 1000:
            daily_sales = 50
        elif self.bsr <= 5000:
            daily_sales = 20
        elif self.bsr <= 10000:
            daily_sales = 10
        elif self.bsr <= 50000:
            daily_sales = 3
        elif self.bsr <= 100000:
            daily_sales = 1
        else:
            daily_sales = 0.3
        
        self.estimated_monthly_units = int(daily_sales * 30)
        self.estimated_monthly_revenue = self.estimated_monthly_units * float(self.price_usd) * 0.70
        self.save(update_fields=['estimated_monthly_units', 'estimated_monthly_revenue', 'updated_at'])


class StyleFingerprint(BaseModel):
    """
    Writing style fingerprint for a pen name.
    Used to maintain voice consistency across AI-generated content.
    """
    pen_name = models.OneToOneField(
        'novels.PenName',
        on_delete=models.CASCADE,
        related_name='style_fingerprint'
    )
    
    # Quantitative Metrics
    avg_sentence_length = models.FloatField(
        default=15,
        help_text="Average words per sentence"
    )
    avg_paragraph_length = models.FloatField(
        default=4,
        help_text="Average sentences per paragraph"
    )
    avg_chapter_length = models.PositiveIntegerField(
        default=1000,
        help_text="Average words per chapter"
    )
    
    # Style Ratios
    dialogue_ratio = models.FloatField(
        default=0.30,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Percentage of content that is dialogue"
    )
    adverb_frequency = models.FloatField(
        default=0.02,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Adverb usage rate"
    )
    passive_voice_ratio = models.FloatField(
        default=0.10,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Percentage of passive voice sentences"
    )
    
    # Vocabulary Patterns
    common_word_patterns = models.JSONField(
        default=dict,
        help_text="""
        Frequently used phrases and patterns:
        {
            "sentence_starters": ["He knew", "She wondered", ...],
            "transitions": ["Meanwhile", "However", ...],
            "descriptive_patterns": ["the way he", "as if", ...]
        }
        """
    )
    forbidden_words = models.JSONField(
        default=list,
        help_text="Words to avoid (clichés, overused terms)"
    )
    
    # Generated System Prompt
    style_system_prompt = models.TextField(
        blank=True,
        help_text="Auto-generated system prompt for AI to match this style"
    )
    
    # Calculation Metadata
    chapters_analyzed = models.PositiveIntegerField(default=0)
    last_recalculated = models.DateTimeField(null=True, blank=True)
    needs_recalculation = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Style Fingerprint"
        verbose_name_plural = "Style Fingerprints"

    def __str__(self):
        return f"Style Fingerprint for {self.pen_name.name}"

    def generate_system_prompt(self):
        """
        Generate an AI system prompt based on the fingerprint metrics.
        """
        prompt_parts = [
            f"Write in a style that matches these characteristics:",
            f"- Average sentence length: {self.avg_sentence_length:.1f} words",
            f"- Average paragraph length: {self.avg_paragraph_length:.1f} sentences",
            f"- Dialogue ratio: approximately {self.dialogue_ratio * 100:.0f}% of content",
            f"- Minimize adverb usage (current rate: {self.adverb_frequency * 100:.1f}%)",
            f"- Use passive voice sparingly ({self.passive_voice_ratio * 100:.0f}% maximum)",
        ]
        
        if self.common_word_patterns.get('sentence_starters'):
            starters = ', '.join(self.common_word_patterns['sentence_starters'][:5])
            prompt_parts.append(f"- Favor sentence starters like: {starters}")
        
        if self.forbidden_words:
            forbidden = ', '.join(self.forbidden_words[:10])
            prompt_parts.append(f"- Avoid these overused words: {forbidden}")
        
        self.style_system_prompt = '\n'.join(prompt_parts)
        self.save(update_fields=['style_system_prompt', 'updated_at'])
        return self.style_system_prompt
