"""
Keyword Research and Book Description models for Amazon SEO.
"""

from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from .base import BaseModel


class KeywordResearch(BaseModel):
    """
    Amazon keyword research data for a book.
    Critical for discoverability on Amazon KDP.
    """
    book = models.OneToOneField(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='keyword_research'
    )
    
    # Primary Keywords
    primary_keywords = models.JSONField(
        default=list,
        help_text="""
        Primary keywords with search volume:
        [
            {"keyword": "psychological thriller", "volume": 12000, "competition": "medium"},
            ...
        ]
        """
    )
    
    # KDP Backend Keywords (7 keywords, max 50 chars each)
    kdp_backend_keywords = models.JSONField(
        default=list,
        help_text="""
        7 backend keywords for KDP (not visible to customers):
        ["keyword1", "keyword2", ..., "keyword7"]
        """
    )
    
    # KDP Categories (2 BISAC category paths)
    kdp_category_1 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Primary BISAC category path (e.g., 'Fiction > Thrillers > Psychological')"
    )
    kdp_category_2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Secondary BISAC category path"
    )
    
    # Suggested Metadata
    suggested_title = models.CharField(
        max_length=200,
        blank=True,
        validators=[MaxLengthValidator(200)],
        help_text="AI-suggested title with keywords in first 5 words"
    )
    suggested_subtitle = models.CharField(
        max_length=200,
        blank=True,
        validators=[MaxLengthValidator(200)],
        help_text="AI-suggested subtitle with secondary keywords"
    )
    
    # Competitor Analysis
    competitor_asins = models.JSONField(
        default=list,
        help_text="""
        Top competitor ASINs with data:
        [
            {
                "asin": "B0...",
                "title": "...",
                "bsr": 1234,
                "reviews": 500,
                "rating": 4.2,
                "price": 2.99
            }
        ]
        """
    )
    avg_competitor_reviews = models.PositiveIntegerField(
        default=0,
        help_text="Average review count of top 5 competitors"
    )
    avg_competitor_bsr = models.PositiveIntegerField(
        default=0,
        help_text="Average BSR of top 5 competitors"
    )
    
    # Search Volume Data
    keyword_search_volume = models.JSONField(
        default=dict,
        help_text="""
        Monthly search volume data:
        {
            "primary_keyword": 12000,
            "long_tail_1": 500,
            ...
        }
        """
    )
    
    # Validation Status
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_keyword_research'
    )
    
    # Research Metadata
    data_source = models.CharField(
        max_length=50,
        default='dataforseo',
        help_text="API source (dataforseo, scraperapi, manual)"
    )
    last_research_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Keyword Research"
        verbose_name_plural = "Keyword Research"

    def __str__(self):
        return f"Keywords for: {self.book.title}"

    def validate_backend_keywords(self):
        """
        Validate KDP backend keywords:
        - Exactly 7 keywords
        - Each max 50 characters
        - No duplicates with title/subtitle
        - No forbidden words
        """
        errors = []
        forbidden_words = ['best', 'free', 'novel', '#1', 'bestseller', 'bestselling']
        
        if len(self.kdp_backend_keywords) != 7:
            errors.append(f"Must have exactly 7 backend keywords, got {len(self.kdp_backend_keywords)}")
        
        for i, kw in enumerate(self.kdp_backend_keywords):
            if len(kw) > 50:
                errors.append(f"Keyword {i+1} exceeds 50 characters: {len(kw)}")
            
            for forbidden in forbidden_words:
                if forbidden.lower() in kw.lower():
                    errors.append(f"Keyword {i+1} contains forbidden word: {forbidden}")
        
        # Check for duplicates with title/subtitle
        title_words = set(self.book.title.lower().split())
        subtitle_words = set(self.book.subtitle.lower().split()) if self.book.subtitle else set()
        
        for i, kw in enumerate(self.kdp_backend_keywords):
            kw_words = set(kw.lower().split())
            if kw_words & title_words:
                errors.append(f"Keyword {i+1} duplicates words from title")
        
        return errors


class BookDescriptionVersion:
    """Version choices for A/B testing."""
    VERSION_A = 'A'
    VERSION_B = 'B'
    
    CHOICES = [
        (VERSION_A, 'Version A'),
        (VERSION_B, 'Version B'),
    ]


class BookDescription(BaseModel):
    """
    Book description (blurb) for Amazon product page.
    Supports A/B testing with multiple versions.
    """
    book = models.ForeignKey(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='descriptions'
    )
    version = models.CharField(
        max_length=1,
        choices=BookDescriptionVersion.CHOICES,
        default=BookDescriptionVersion.VERSION_A
    )
    
    # HTML formatted description (Amazon supported tags only)
    description_html = models.TextField(
        help_text="HTML description (only <b>, <em>, <br>, <ul>, <li> allowed)"
    )
    
    # Plain text version
    description_plain = models.TextField(
        blank=True,
        help_text="Plain text version (auto-generated from HTML)"
    )
    
    # Formula Components
    hook_line = models.TextField(
        blank=True,
        help_text="Opening hook - question or exciting statement"
    )
    setup_paragraph = models.TextField(
        blank=True,
        help_text="Setup - who is the protagonist, what do they face"
    )
    stakes_paragraph = models.TextField(
        blank=True,
        help_text="Stakes - what happens if they fail"
    )
    twist_tease = models.TextField(
        blank=True,
        help_text="Twist tease - 'But nothing is what it seems...'"
    )
    call_to_action = models.TextField(
        blank=True,
        help_text="CTA - 'Perfect for fans of X and Y. Grab your copy today.'"
    )
    
    # Comparable Authors for CTA
    comparable_authors = models.JSONField(
        default=list,
        help_text="List of comparable authors for 'Perfect for fans of...' CTA"
    )
    
    # Status
    is_active = models.BooleanField(
        default=False,
        help_text="Is this the active description for the book"
    )
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Character Count
    character_count = models.PositiveIntegerField(
        default=0,
        help_text="Total character count (Amazon max: 4000)"
    )

    class Meta:
        verbose_name = "Book Description"
        verbose_name_plural = "Book Descriptions"
        unique_together = ['book', 'version']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.book.title} - Version {self.version} ({status})"

    def save(self, *args, **kwargs):
        # Auto-calculate character count
        if self.description_html:
            import re
            # Strip HTML tags for character count
            self.description_plain = re.sub(r'<[^>]+>', '', self.description_html)
            self.character_count = len(self.description_html)
        super().save(*args, **kwargs)

    def validate_amazon_html(self):
        """
        Validate that only Amazon-supported HTML tags are used.
        Allowed: <b>, <em>, <br>, <ul>, <li>
        """
        import re
        allowed_tags = {'b', 'em', 'br', 'ul', 'li', '/b', '/em', '/ul', '/li'}
        
        # Find all HTML tags
        tags = re.findall(r'<([^>]+)>', self.description_html)
        invalid_tags = []
        
        for tag in tags:
            tag_name = tag.split()[0].lower()
            if tag_name not in allowed_tags:
                invalid_tags.append(tag)
        
        return invalid_tags

    def validate_character_limit(self):
        """Check if description exceeds Amazon's 4000 character limit."""
        return self.character_count <= 4000
