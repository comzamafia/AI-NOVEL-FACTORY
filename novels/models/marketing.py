"""
Pricing, Ads Performance, and Marketing models.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseModel


class PricingPhase:
    """Pricing phase choices."""
    LAUNCH = 'launch'
    GROWTH = 'growth'
    MATURE = 'mature'
    PROMO = 'promo'
    BUNDLE = 'bundle'
    
    CHOICES = [
        (LAUNCH, 'Launch Phase ($0.99)'),
        (GROWTH, 'Growth Phase ($2.99)'),
        (MATURE, 'Mature Phase ($3.99+)'),
        (PROMO, 'Promotional ($0.99)'),
        (BUNDLE, 'Bundle/Box Set'),
    ]


class PromotionType:
    """Promotion type choices."""
    KINDLE_COUNTDOWN = 'kindle_countdown'
    FREE_PROMO = 'free_promo'
    PRICE_DROP = 'price_drop'
    
    CHOICES = [
        (KINDLE_COUNTDOWN, 'Kindle Countdown Deal'),
        (FREE_PROMO, 'Free Promotion (KDP Select)'),
        (PRICE_DROP, 'Temporary Price Drop'),
    ]


class PricingStrategy(BaseModel):
    """
    Dynamic pricing strategy for a book.
    Manages price phases and automatic transitions.
    """
    book = models.OneToOneField(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='pricing_strategy'
    )
    
    # Current Pricing
    current_phase = models.CharField(
        max_length=20,
        choices=PricingPhase.CHOICES,
        default=PricingPhase.LAUNCH
    )
    current_price_usd = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.99,
        validators=[MinValueValidator(0.00), MaxValueValidator(999.99)]
    )
    
    # Phase Transition Rules
    reviews_threshold_for_growth = models.PositiveIntegerField(
        default=20,
        help_text="Reviews needed to transition from Launch to Growth"
    )
    days_in_launch_phase = models.PositiveIntegerField(
        default=7,
        help_text="Days to stay in Launch phase regardless of reviews"
    )
    
    # KDP Select Status
    is_kdp_select = models.BooleanField(
        default=True,
        help_text="Enrolled in KDP Select (required for Kindle Countdown)"
    )
    kdp_select_enrollment_date = models.DateField(null=True, blank=True)
    
    # Promotions
    next_promotion_date = models.DateField(null=True, blank=True)
    next_promotion_type = models.CharField(
        max_length=20,
        choices=PromotionType.CHOICES,
        blank=True
    )
    last_promotion_date = models.DateField(null=True, blank=True)
    days_between_promotions = models.PositiveIntegerField(
        default=90,
        help_text="Minimum days between Kindle Countdown deals"
    )
    
    # Auto-pricing
    auto_price_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic price transitions"
    )
    
    # Price History
    price_history = models.JSONField(
        default=list,
        help_text="""
        Price change history:
        [
            {"date": "2024-01-01", "price": 0.99, "phase": "launch", "reason": "Initial launch"},
            ...
        ]
        """
    )

    class Meta:
        verbose_name = "Pricing Strategy"
        verbose_name_plural = "Pricing Strategies"

    def __str__(self):
        return f"Pricing for {self.book.title}: ${self.current_price_usd} ({self.current_phase})"

    def log_price_change(self, new_price, new_phase, reason):
        """Log a price change to history."""
        from django.utils import timezone
        self.price_history.append({
            'date': timezone.now().isoformat(),
            'price': float(new_price),
            'phase': new_phase,
            'reason': reason
        })
        self.save(update_fields=['price_history', 'updated_at'])


class AdsPerformance(BaseModel):
    """
    Amazon Advertising performance tracking per book per day.
    """
    book = models.ForeignKey(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='ads_performance'
    )
    report_date = models.DateField(db_index=True)
    
    # Basic Metrics
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    spend_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sales_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Calculated Metrics
    acos = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="ACOS = (Spend / Sales) × 100"
    )
    ctr = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Click-through rate percentage"
    )
    cpc = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost per click"
    )
    
    # Keyword Performance
    top_keywords = models.JSONField(
        default=list,
        help_text="""
        Top performing keywords:
        [{"keyword": "...", "impressions": 100, "clicks": 10, "sales": 5.99}]
        """
    )
    keywords_to_pause = models.JSONField(
        default=list,
        help_text="Keywords recommended for pausing (ACOS > 70%)"
    )
    keywords_to_scale = models.JSONField(
        default=list,
        help_text="Keywords recommended for bid increase (ACOS < 25%)"
    )
    
    # Orders
    orders = models.PositiveIntegerField(default=0)
    units_sold = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Ads Performance"
        verbose_name_plural = "Ads Performance"
        unique_together = ['book', 'report_date']
        ordering = ['-report_date']

    def __str__(self):
        return f"Ads for {self.book.title} on {self.report_date}"

    def save(self, *args, **kwargs):
        # Auto-calculate ACOS
        if self.sales_usd and self.sales_usd > 0:
            self.acos = (float(self.spend_usd) / float(self.sales_usd)) * 100
        
        # Auto-calculate CTR
        if self.impressions > 0:
            self.ctr = (self.clicks / self.impressions) * 100
        
        # Auto-calculate CPC
        if self.clicks > 0:
            self.cpc = self.spend_usd / self.clicks
        
        super().save(*args, **kwargs)


class ReviewTracker(BaseModel):
    """
    Amazon review tracking for a book.
    """
    book = models.OneToOneField(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='review_tracker'
    )
    
    # Current Stats
    total_reviews = models.PositiveIntegerField(default=0)
    avg_rating = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Velocity Tracking (reviews per week since launch)
    reviews_week_1 = models.PositiveIntegerField(default=0)
    reviews_week_2 = models.PositiveIntegerField(default=0)
    reviews_week_3 = models.PositiveIntegerField(default=0)
    reviews_week_4 = models.PositiveIntegerField(default=0)
    
    # Sentiment Analysis
    positive_themes = models.JSONField(
        default=list,
        help_text="Common positive themes from reviews"
    )
    negative_themes = models.JSONField(
        default=list,
        help_text="Common negative themes/complaints from reviews"
    )
    
    # ARC Campaign Stats
    arc_emails_sent = models.PositiveIntegerField(default=0)
    arc_reviews_received = models.PositiveIntegerField(default=0)
    arc_conversion_rate = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Rating Distribution
    rating_distribution = models.JSONField(
        default=dict,
        help_text='{"5": 100, "4": 50, "3": 10, "2": 5, "1": 2}'
    )
    
    # Scraping Metadata
    last_scraped = models.DateTimeField(null=True, blank=True)
    scrape_error = models.TextField(blank=True)

    class Meta:
        verbose_name = "Review Tracker"
        verbose_name_plural = "Review Trackers"

    def __str__(self):
        return f"Reviews for {self.book.title}: {self.avg_rating}★ ({self.total_reviews} reviews)"

    def update_arc_conversion_rate(self):
        """Calculate ARC conversion rate."""
        if self.arc_emails_sent > 0:
            self.arc_conversion_rate = (self.arc_reviews_received / self.arc_emails_sent) * 100
            self.save(update_fields=['arc_conversion_rate', 'updated_at'])


class ARCReader(BaseModel):
    """
    Advance Review Copy (ARC) reader database.
    """
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    
    # Preferences
    genres_interested = models.JSONField(
        default=list,
        help_text="List of genres they're interested in"
    )
    
    # Reliability Metrics
    reviews_left_count = models.PositiveIntegerField(
        default=0,
        help_text="Total reviews left across all ARC copies received"
    )
    arc_copies_received = models.PositiveIntegerField(
        default=0,
        help_text="Total ARC copies sent to this reader"
    )
    avg_rating_given = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Reliability Flag
    is_reliable = models.BooleanField(
        default=True,
        help_text="False if reader hasn't reviewed 3+ times after receiving ARCs"
    )
    unreliable_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times they received ARC but didn't review"
    )
    
    # Communication
    last_email_sent = models.DateTimeField(null=True, blank=True)
    email_opt_out = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "ARC Reader"
        verbose_name_plural = "ARC Readers"
        ordering = ['-reviews_left_count']

    def __str__(self):
        reliability = "✓" if self.is_reliable else "✗"
        return f"{self.name} ({self.email}) - {self.reviews_left_count} reviews {reliability}"

    def mark_unreliable_if_needed(self):
        """Check and mark as unreliable if didn't review 3+ times."""
        if self.unreliable_count >= 3 and self.is_reliable:
            self.is_reliable = False
            self.save(update_fields=['is_reliable', 'updated_at'])
