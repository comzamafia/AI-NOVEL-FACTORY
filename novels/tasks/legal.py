"""
Celery tasks for legal protection and copyright monitoring.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def check_content_theft(book_id: int = None):
    """
    Monthly task to check for content theft using Copyscape.
    Optionally scope to a single book.
    """
    from novels.models import Book, BookLifecycleStatus

    logger.info("Starting monthly content theft check...")

    if book_id:
        books = Book.objects.filter(id=book_id, is_deleted=False)
    else:
        books = Book.objects.filter(
            lifecycle_status__in=[
                BookLifecycleStatus.PUBLISHED_KDP,
                BookLifecycleStatus.PUBLISHED_ALL,
            ],
            is_deleted=False,
        )

    theft_found = 0
    for book in books:
        try:
            first_chapter = book.chapters.filter(is_deleted=False).order_by('chapter_number').first()
            if not first_chapter or not first_chapter.content:
                continue
            # TODO: Integrate Copyscape inbound scan API
            logger.info(f"Checked book {book.id} for content theft (stub)")
        except Exception as e:
            logger.error(f"Error checking content theft for book {book.id}: {e}")

    logger.info(f"Content theft check complete, {theft_found} potential cases found")
    return {'books_checked': books.count(), 'theft_found': theft_found}


@shared_task
def setup_google_alerts(book_id: int):
    """
    Set up Google Alerts for a book title and unique phrases.
    """
    from novels.models import Book

    try:
        book = Book.objects.select_related('pen_name').get(id=book_id)
        # TODO: Integrate Google Alerts API or generate alert URLs
        # For now, log the alert terms that should be monitored
        alert_terms = [book.title]
        if book.subtitle:
            alert_terms.append(book.subtitle)
        if book.pen_name:
            alert_terms.append(f'"{book.pen_name.name}" author')

        logger.info(f"Google Alerts setup requested for book {book_id}: {alert_terms}")
        # TODO: Automate Google Alerts creation via browser automation or API
        return {'book_id': book_id, 'alert_terms': alert_terms, 'status': 'logged'}

    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise


@shared_task
def run_quality_check(chapter_id: int):
    """
    Run AI detection and plagiarism check on a chapter.
    """
    from novels.models import Chapter
    from novels.services.quality_service import QualityCheckService
    
    logger.info(f"Running quality check on chapter {chapter_id}")
    
    try:
        chapter = Chapter.objects.get(id=chapter_id)
        quality_service = QualityCheckService()
        
        # Run AI detection
        ai_result = quality_service.check_ai_detection(chapter.content)
        chapter.ai_detection_score = ai_result.get('score', 0)
        
        # Run plagiarism check
        plag_result = quality_service.check_plagiarism(chapter.content)
        chapter.plagiarism_score = plag_result.get('score', 0)
        
        chapter.save(update_fields=['ai_detection_score', 'plagiarism_score', 'updated_at'])
        
        # Check thresholds
        if chapter.ai_detection_score > 20:
            logger.warning(f"High AI detection score for chapter {chapter_id}: {chapter.ai_detection_score}%")
            # TODO: Send alert
        
        if chapter.plagiarism_score > 3:
            logger.warning(f"High plagiarism score for chapter {chapter_id}: {chapter.plagiarism_score}%")
            # TODO: Send alert
        
        logger.info(f"Quality check complete for chapter {chapter_id}")
        return {
            'chapter_id': chapter_id,
            'ai_score': chapter.ai_detection_score,
            'plagiarism_score': chapter.plagiarism_score
        }
        
    except Chapter.DoesNotExist:
        logger.error(f"Chapter {chapter_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error in quality check for chapter {chapter_id}: {e}")
        raise


@shared_task
def generate_dmca_notice(book_id: int, infringing_url: str):
    """
    Generate a DMCA takedown notice for a book.
    """
    from novels.models import Book
    
    logger.info(f"Generating DMCA notice for book {book_id}")
    
    try:
        book = Book.objects.select_related('pen_name').get(id=book_id)
        
        notice_template = f"""
DMCA TAKEDOWN NOTICE

Date: {{date}}

To Whom It May Concern:

I am writing to you to request the removal of copyrighted material 
that is being infringed upon at the URL listed below.

COPYRIGHTED WORK:
Title: {book.title}
Author: {book.pen_name.name}
ASIN: {book.asin}
Original Publication: Amazon Kindle Direct Publishing

INFRINGING URL:
{infringing_url}

I have a good faith belief that the use of the copyrighted material 
is not authorized by the copyright owner, its agent, or the law.

This information is accurate, and under penalty of perjury, I am 
authorized to act on behalf of the copyright owner.

Signed:
{book.pen_name.name}
        """
        
        # TODO: Store notice and send to admin
        logger.info(f"DMCA notice generated for book {book_id}")
        return {'book_id': book_id, 'notice_generated': True}
        
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error generating DMCA notice for book {book_id}: {e}")
        raise
