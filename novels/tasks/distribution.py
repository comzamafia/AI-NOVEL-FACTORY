"""
Celery tasks for multi-platform distribution and competitor tracking.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def sync_platform_revenue():
    """
    Weekly task to sync revenue data from all distribution platforms.
    """
    from novels.models import Book, BookLifecycleStatus, DistributionChannel
    from novels.services.distribution_service import DistributionService
    from django.utils import timezone
    
    logger.info("Starting weekly platform revenue sync...")
    
    # Get all active distribution channels
    channels = DistributionChannel.objects.filter(
        is_active=True,
        book__is_deleted=False
    ).select_related('book')
    
    distribution_service = DistributionService()
    synced_count = 0
    
    for channel in channels:
        try:
            # Get revenue data from platform
            data = distribution_service.get_platform_data(
                channel.platform,
                channel.asin_or_id
            )
            
            if data:
                channel.units_sold = data.get('units_sold', channel.units_sold)
                channel.pages_read = data.get('pages_read', channel.pages_read)
                channel.revenue_usd = data.get('revenue', channel.revenue_usd)
                channel.last_synced_at = timezone.now()
                channel.sync_error = ''
                channel.save()
                synced_count += 1
            
        except Exception as e:
            logger.error(f"Failed to sync channel {channel.id}: {e}")
            channel.sync_error = str(e)
            channel.save(update_fields=['sync_error', 'updated_at'])
    
    # Update total revenue on books
    books_updated = set()
    for channel in channels:
        if channel.book_id not in books_updated:
            try:
                # Calculate total revenue across all channels
                from django.db.models import Sum
                total = DistributionChannel.objects.filter(
                    book=channel.book,
                    is_active=True
                ).aggregate(total=Sum('revenue_usd'))['total'] or 0
                
                channel.book.total_revenue_usd = total
                channel.book.save(update_fields=['total_revenue_usd', 'updated_at'])
                books_updated.add(channel.book_id)
            except Exception as e:
                logger.error(f"Failed to update total revenue for book {channel.book_id}: {e}")
    
    logger.info(f"Synced {synced_count} distribution channels")
    return {'synced_count': synced_count, 'books_updated': len(books_updated)}


@shared_task
def update_competitor_data():
    """
    Weekly task to update competitor book data.
    """
    from novels.models import CompetitorBook
    from novels.services.scraper_service import ScraperService
    from django.utils import timezone
    
    logger.info("Starting weekly competitor data update...")
    
    competitors = CompetitorBook.objects.filter(is_deleted=False)
    scraper = ScraperService()
    updated_count = 0
    
    for competitor in competitors[:100]:  # Limit to avoid rate limits
        try:
            data = scraper.scrape_amazon_product(competitor.asin)
            
            if data:
                # Store old BSR for history
                if competitor.bsr:
                    competitor.bsr_history.append({
                        'date': timezone.now().date().isoformat(),
                        'bsr': competitor.bsr
                    })
                    # Keep only last 90 days
                    competitor.bsr_history = competitor.bsr_history[-90:]
                
                # Update fields
                competitor.bsr = data.get('bsr', competitor.bsr)
                competitor.review_count = data.get('review_count', competitor.review_count)
                competitor.avg_rating = data.get('avg_rating', competitor.avg_rating)
                competitor.price_usd = data.get('price', competitor.price_usd)
                competitor.save()
                
                # Estimate revenue
                competitor.estimate_revenue()
                
                updated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to update competitor {competitor.asin}: {e}")
    
    logger.info(f"Updated {updated_count} competitor records")
    return {'updated_count': updated_count}


@shared_task
def generate_market_opportunity_report():
    """
    Weekly task to generate market opportunity report.
    """
    from novels.models import CompetitorBook
    from novels.services.ai_writer import AIWriterService
    
    logger.info("Generating market opportunity report...")
    
    try:
        # Get competitor data
        competitors = CompetitorBook.objects.filter(is_deleted=False).order_by('bsr')[:50]
        
        ai_service = AIWriterService()
        
        # Analyze market gaps
        report = ai_service.generate_market_report(competitors)
        
        # TODO: Store report or send to admin
        logger.info("Market opportunity report generated")
        return {'status': 'success', 'report_generated': True}
        
    except Exception as e:
        logger.error(f"Failed to generate market report: {e}")
        raise


@shared_task
def recalculate_style_fingerprint(pen_name_id: int):
    """
    Phase 14 — Recalculate style fingerprint metrics from approved chapters.
    Triggered every 10 new approved chapters per pen name.
    """
    from novels.models import PenName, StyleFingerprint, Chapter, ChapterStatus
    import re

    logger.info(f"Recalculating style fingerprint for pen name {pen_name_id}")

    try:
        pen_name = PenName.objects.get(id=pen_name_id)
        fingerprint, _ = StyleFingerprint.objects.get_or_create(pen_name=pen_name)

        # Get all approved chapters for this pen name
        chapters = Chapter.objects.filter(
            book__pen_name=pen_name,
            status=ChapterStatus.APPROVED,
            is_deleted=False,
        ).values_list('content', flat=True)[:100]

        if not chapters:
            logger.warning(f"No approved chapters for pen name {pen_name_id}")
            return {'pen_name_id': pen_name_id, 'status': 'no_chapters'}

        all_text = ' '.join(c for c in chapters if c)

        # Sentence & paragraph metrics
        sentences = re.split(r'(?<=[.!?])\s+', all_text)
        paragraphs = [p for p in all_text.split('\n\n') if p.strip()]
        words = all_text.split()

        avg_sent_len = round(len(words) / max(len(sentences), 1), 1)
        avg_para_len = round(len(sentences) / max(len(paragraphs), 1), 1)

        # Dialogue ratio: count lines with quotes
        dialogue_lines = len(re.findall(r'[""].*?[""]', all_text))
        total_sentences = max(len(sentences), 1)
        dialogue_ratio = round(dialogue_lines / total_sentences, 3)

        # Adverb frequency: words ending in 'ly'
        adverbs = len(re.findall(r'\b\w+ly\b', all_text, re.IGNORECASE))
        adverb_freq = round(adverbs / max(len(words), 1), 4)

        # Passive voice ratio: look for 'was/were/been + past participle'
        passive = len(re.findall(r'\b(?:was|were|been|be|is|are)\s+\w+ed\b', all_text, re.IGNORECASE))
        passive_ratio = round(passive / total_sentences, 3)

        # Common word patterns (top 20 bigrams excluding stopwords)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'he', 'she', 'it', 'they', 'was', 'had', 'her', 'his', 'i', 'you', 'we'}
        word_list = [w.lower().strip('.,!?;:"') for w in words if w.lower() not in stop_words and len(w) > 3]
        bigrams = [(word_list[i], word_list[i+1]) for i in range(len(word_list)-1)]
        from collections import Counter
        top_bigrams = [f"{a} {b}" for (a, b), _ in Counter(bigrams).most_common(20)]

        # Auto-generate style prompt
        style_prompt = (
            f"Write in the style of {pen_name.name}. "
            f"Use sentences of approximately {avg_sent_len} words. "
            f"Keep dialogue at about {int(dialogue_ratio * 100)}% of the content. "
            f"Minimize adverbs (target under {max(int(adverb_freq * 100 * 2), 3)}%). "
            f"Use active voice predominantly (passive voice under {max(int(passive_ratio * 100), 5)}%). "
            f"Common phrase patterns to emulate: {', '.join(top_bigrams[:5])}."
        )

        from django.utils import timezone
        fingerprint.avg_sentence_length = avg_sent_len
        fingerprint.avg_paragraph_length = avg_para_len
        fingerprint.dialogue_ratio = dialogue_ratio
        fingerprint.adverb_frequency = adverb_freq
        fingerprint.passive_voice_ratio = passive_ratio
        fingerprint.common_word_patterns = top_bigrams
        fingerprint.style_system_prompt = style_prompt
        fingerprint.last_recalculated = timezone.now()
        fingerprint.save()

        logger.info(f"Style fingerprint recalculated for pen name {pen_name_id}")
        return {'pen_name_id': pen_name_id, 'avg_sentence_length': avg_sent_len, 'status': 'success'}

    except PenName.DoesNotExist:
        logger.error(f"PenName {pen_name_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error recalculating style fingerprint for pen name {pen_name_id}: {e}")
        raise
