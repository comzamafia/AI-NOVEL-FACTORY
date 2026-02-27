"""
Celery tasks for keyword research and SEO.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_keyword_research(self, book_id: int):
    """
    Run keyword research for a book.
    Triggered when a book concept is approved.
    """
    from novels.models import Book, KeywordResearch
    from novels.services.keyword_service import AmazonKeywordService
    
    logger.info(f"Starting keyword research for book {book_id}")
    
    try:
        book = Book.objects.get(id=book_id)
        
        # Get or create keyword research record
        keyword_research, created = KeywordResearch.objects.get_or_create(
            book=book
        )
        
        # Initialize keyword service
        keyword_service = AmazonKeywordService()
        
        # Run research
        result = keyword_service.research_keywords(book)
        
        # Update keyword research record
        keyword_research.primary_keywords = result.get('primary_keywords', [])
        keyword_research.kdp_backend_keywords = result.get('backend_keywords', [])
        keyword_research.kdp_category_1 = result.get('category_1', '')
        keyword_research.kdp_category_2 = result.get('category_2', '')
        keyword_research.suggested_title = result.get('suggested_title', '')
        keyword_research.suggested_subtitle = result.get('suggested_subtitle', '')
        keyword_research.competitor_asins = result.get('competitors', [])
        keyword_research.keyword_search_volume = result.get('search_volumes', {})
        keyword_research.last_research_at = __import__('django.utils.timezone', fromlist=['timezone']).timezone.now()
        keyword_research.save()
        
        logger.info(f"Completed keyword research for book {book_id}")
        return {'book_id': book_id, 'status': 'success'}
        
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error in keyword research for book {book_id}: {e}")
        self.retry(exc=e, countdown=300)


@shared_task
def sync_keyword_data():
    """
    Daily task to refresh keyword data for active books.
    """
    from novels.models import Book, BookLifecycleStatus
    
    logger.info("Starting daily keyword data sync...")
    
    # Find books that are published but might need keyword updates
    books = Book.objects.filter(
        lifecycle_status__in=[
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL
        ],
        is_deleted=False
    )
    
    for book in books[:10]:  # Limit to avoid API rate limits
        try:
            # Only refresh if needed
            if hasattr(book, 'keyword_research'):
                run_keyword_research.delay(book.id)
        except Exception as e:
            logger.error(f"Failed to queue keyword sync for book {book.id}: {e}")
    
    logger.info("Keyword data sync queued")


@shared_task(bind=True, max_retries=3)
def generate_kdp_metadata(self, book_id: int):
    """
    Generate KDP-optimized metadata using AI.
    """
    from novels.models import Book, KeywordResearch
    from novels.services.keyword_service import AmazonKeywordService
    
    logger.info(f"Generating KDP metadata for book {book_id}")
    
    try:
        book = Book.objects.get(id=book_id)
        keyword_research = book.keyword_research
        
        service = AmazonKeywordService()
        
        # Generate optimized metadata
        metadata = service.generate_optimized_metadata(book, keyword_research)
        
        # Update suggested fields
        keyword_research.suggested_title = metadata.get('title', '')
        keyword_research.suggested_subtitle = metadata.get('subtitle', '')
        keyword_research.kdp_backend_keywords = metadata.get('backend_keywords', [])
        keyword_research.kdp_category_1 = metadata.get('category_1', '')
        keyword_research.kdp_category_2 = metadata.get('category_2', '')
        keyword_research.save()
        
        logger.info(f"Generated KDP metadata for book {book_id}")
        return {'book_id': book_id, 'status': 'success'}
        
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error generating KDP metadata for book {book_id}: {e}")
        self.retry(exc=e, countdown=120)
