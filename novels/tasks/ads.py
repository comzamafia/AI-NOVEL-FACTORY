"""
Celery tasks for Amazon Ads management.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def sync_ads_performance():
    """
    Daily task to sync ads performance data from Amazon Advertising API.
    """
    from novels.models import Book, BookLifecycleStatus, AdsPerformance
    from novels.services.ads_service import AmazonAdsService
    from django.utils import timezone
    
    logger.info("Starting daily ads performance sync...")
    
    # Get published books
    books = Book.objects.filter(
        lifecycle_status__in=[
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL
        ],
        asin__isnull=False,
        is_deleted=False
    ).exclude(asin='')
    
    ads_service = AmazonAdsService()
    synced_count = 0
    
    for book in books:
        try:
            # Get performance data
            data = ads_service.get_campaign_performance(book.asin)
            
            # Create or update performance record
            AdsPerformance.objects.update_or_create(
                book=book,
                report_date=timezone.now().date(),
                defaults={
                    'impressions': data.get('impressions', 0),
                    'clicks': data.get('clicks', 0),
                    'spend_usd': data.get('spend', 0),
                    'sales_usd': data.get('sales', 0),
                    'orders': data.get('orders', 0),
                    'units_sold': data.get('units', 0),
                    'top_keywords': data.get('top_keywords', []),
                }
            )
            synced_count += 1
            
        except Exception as e:
            logger.error(f"Failed to sync ads for book {book.id}: {e}")
    
    logger.info(f"Synced ads performance for {synced_count} books")
    return {'synced_count': synced_count}


@shared_task
def optimize_ads_keywords():
    """
    Weekly task to optimize ads keywords based on performance.
    Runs every Monday at 08:00 AM.
    """
    from novels.models import Book, BookLifecycleStatus, AdsPerformance
    from novels.services.ads_service import AmazonAdsService
    from datetime import timedelta
    from django.utils import timezone
    
    logger.info("Starting weekly ads keyword optimization...")
    
    # Get recent ads performance
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    
    books = Book.objects.filter(
        lifecycle_status__in=[
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL
        ],
        asin__isnull=False,
        is_deleted=False
    ).exclude(asin='')
    
    ads_service = AmazonAdsService()
    
    for book in books:
        try:
            # Get recent performance records
            performances = AdsPerformance.objects.filter(
                book=book,
                report_date__gte=seven_days_ago
            )
            
            if not performances.exists():
                continue
            
            # Calculate aggregate metrics
            total_spend = sum(p.spend_usd for p in performances)
            total_sales = sum(p.sales_usd for p in performances)
            
            if total_sales > 0:
                overall_acos = (float(total_spend) / float(total_sales)) * 100
            else:
                overall_acos = 100  # No sales = 100% ACOS
            
            # Get keyword recommendations
            recommendations = ads_service.get_keyword_recommendations(
                book.asin,
                performances
            )
            
            # Update latest performance record with recommendations
            latest = performances.order_by('-report_date').first()
            if latest:
                latest.keywords_to_pause = recommendations.get('pause', [])
                latest.keywords_to_scale = recommendations.get('scale', [])
                latest.save()
            
            # Alert if ACOS too high
            if overall_acos > 50:
                logger.warning(f"High ACOS alert for book {book.id}: {overall_acos:.1f}%")
                # TODO: Send admin notification
            
        except Exception as e:
            logger.error(f"Failed to optimize ads for book {book.id}: {e}")
    
    logger.info("Completed weekly ads optimization")
