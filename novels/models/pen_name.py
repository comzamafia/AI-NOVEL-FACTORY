"""
PenName model - Represents author personas/pen names.
"""

from django.db import models
from .base import BaseModel


class PenName(BaseModel):
    """
    Represents an author persona (pen name) in the publishing house.
    Each pen name can have its own writing style, genre niche, and multiple books.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The pen name/author name"
    )
    niche_genre = models.CharField(
        max_length=100,
        help_text="Primary genre niche (e.g., 'Psychological Thriller', 'Cozy Mystery')"
    )
    bio = models.TextField(
        blank=True,
        help_text="Author biography for Amazon author page and marketing"
    )
    writing_style_prompt = models.TextField(
        blank=True,
        help_text="Default AI prompt defining this author's writing style"
    )
    profile_image = models.ImageField(
        upload_to='pen_names/profiles/',
        null=True,
        blank=True,
        help_text="Author profile image"
    )
    
    # Social/Marketing Links
    website_url = models.URLField(blank=True)
    amazon_author_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    email_list_signup_url = models.URLField(blank=True)
    
    # Analytics
    total_books_published = models.PositiveIntegerField(default=0)
    total_revenue_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total lifetime revenue from all books"
    )

    class Meta:
        verbose_name = "Pen Name"
        verbose_name_plural = "Pen Names"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.niche_genre})"

    def update_stats(self):
        """Update aggregated statistics from related books."""
        from django.db.models import Sum, Count
        from .book import Book
        
        stats = Book.objects.filter(
            pen_name=self,
            is_deleted=False
        ).aggregate(
            book_count=Count('id'),
            total_revenue=Sum('total_revenue_usd')
        )
        
        self.total_books_published = stats['book_count'] or 0
        self.total_revenue_usd = stats['total_revenue'] or 0
        self.save(update_fields=['total_books_published', 'total_revenue_usd', 'updated_at'])
