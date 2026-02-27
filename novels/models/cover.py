"""
BookCover model — stores KDP cover files and calculated dimensions per version.
"""

from django.db import models
from .base import BaseModel


class CoverType:
    EBOOK = 'ebook'
    PAPERBACK = 'paperback'
    CHOICES = [
        (EBOOK, 'eBook'),
        (PAPERBACK, 'Paperback'),
    ]


class PaperType:
    BW_WHITE = 'bw_white'
    BW_CREAM = 'bw_cream'
    COLOR = 'color'
    CHOICES = [
        (BW_WHITE, 'B&W White Paper'),
        (BW_CREAM, 'B&W Cream Paper'),
        (COLOR, 'Color Paper'),
    ]
    # KDP spine width multipliers (inches per page)
    SPINE_MULTIPLIER = {
        BW_WHITE: 0.002252,
        BW_CREAM: 0.002500,
        COLOR: 0.002347,
    }


class TrimSize:
    CHOICES = [
        ('5x8',       '5" × 8"'),
        ('5.06x7.81', '5.06" × 7.81"'),
        ('5.25x8',    '5.25" × 8"'),
        ('5.5x8.5',   '5.5" × 8.5"'),
        ('5.83x8.27', '5.83" × 8.27" (A5)'),
        ('6x9',       '6" × 9"'),
        ('6.14x9.21', '6.14" × 9.21"'),
        ('6.69x9.61', '6.69" × 9.61"'),
        ('7x10',      '7" × 10"'),
        ('7.44x9.69', '7.44" × 9.69"'),
        ('8x10',      '8" × 10"'),
        ('8.5x8.5',   '8.5" × 8.5" (Square)'),
        ('8.5x11',    '8.5" × 11"'),
    ]
    # width, height in inches
    DIMENSIONS = {
        '5x8':       (5.00, 8.00),
        '5.06x7.81': (5.06, 7.81),
        '5.25x8':    (5.25, 8.00),
        '5.5x8.5':   (5.50, 8.50),
        '5.83x8.27': (5.83, 8.27),
        '6x9':       (6.00, 9.00),
        '6.14x9.21': (6.14, 9.21),
        '6.69x9.61': (6.69, 9.61),
        '7x10':      (7.00, 10.00),
        '7.44x9.69': (7.44, 9.69),
        '8x10':      (8.00, 10.00),
        '8.5x8.5':   (8.50, 8.50),
        '8.5x11':    (8.50, 11.00),
    }


class BookCover(BaseModel):
    """
    Tracks each version of a book cover (eBook or Paperback).
    Stores KDP-calculated dimensions alongside uploaded cover files.
    """
    book = models.ForeignKey(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='covers',
    )
    cover_type = models.CharField(
        max_length=20,
        choices=CoverType.CHOICES,
        default=CoverType.EBOOK,
        db_index=True,
    )
    version_number = models.PositiveIntegerField(
        default=1,
        help_text='Auto-incremented version per book+type',
    )
    version_note = models.TextField(
        blank=True,
        help_text='Designer notes or change description for this version',
    )
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text='The currently active/approved cover for this type',
    )

    # ── Paperback-specific ─────────────────────────────────────────────────
    trim_size = models.CharField(
        max_length=20,
        choices=TrimSize.CHOICES,
        blank=True,
        help_text='KDP trim size (paperback only)',
    )
    paper_type = models.CharField(
        max_length=20,
        choices=PaperType.CHOICES,
        blank=True,
        help_text='Paper type affects spine width (paperback only)',
    )
    page_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Total interior pages (paperback only)',
    )

    # ── Calculated KDP Dimensions ──────────────────────────────────────────
    # eBook
    ebook_width_px = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='eBook cover width in pixels (recommended 1600)',
    )
    ebook_height_px = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='eBook cover height in pixels (recommended 2560)',
    )
    # Paperback
    spine_width_in = models.DecimalField(
        max_digits=8, decimal_places=4,
        null=True, blank=True,
        help_text='Calculated spine width in inches',
    )
    total_width_in = models.DecimalField(
        max_digits=8, decimal_places=4,
        null=True, blank=True,
        help_text='Full cover width including bleed (in inches)',
    )
    total_height_in = models.DecimalField(
        max_digits=8, decimal_places=4,
        null=True, blank=True,
        help_text='Full cover height including bleed (in inches)',
    )
    total_width_px = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Full cover width at 300 DPI (pixels)',
    )
    total_height_px = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Full cover height at 300 DPI (pixels)',
    )

    # ── Cover Files ────────────────────────────────────────────────────────
    front_cover = models.ImageField(
        upload_to='covers/front/',
        blank=True,
        help_text='Front cover image (eBook: JPEG/PNG, Paperback: high-res)',
    )
    full_cover = models.ImageField(
        upload_to='covers/full/',
        blank=True,
        help_text='Full wrap cover PDF/PNG (paperback only: front+spine+back)',
    )
    back_cover = models.ImageField(
        upload_to='covers/back/',
        blank=True,
        help_text='Back cover image (optional, paperback)',
    )

    class Meta:
        ordering = ['book', 'cover_type', '-version_number']
        unique_together = [('book', 'cover_type', 'version_number')]
        verbose_name = 'Book Cover'
        verbose_name_plural = 'Book Covers'

    def __str__(self):
        return f'{self.book.title} — {self.get_cover_type_display()} v{self.version_number}'

    def save(self, *args, **kwargs):
        # Auto-assign version number if new
        if not self.pk and not self.version_number:
            last = BookCover.objects.filter(
                book=self.book,
                cover_type=self.cover_type,
            ).order_by('-version_number').first()
            self.version_number = (last.version_number + 1) if last else 1

        # Only one cover can be active per book+type
        if self.is_active:
            BookCover.objects.filter(
                book=self.book,
                cover_type=self.cover_type,
                is_active=True,
            ).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    def activate(self):
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
