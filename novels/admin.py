"""
Django Admin configuration for AI Novel Factory.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    PenName,
    Book,
    StoryBible,
    Chapter,
    KeywordResearch,
    BookDescription,
    PricingStrategy,
    AdsPerformance,
    ReviewTracker,
    ARCReader,
    DistributionChannel,
    CompetitorBook,
    StyleFingerprint,
    Subscription,
    ChapterPurchase,
    WebhookEvent,
)


# =============================================================================
# INLINE ADMIN CLASSES
# =============================================================================

class ChapterInline(admin.TabularInline):
    """Inline display of chapters in Book admin."""
    model = Chapter
    extra = 0
    fields = ['chapter_number', 'title', 'status', 'word_count', 'ai_detection_score']
    readonly_fields = ['word_count']
    ordering = ['chapter_number']
    show_change_link = True


class BookDescriptionInline(admin.TabularInline):
    """Inline display of book descriptions."""
    model = BookDescription
    extra = 0
    fields = ['version', 'is_active', 'is_approved', 'character_count']
    readonly_fields = ['character_count']
    show_change_link = True


class DistributionChannelInline(admin.TabularInline):
    """Inline display of distribution channels."""
    model = DistributionChannel
    extra = 0
    fields = ['platform', 'is_active', 'revenue_usd', 'units_sold']
    readonly_fields = ['revenue_usd', 'units_sold']


class AdsPerformanceInline(admin.TabularInline):
    """Inline display of recent ads performance."""
    model = AdsPerformance
    extra = 0
    max_num = 7
    fields = ['report_date', 'impressions', 'clicks', 'spend_usd', 'sales_usd', 'acos']
    readonly_fields = ['report_date', 'impressions', 'clicks', 'spend_usd', 'sales_usd', 'acos']
    ordering = ['-report_date']


# =============================================================================
# PEN NAME ADMIN
# =============================================================================

@admin.register(PenName)
class PenNameAdmin(admin.ModelAdmin):
    """Admin for Pen Names (Authors)."""
    list_display = [
        'name',
        'niche_genre',
        'total_books_published',
        'total_revenue_display',
        'has_style_fingerprint',
        'created_at',
    ]
    list_filter = ['niche_genre', 'created_at']
    search_fields = ['name', 'bio']
    readonly_fields = ['total_books_published', 'total_revenue_usd', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'niche_genre', 'bio', 'profile_image')
        }),
        ('Writing Style', {
            'fields': ('writing_style_prompt',),
            'classes': ('collapse',)
        }),
        ('Links', {
            'fields': ('website_url', 'amazon_author_url', 'twitter_handle', 'email_list_signup_url'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_books_published', 'total_revenue_usd'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Revenue')
    def total_revenue_display(self, obj):
        return f"${obj.total_revenue_usd:,.2f}"

    @admin.display(description='Style', boolean=True)
    def has_style_fingerprint(self, obj):
        return hasattr(obj, 'style_fingerprint')


# =============================================================================
# BOOK ADMIN
# =============================================================================

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin for Books with lifecycle management."""
    list_display = [
        'title',
        'pen_name',
        'lifecycle_status_display',
        'progress_bar',
        'chapter_stats',
        'quality_scores',
        'revenue_display',
        'created_at',
    ]
    list_filter = [
        'lifecycle_status',
        'pen_name',
        'is_ai_generated_disclosure',
        'kdp_preflight_passed',
        'created_at',
    ]
    search_fields = ['title', 'subtitle', 'synopsis', 'pen_name__name']
    readonly_fields = [
        'pipeline_actions',
        'current_word_count',
        'ai_detection_score',
        'plagiarism_score',
        'total_revenue_usd',
        'created_at',
        'updated_at',
        'published_at',
    ]
    inlines = [ChapterInline, BookDescriptionInline, DistributionChannelInline]

    fieldsets = (
        ('ðŸš€ Pipeline Actions', {
            'fields': ('pipeline_actions',),
            'description': 'Quick links to each stage of the production pipeline.',
        }),
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'pen_name', 'synopsis')
        }),
        ('Market Research', {
            'fields': ('target_audience', 'comparable_titles', 'hook', 'core_twist'),
            'classes': ('collapse',)
        }),
        ('Lifecycle', {
            'fields': ('lifecycle_status',)
        }),
        ('Publishing', {
            'fields': ('asin', 'bsr', 'published_at'),
            'classes': ('collapse',)
        }),
        ('Content Stats', {
            'fields': ('target_chapter_count', 'target_word_count', 'current_word_count'),
        }),
        ('Quality', {
            'fields': ('ai_detection_score', 'plagiarism_score'),
            'classes': ('collapse',)
        }),
        ('KDP Compliance', {
            'fields': ('is_ai_generated_disclosure', 'kdp_preflight_passed', 'copyright_registered'),
        }),
        ('Revenue', {
            'fields': ('total_revenue_usd',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Pipeline Actions')
    def pipeline_actions(self, obj):
        if not obj.pk:
            return 'â€” Save book first to access pipeline actions â€”'

        btn = lambda url, label, color='#417690': (
            f'<a href="{url}" style="display:inline-block; background:{color}; color:#fff; '
            f'padding:6px 12px; border-radius:3px; text-decoration:none; font-size:12px; '
            f'margin:3px;">{label}</a>'
        )

        buttons = [
            btn(reverse('concept_selection', args=[obj.pk]), '💡 Concepts'),
            btn(reverse('keyword_research', args=[obj.pk]), '🔍 Keywords'),
            btn(reverse('description_editor', args=[obj.pk]), '📝 Description'),
            btn(reverse('story_bible', args=[obj.pk]), '📖 Story Bible'),
            btn(reverse('qa_review', args=[obj.pk]), '🛡️ QA Review', '#fd7e14'),
            btn(reverse('kdp_preflight', args=[obj.pk]), '✈️ Pre-Flight', '#6f42c1'),
            btn(reverse('export_book', args=[obj.pk]), '📦 Export', '#28a745'),
            btn(reverse('ads_dashboard', args=[obj.pk]), '📣 Ads', '#e74c3c'),
            btn(reverse('pricing_strategy', args=[obj.pk]), '💰 Pricing', '#20c997'),
            btn(reverse('review_arc', args=[obj.pk]), '⭐ Reviews', '#007bff'),
            btn(reverse('distribution_tracker', args=[obj.pk]), '🌐 Distribution', '#17a2b8'),
            btn(reverse('legal_protection', args=[obj.pk]), '🔐 Legal', '#6c757d'),
        ]
        return format_html(''.join(buttons))

    @admin.display(description='Status')
    def lifecycle_status_display(self, obj):
        status_colors = {
            'concept_pending': '#ffc107',
            'keyword_research': '#17a2b8',
            'keyword_approved': '#28a745',
            'description_generation': '#17a2b8',
            'description_approved': '#28a745',
            'bible_generation': '#17a2b8',
            'bible_approved': '#28a745',
            'writing_in_progress': '#007bff',
            'qa_review': '#fd7e14',
            'export_ready': '#6f42c1',
            'published_kdp': '#28a745',
            'published_all': '#20c997',
            'archived': '#6c757d',
        }
        color = status_colors.get(obj.lifecycle_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_lifecycle_status_display()
        )

    @admin.display(description='Progress')
    def progress_bar(self, obj):
        progress = obj.get_progress_percentage()
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}px; background-color: #007bff; height: 20px; '
            'border-radius: 3px; text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}%</div></div>',
            progress,
            progress
        )

    @admin.display(description='Chapters')
    def chapter_stats(self, obj):
        total = obj.target_chapter_count
        completed = obj.chapters.filter(status='approved').count()
        return f"{completed}/{total}"

    @admin.display(description='Quality')
    def quality_scores(self, obj):
        ai = obj.ai_detection_score or '-'
        plag = obj.plagiarism_score or '-'
        return f"AI: {ai}% | Plag: {plag}%"

    @admin.display(description='Revenue')
    def revenue_display(self, obj):
        return f"${obj.total_revenue_usd:,.2f}"


# =============================================================================
# STORY BIBLE & CHAPTER ADMIN
# =============================================================================

@admin.register(StoryBible)
class StoryBibleAdmin(admin.ModelAdmin):
    """Admin for Story Bibles."""
    list_display = ['book', 'tone', 'pov', 'tense', 'created_at']
    list_filter = ['pov', 'tense']
    search_fields = ['book__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """Admin for Chapters."""
    list_display = [
        'chapter_display',
        'book',
        'status_display',
        'word_count',
        'quality_scores',
        'generation_cost_usd',
        'updated_at',
    ]
    list_filter = ['status', 'book__pen_name', 'book']
    search_fields = ['book__title', 'title', 'content']
    readonly_fields = [
        'word_count',
        'ai_detection_score',
        'plagiarism_score',
        'generation_tokens_used',
        'generation_cost_usd',
        'generation_attempts',
        'qa_reviewed_at',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Chapter Info', {
            'fields': ('book', 'chapter_number', 'title', 'status')
        }),
        ('Brief', {
            'fields': ('brief',),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('content', 'word_count'),
        }),
        ('Quality', {
            'fields': ('ai_detection_score', 'plagiarism_score'),
        }),
        ('QA', {
            'fields': ('qa_notes', 'qa_reviewed_at'),
            'classes': ('collapse',)
        }),
        ('Generation Metadata', {
            'fields': (
                'generation_prompt',
                'generation_model',
                'generation_tokens_used',
                'generation_cost_usd',
                'generation_attempts',
            ),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('published_at', 'drip_scheduled_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Chapter')
    def chapter_display(self, obj):
        return f"Ch. {obj.chapter_number}"

    @admin.display(description='Status')
    def status_display(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'ready_to_write': '#17a2b8',
            'writing': '#007bff',
            'written': '#28a745',
            'pending_qa': '#fd7e14',
            'approved': '#20c997',
            'rejected': '#dc3545',
            'published': '#6f42c1',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Quality')
    def quality_scores(self, obj):
        ai = f"{obj.ai_detection_score:.1f}" if obj.ai_detection_score else '-'
        plag = f"{obj.plagiarism_score:.1f}" if obj.plagiarism_score else '-'
        return f"AI: {ai}% | Plag: {plag}%"


# =============================================================================
# KEYWORD & DESCRIPTION ADMIN
# =============================================================================

@admin.register(KeywordResearch)
class KeywordResearchAdmin(admin.ModelAdmin):
    """Admin for Keyword Research."""
    list_display = [
        'book',
        'suggested_title_short',
        'categories',
        'is_approved',
        'last_research_at',
    ]
    list_filter = ['is_approved', 'data_source']
    search_fields = ['book__title', 'suggested_title', 'kdp_category_1', 'kdp_category_2']
    readonly_fields = ['approved_at', 'last_research_at', 'created_at', 'updated_at']

    @admin.display(description='Suggested Title')
    def suggested_title_short(self, obj):
        if obj.suggested_title:
            return obj.suggested_title[:50] + '...' if len(obj.suggested_title) > 50 else obj.suggested_title
        return '-'

    @admin.display(description='Categories')
    def categories(self, obj):
        cat1 = obj.kdp_category_1[:30] + '...' if len(obj.kdp_category_1) > 30 else obj.kdp_category_1
        return cat1 or '-'


@admin.register(BookDescription)
class BookDescriptionAdmin(admin.ModelAdmin):
    """Admin for Book Descriptions."""
    list_display = [
        'book',
        'version',
        'is_active',
        'is_approved',
        'character_count',
        'updated_at',
    ]
    list_filter = ['version', 'is_active', 'is_approved']
    search_fields = ['book__title', 'hook_line', 'description_plain']
    readonly_fields = ['character_count', 'description_plain', 'approved_at', 'created_at', 'updated_at']


# =============================================================================
# MARKETING ADMIN
# =============================================================================

@admin.register(PricingStrategy)
class PricingStrategyAdmin(admin.ModelAdmin):
    """Admin for Pricing Strategy."""
    list_display = [
        'book',
        'current_phase',
        'price_display',
        'is_kdp_select',
        'auto_price_enabled',
        'next_promotion_date',
    ]
    list_filter = ['current_phase', 'is_kdp_select', 'auto_price_enabled']
    search_fields = ['book__title']
    readonly_fields = ['price_history', 'created_at', 'updated_at']

    @admin.display(description='Price')
    def price_display(self, obj):
        return f"${obj.current_price_usd}"


@admin.register(AdsPerformance)
class AdsPerformanceAdmin(admin.ModelAdmin):
    """Admin for Ads Performance."""
    list_display = [
        'book',
        'report_date',
        'impressions',
        'clicks',
        'spend_display',
        'sales_display',
        'acos_display',
    ]
    list_filter = ['report_date', 'book']
    search_fields = ['book__title']
    date_hierarchy = 'report_date'
    readonly_fields = ['acos', 'ctr', 'cpc', 'created_at', 'updated_at']

    @admin.display(description='Spend')
    def spend_display(self, obj):
        return f"${obj.spend_usd}"

    @admin.display(description='Sales')
    def sales_display(self, obj):
        return f"${obj.sales_usd}"

    @admin.display(description='ACOS')
    def acos_display(self, obj):
        if obj.acos is not None:
            color = '#28a745' if obj.acos < 30 else '#ffc107' if obj.acos < 50 else '#dc3545'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color,
                obj.acos
            )
        return '-'


@admin.register(ReviewTracker)
class ReviewTrackerAdmin(admin.ModelAdmin):
    """Admin for Review Tracker."""
    list_display = [
        'book',
        'total_reviews',
        'rating_display',
        'arc_stats',
        'last_scraped',
    ]
    list_filter = ['avg_rating']
    search_fields = ['book__title']
    readonly_fields = [
        'arc_conversion_rate',
        'last_scraped',
        'created_at',
        'updated_at',
    ]

    @admin.display(description='Rating')
    def rating_display(self, obj):
        stars = 'â˜…' * int(obj.avg_rating) + 'â˜†' * (5 - int(obj.avg_rating))
        return f"{stars} ({obj.avg_rating:.1f})"

    @admin.display(description='ARC Stats')
    def arc_stats(self, obj):
        return f"Sent: {obj.arc_emails_sent} | Reviews: {obj.arc_reviews_received}"


@admin.register(ARCReader)
class ARCReaderAdmin(admin.ModelAdmin):
    """Admin for ARC Readers."""
    list_display = [
        'name',
        'email',
        'reviews_left_count',
        'arc_copies_received',
        'avg_rating_given',
        'reliability_display',
    ]
    list_filter = ['is_reliable', 'email_opt_out']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Reliable', boolean=True)
    def reliability_display(self, obj):
        return obj.is_reliable


# =============================================================================
# DISTRIBUTION & INTELLIGENCE ADMIN
# =============================================================================

@admin.register(DistributionChannel)
class DistributionChannelAdmin(admin.ModelAdmin):
    """Admin for Distribution Channels."""
    list_display = [
        'book',
        'platform',
        'is_active',
        'revenue_display',
        'units_sold',
        'published_at',
    ]
    list_filter = ['platform', 'is_active']
    search_fields = ['book__title', 'asin_or_id']

    @admin.display(description='Revenue')
    def revenue_display(self, obj):
        return f"${obj.revenue_usd:,.2f}"


@admin.register(CompetitorBook)
class CompetitorBookAdmin(admin.ModelAdmin):
    """Admin for Competitor Books."""
    list_display = [
        'title_short',
        'author',
        'genre',
        'bsr',
        'review_count',
        'rating_display',
        'price_usd',
        'estimated_monthly_revenue',
    ]
    list_filter = ['genre', 'subgenre']
    search_fields = ['title', 'author', 'asin']
    ordering = ['bsr']

    @admin.display(description='Title')
    def title_short(self, obj):
        return obj.title[:40] + '...' if len(obj.title) > 40 else obj.title

    @admin.display(description='Rating')
    def rating_display(self, obj):
        return f"{obj.avg_rating:.1f}â˜…"


@admin.register(StyleFingerprint)
class StyleFingerprintAdmin(admin.ModelAdmin):
    """Admin for Style Fingerprints."""
    list_display = [
        'pen_name',
        'avg_sentence_length',
        'dialogue_ratio_display',
        'chapters_analyzed',
        'last_recalculated',
    ]
    search_fields = ['pen_name__name']
    readonly_fields = ['chapters_analyzed', 'last_recalculated', 'created_at', 'updated_at']

    @admin.display(description='Dialogue %')
    def dialogue_ratio_display(self, obj):
        return f"{obj.dialogue_ratio * 100:.0f}%"


# =============================================================================
# SUBSCRIPTION ADMIN
# =============================================================================

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin for Subscriptions."""
    list_display = [
        'user',
        'plan',
        'status',
        'total_spent_display',
        'current_period_end',
    ]
    list_filter = ['plan', 'status']
    search_fields = ['user__username', 'user__email', 'stripe_customer_id']
    readonly_fields = ['total_spent_usd', 'created_at', 'updated_at']

    @admin.display(description='Total Spent')
    def total_spent_display(self, obj):
        return f"${obj.total_spent_usd:,.2f}"


@admin.register(ChapterPurchase)
class ChapterPurchaseAdmin(admin.ModelAdmin):
    """Admin for Chapter Purchases."""
    list_display = [
        'user',
        'chapter',
        'price_usd',
        'is_refunded',
        'created_at',
    ]
    list_filter = ['is_refunded', 'created_at']
    search_fields = ['user__username', 'chapter__book__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Admin for Webhook Events."""
    list_display = [
        'stripe_event_id',
        'event_type',
        'processed',
        'created_at',
    ]
    list_filter = ['event_type', 'processed']
    search_fields = ['stripe_event_id']
    readonly_fields = ['stripe_event_id', 'event_type', 'payload', 'created_at', 'updated_at']


# =============================================================================
# ADMIN SITE CUSTOMIZATION
# =============================================================================

admin.site.site_header = "AI Novel Factory Admin"
admin.site.site_title = "AI Novel Factory"
admin.site.index_title = "Publishing Dashboard"

