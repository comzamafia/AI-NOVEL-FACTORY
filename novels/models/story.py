"""
StoryBible and Chapter models for story architecture.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseModel


class StoryBible(BaseModel):
    """
    Story bible containing all the metadata needed for consistent story generation.
    Each book has exactly one story bible.
    """
    book = models.OneToOneField(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='story_bible'
    )
    
    # Characters
    characters = models.JSONField(
        default=dict,
        help_text="""
        Character definitions in format:
        {
            "protagonist": {
                "name": "...",
                "age": ...,
                "occupation": "...",
                "personality": "...",
                "wound": "...",
                "goal": "...",
                "arc": "..."
            },
            "antagonist": {...},
            "supporting": [{...}, {...}]
        }
        """
    )
    
    # World Building
    world_rules = models.JSONField(
        default=dict,
        help_text="""
        World/setting rules:
        {
            "setting": "...",
            "time_period": "...",
            "locations": [{...}],
            "important_rules": ["..."],
            "technology_level": "...",
            "social_structures": "..."
        }
        """
    )
    
    # Timeline
    timeline = models.JSONField(
        default=list,
        help_text="""
        Story timeline events:
        [
            {"day": 1, "event": "...", "chapter_range": [1, 5]},
            ...
        ]
        """
    )
    
    # Four-Act Structure
    four_act_outline = models.JSONField(
        default=dict,
        help_text="""
        Four-act structure:
        {
            "act_1_setup": {
                "chapters": [1, 20],
                "summary": "...",
                "key_events": ["..."]
            },
            "act_2_confrontation": {...},
            "act_3_complication": {...},
            "act_4_resolution": {...}
        }
        """
    )
    
    # Clue & Red Herring Tracker (for Mystery/Thriller)
    clues_tracker = models.JSONField(
        default=list,
        help_text="""
        Clue tracking for mysteries:
        [
            {
                "clue_id": "clue_001",
                "description": "...",
                "planted_in_chapter": 5,
                "revealed_in_chapter": 45,
                "is_red_herring": false,
                "connected_to": ["clue_002"]
            }
        ]
        """
    )
    
    # Themes
    themes = models.JSONField(
        default=list,
        help_text="List of primary themes to weave throughout the story"
    )
    
    # Style Notes
    tone = models.CharField(
        max_length=100,
        blank=True,
        help_text="Overall tone (e.g., 'Dark and suspenseful', 'Light-hearted mystery')"
    )
    pov = models.CharField(
        max_length=50,
        default='Third Person Limited',
        help_text="Point of View (First Person, Third Person Limited, etc.)"
    )
    tense = models.CharField(
        max_length=20,
        default='Past',
        help_text="Narrative tense (Past, Present)"
    )
    
    # Summary for prompt injection
    summary_for_ai = models.TextField(
        blank=True,
        help_text="500-word summary optimized for AI prompt injection"
    )

    class Meta:
        verbose_name = "Story Bible"
        verbose_name_plural = "Story Bibles"

    def __str__(self):
        return f"Story Bible for: {self.book.title}"

    def generate_ai_summary(self):
        """
        Generate a condensed summary suitable for AI prompt injection.
        This should be called after the story bible is fully populated.
        """
        # This will be implemented to create a ~500 word summary
        # combining the most important elements for consistency
        pass


class ChapterStatus:
    """Chapter status choices."""
    PENDING = 'pending'
    PENDING_WRITE = 'ready_to_write'  # Alias for admin_views
    READY_TO_WRITE = 'ready_to_write'
    WRITING = 'writing'
    WRITTEN = 'written'
    PENDING_QA = 'pending_qa'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    PUBLISHED = 'published'
    
    CHOICES = [
        (PENDING, 'Pending Brief'),
        (READY_TO_WRITE, 'Ready to Write'),
        (WRITING, 'Writing in Progress'),
        (WRITTEN, 'Written'),
        (PENDING_QA, 'Pending QA'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected - Needs Rewrite'),
        (PUBLISHED, 'Published'),
    ]


class Chapter(BaseModel):
    """
    Individual chapter of a book.
    """
    book = models.ForeignKey(
        'novels.Book',
        on_delete=models.CASCADE,
        related_name='chapters'
    )
    chapter_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(300)]
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Chapter title (optional)"
    )
    
    # Brief/Outline
    brief = models.JSONField(
        default=dict,
        help_text="""
        Chapter brief for AI writing:
        {
            "opening_hook": "...",
            "key_events": ["...", "..."],
            "ending_hook": "...",
            "mood": "...",
            "pov_character": "...",
            "clues_to_plant": ["clue_001"],
            "clues_to_reveal": [],
            "characters_present": ["..."],
            "location": "..."
        }
        """
    )
    
    # Content
    content = models.TextField(
        blank=True,
        help_text="Full chapter content"
    )
    word_count = models.PositiveIntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ChapterStatus.CHOICES,
        default=ChapterStatus.PENDING,
        db_index=True
    )
    
    # Quality Metrics
    ai_detection_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    plagiarism_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # QA Notes
    qa_notes = models.TextField(
        blank=True,
        help_text="Notes from QA review (reasons for rejection, etc.)"
    )
    # Alias used in admin views
    @property
    def qa_feedback(self):
        return self.qa_notes

    @qa_feedback.setter
    def qa_feedback(self, value):
        self.qa_notes = value

    qa_reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Generation Metadata
    generation_prompt = models.TextField(
        blank=True,
        help_text="The full prompt used to generate this chapter"
    )
    generation_model = models.CharField(
        max_length=50,
        blank=True,
        help_text="AI model used (e.g., 'gemini-1.5-pro')"
    )
    generation_tokens_used = models.PositiveIntegerField(default=0)
    generation_cost_usd = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0
    )
    generation_attempts = models.PositiveIntegerField(default=0)
    
    # Publishing
    published_at = models.DateTimeField(null=True, blank=True)
    drip_scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled date for drip-feed publishing on website"
    )
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this chapter is publicly visible on the storefront"
    )
    is_free = models.BooleanField(
        default=False,
        help_text="Whether this chapter is free to read without purchase (e.g. Chapter 1 preview)"
    )

    class Meta:
        verbose_name = "Chapter"
        verbose_name_plural = "Chapters"
        ordering = ['book', 'chapter_number']
        unique_together = ['book', 'chapter_number']
        indexes = [
            models.Index(fields=['book', 'status']),
            models.Index(fields=['status', 'is_deleted']),
        ]

    def __str__(self):
        return f"{self.book.title} - Chapter {self.chapter_number}"

    def save(self, *args, **kwargs):
        # Auto-calculate word count
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)

    def mark_ready_to_write(self):
        """Mark chapter as ready for AI writing."""
        self.status = ChapterStatus.READY_TO_WRITE
        self.save(update_fields=['status', 'updated_at'])

    def mark_written(self, content, model, tokens, cost):
        """Mark chapter as written with metadata."""
        self.content = content
        self.status = ChapterStatus.PENDING_QA
        self.generation_model = model
        self.generation_tokens_used = tokens
        self.generation_cost_usd = cost
        self.generation_attempts += 1
        self.save()

    def approve(self):
        """Approve chapter after QA."""
        from django.utils import timezone
        self.status = ChapterStatus.APPROVED
        self.qa_reviewed_at = timezone.now()
        self.save(update_fields=['status', 'qa_reviewed_at', 'updated_at'])

    def reject(self, notes):
        """Reject chapter and mark for rewrite."""
        from django.utils import timezone
        self.status = ChapterStatus.REJECTED
        self.qa_notes = notes
        self.qa_reviewed_at = timezone.now()
        self.save(update_fields=['status', 'qa_notes', 'qa_reviewed_at', 'updated_at'])
