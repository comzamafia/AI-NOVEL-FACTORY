"""
AI Novel Factory Celery Tasks Package.

All tasks are organized into separate modules by functionality.
"""

# Content generation tasks
from .content import (
    run_daily_content_generation,
    write_chapter,
    run_consistency_check,
    rewrite_chapter,
    generate_book_concepts,
    generate_book_description,
)

# Keyword research tasks
from .keywords import (
    run_keyword_research,
    sync_keyword_data,
    generate_kdp_metadata,
)

# Ads management tasks
from .ads import (
    sync_ads_performance,
    optimize_ads_keywords,
)

# Review tracking tasks
from .reviews import (
    scrape_amazon_reviews,
    analyze_review_sentiment,
    send_arc_emails,
)

# Pricing tasks
from .pricing import (
    auto_transition_pricing,
    schedule_kindle_countdown,
)

# Distribution tasks
from .distribution import (
    sync_platform_revenue,
    update_competitor_data,
    generate_market_opportunity_report,
)

# Legal tasks
from .legal import (
    check_content_theft,
    run_quality_check,
    generate_dmca_notice,
)

__all__ = [
    # Content
    'run_daily_content_generation',
    'write_chapter',
    'run_consistency_check',
    'rewrite_chapter',
    'generate_book_concepts',
    'generate_book_description',
    # Keywords
    'run_keyword_research',
    'sync_keyword_data',
    'generate_kdp_metadata',
    # Ads
    'sync_ads_performance',
    'optimize_ads_keywords',
    # Reviews
    'scrape_amazon_reviews',
    'analyze_review_sentiment',
    'send_arc_emails',
    # Pricing
    'auto_transition_pricing',
    'schedule_kindle_countdown',
    # Distribution
    'sync_platform_revenue',
    'update_competitor_data',
    'generate_market_opportunity_report',
    # Legal
    'check_content_theft',
    'run_quality_check',
    'generate_dmca_notice',
]
