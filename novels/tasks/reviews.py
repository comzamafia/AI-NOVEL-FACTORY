"""
Celery tasks for review tracking and ARC management.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def scrape_amazon_reviews():
    """
    Daily task to scrape Amazon reviews for all published books.
    """
    from novels.models import Book, BookLifecycleStatus, ReviewTracker
    from novels.services.scraper_service import ScraperService
    from django.utils import timezone
    
    logger.info("Starting daily Amazon review scraping...")
    
    books = Book.objects.filter(
        lifecycle_status__in=[
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL
        ],
        asin__isnull=False,
        is_deleted=False
    ).exclude(asin='')
    
    scraper = ScraperService()
    scraped_count = 0
    
    for book in books:
        try:
            # Get or create review tracker
            tracker, created = ReviewTracker.objects.get_or_create(book=book)
            
            # Scrape reviews
            data = scraper.scrape_amazon_reviews(book.asin)
            
            # Update tracker
            tracker.total_reviews = data.get('total_reviews', tracker.total_reviews)
            tracker.avg_rating = data.get('avg_rating', tracker.avg_rating)
            tracker.rating_distribution = data.get('rating_distribution', {})
            tracker.last_scraped = timezone.now()
            tracker.save()
            
            # Update book BSR if available
            if 'bsr' in data:
                book.bsr = data['bsr']
                book.save(update_fields=['bsr', 'updated_at'])
            
            # Check for alerts
            if tracker.avg_rating < 3.5:
                logger.warning(f"Low rating alert for book {book.id}: {tracker.avg_rating}")
                # TODO: Send admin notification
            
            scraped_count += 1
            
        except Exception as e:
            logger.error(f"Failed to scrape reviews for book {book.id}: {e}")
            tracker.scrape_error = str(e)
            tracker.save(update_fields=['scrape_error', 'updated_at'])
    
    logger.info(f"Scraped reviews for {scraped_count} books")
    return {'scraped_count': scraped_count}


@shared_task
def analyze_review_sentiment(book_id: int):
    """
    Analyze sentiment of recent reviews for a book.
    """
    from novels.models import Book, ReviewTracker
    from novels.services.ai_writer import AIWriterService
    
    logger.info(f"Analyzing review sentiment for book {book_id}")
    
    try:
        book = Book.objects.get(id=book_id)
        tracker = book.review_tracker
        
        ai_service = AIWriterService()
        
        # Analyze sentiment
        analysis = ai_service.analyze_review_sentiment(book)
        
        tracker.positive_themes = analysis.get('positive_themes', [])
        tracker.negative_themes = analysis.get('negative_themes', [])
        tracker.save()
        
        logger.info(f"Completed sentiment analysis for book {book_id}")
        return {'book_id': book_id, 'status': 'success'}
        
    except Exception as e:
        logger.error(f"Error analyzing reviews for book {book_id}: {e}")
        raise


@shared_task
def send_arc_emails(book_id: int):
    """
    Send ARC copies to readers before book launch.
    """
    from novels.models import Book, ARCReader, ReviewTracker
    from novels.services.email_service import EmailService
    
    logger.info(f"Sending ARC emails for book {book_id}")
    
    try:
        book = Book.objects.select_related('pen_name').get(id=book_id)
        
        # Get eligible ARC readers
        readers = ARCReader.objects.filter(
            is_reliable=True,
            email_opt_out=False,
            is_deleted=False
        )
        
        # Filter by genre interest
        genre_readers = [
            r for r in readers
            if book.pen_name.niche_genre in r.genres_interested
        ]
        
        email_service = EmailService()
        sent_count = 0
        
        for reader in genre_readers[:50]:  # Limit batch size
            try:
                email_service.send_arc_email(reader, book)
                reader.arc_copies_received += 1
                reader.save(update_fields=['arc_copies_received', 'updated_at'])
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send ARC email to {reader.email}: {e}")
        
        # Update review tracker
        tracker, _ = ReviewTracker.objects.get_or_create(book=book)
        tracker.arc_emails_sent += sent_count
        tracker.save(update_fields=['arc_emails_sent', 'updated_at'])
        
        logger.info(f"Sent {sent_count} ARC emails for book {book_id}")
        return {'book_id': book_id, 'emails_sent': sent_count}
        
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error sending ARC emails for book {book_id}: {e}")
        raise
