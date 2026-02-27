"""
Celery tasks for content generation.
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_daily_content_generation(self):
    """
    Daily task to generate content for chapters.
    Runs at 06:00 AM via Celery Beat.
    """
    from novels.models import Book, Chapter, BookLifecycleStatus, ChapterStatus
    
    logger.info("Starting daily content generation...")
    
    # Find books in writing phase
    books = Book.objects.filter(
        lifecycle_status=BookLifecycleStatus.WRITING_IN_PROGRESS,
        is_deleted=False
    )
    
    chapters_written = 0
    
    for book in books:
        # Find chapters ready to write
        chapters = Chapter.objects.filter(
            book=book,
            status=ChapterStatus.READY_TO_WRITE,
            is_deleted=False
        ).order_by('chapter_number')[:5]  # Max 5 per book per day
        
        for chapter in chapters:
            try:
                write_chapter.delay(chapter.id)
                chapters_written += 1
            except Exception as e:
                logger.error(f"Failed to queue chapter {chapter.id}: {e}")
    
    logger.info(f"Queued {chapters_written} chapters for writing")
    return {'chapters_queued': chapters_written}


@shared_task(bind=True, max_retries=3)
def write_chapter(self, chapter_id: int):
    """
    Generate content for a single chapter using AI.
    """
    from novels.models import Chapter, ChapterStatus
    from novels.services.ai_writer import AIWriterService
    
    try:
        chapter = Chapter.objects.select_related(
            'book',
            'book__pen_name',
            'book__story_bible'
        ).get(id=chapter_id)
        
        # Mark as writing
        chapter.status = ChapterStatus.WRITING
        chapter.save(update_fields=['status', 'updated_at'])
        
        # Get AI writer service
        writer = AIWriterService()
        
        # Generate content
        result = writer.write_chapter(chapter)
        
        # Update chapter
        chapter.mark_written(
            content=result['content'],
            model=result['model'],
            tokens=result['tokens_used'],
            cost=result['cost_usd']
        )
        
        logger.info(f"Successfully wrote chapter {chapter_id}")
        return {'chapter_id': chapter_id, 'status': 'success'}
        
    except Chapter.DoesNotExist:
        logger.error(f"Chapter {chapter_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error writing chapter {chapter_id}: {e}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def run_consistency_check(self, book_id: int):
    """
    Check consistency across chapters in a book.
    Triggered every 10 chapters that are written.
    """
    from novels.models import Book, Chapter
    from novels.services.ai_writer import AIWriterService
    
    logger.info(f"Running consistency check for book {book_id}")
    
    try:
        book = Book.objects.get(id=book_id)
        chapters = Chapter.objects.filter(
            book=book,
            status__in=['written', 'pending_qa'],
            is_deleted=False
        ).order_by('chapter_number')
        
        if chapters.count() < 10:
            logger.info("Less than 10 chapters, skipping consistency check")
            return {'status': 'skipped', 'reason': 'insufficient_chapters'}
        
        # Get AI service for consistency check
        writer = AIWriterService()
        issues = writer.check_consistency(book, chapters)
        
        if issues:
            # Flag issues in database
            logger.warning(f"Found {len(issues)} consistency issues in book {book_id}")
            # TODO: Store issues and notify admin
            return {'status': 'issues_found', 'count': len(issues)}
        else:
            logger.info(f"No consistency issues found in book {book_id}")
            return {'status': 'passed'}
            
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error in consistency check for book {book_id}: {e}")
        raise


@shared_task
def rewrite_chapter(chapter_id: int, feedback: str):
    """
    Rewrite a rejected chapter with the given feedback.
    """
    from novels.models import Chapter, ChapterStatus
    from novels.services.ai_writer import AIWriterService
    
    logger.info(f"Rewriting chapter {chapter_id} with feedback")
    
    try:
        chapter = Chapter.objects.select_related(
            'book',
            'book__pen_name',
            'book__story_bible'
        ).get(id=chapter_id)
        
        # Mark as writing
        chapter.status = ChapterStatus.WRITING
        chapter.save(update_fields=['status', 'updated_at'])
        
        # Get AI writer service
        writer = AIWriterService()
        
        # Rewrite with feedback
        result = writer.rewrite_chapter(chapter, feedback)
        
        # Update chapter
        chapter.mark_written(
            content=result['content'],
            model=result['model'],
            tokens=result['tokens_used'],
            cost=result['cost_usd']
        )
        
        logger.info(f"Successfully rewrote chapter {chapter_id}")
        return {'chapter_id': chapter_id, 'status': 'success'}
        
    except Chapter.DoesNotExist:
        logger.error(f"Chapter {chapter_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error rewriting chapter {chapter_id}: {e}")
        raise


# =============================================================================
# PHASE 3 — Concept Generation
# =============================================================================

@shared_task(bind=True, max_retries=2)
def generate_book_concepts(self, book_id: int):
    """
    Generate 3 book concepts using AI for admin to select from.
    Triggered from the admin Concept Selection page.
    """
    from novels.models import Book
    from novels.services.ai_writer import AIWriterService

    logger.info(f"Generating concepts for book {book_id}...")

    try:
        book = Book.objects.get(pk=book_id)
        writer = AIWriterService()

        concepts = writer.generate_book_concepts(book)

        book.book_concepts = concepts
        book.save(update_fields=['book_concepts', 'updated_at'])

        logger.info(f"Generated {len(concepts)} concepts for book {book_id}")
        return {'book_id': book_id, 'concepts_generated': len(concepts)}

    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Concept generation failed for book {book_id}: {e}")
        raise self.retry(exc=e, countdown=60)


# =============================================================================
# PHASE 4a — Story Bible Generation
# =============================================================================

@shared_task(bind=True, max_retries=2)
def generate_story_bible(self, book_id: int):
    """
    Generate a full story bible for a book using AI.
    Triggered after description approval.
    """
    from novels.models import Book, StoryBible, BookLifecycleStatus
    from novels.services.ai_writer import AIWriterService

    logger.info(f"Generating story bible for book {book_id}...")

    try:
        book = Book.objects.select_related('pen_name').get(pk=book_id)
        writer = AIWriterService()

        bible_data = writer.create_story_bible(book)

        # Upsert StoryBible model
        StoryBible.objects.update_or_create(
            book=book,
            defaults={
                'characters': bible_data.get('characters', {}),
                'world_rules': bible_data.get('world_rules', {}),
                'four_act_outline': bible_data.get('four_act_outline', {}),
                'timeline': bible_data.get('timeline', []),
                'thematic_elements': bible_data.get('thematic_elements', {}),
            },
        )

        logger.info(f"Story bible generated for book {book_id}")
        return {'book_id': book_id, 'status': 'success'}

    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Story bible generation failed for book {book_id}: {e}")
        raise self.retry(exc=e, countdown=60)


# =============================================================================
# PHASE 4b — Description Generation
# =============================================================================

@shared_task(bind=True, max_retries=2)
def generate_book_description(self, book_id: int):
    """
    Generate A/B book descriptions using AI.
    Triggered after keyword approval.
    """
    from novels.models import Book, BookDescription
    from novels.services.ai_writer import AIWriterService

    logger.info(f"Generating book descriptions for book {book_id}...")

    try:
        book = Book.objects.select_related('pen_name', 'keyword_research').get(pk=book_id)

        writer = AIWriterService()
        desc = writer.generate_book_description(book)

        # Save both versions
        BookDescription.objects.update_or_create(
            book=book, version='A',
            defaults={
                'description_html': desc.get('version_a', ''),
                'hook_line': desc.get('hook_a', ''),
                'is_active': True,
            }
        )
        BookDescription.objects.update_or_create(
            book=book, version='B',
            defaults={
                'description_html': desc.get('version_b', ''),
                'hook_line': desc.get('hook_b', ''),
                'is_active': False,
            }
        )

        logger.info(f"Generated A/B descriptions for book {book_id}")
        return {'book_id': book_id, 'status': 'success', 'versions': ['A', 'B']}

    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise
    except Exception as e:
        logger.error(f"Description generation failed for book {book_id}: {e}")
        raise self.retry(exc=e, countdown=60)
