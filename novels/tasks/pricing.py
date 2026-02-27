"""
Celery tasks for pricing management.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def auto_transition_pricing():
    """
    Daily task to check and transition book pricing based on rules.
    """
    from novels.models import Book, BookLifecycleStatus, PricingStrategy, PricingPhase
    from datetime import timedelta
    from django.utils import timezone
    from decimal import Decimal
    
    logger.info("Starting daily pricing transition check...")
    
    # Get books with pricing strategies
    strategies = PricingStrategy.objects.filter(
        auto_price_enabled=True,
        book__lifecycle_status__in=[
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL
        ],
        book__is_deleted=False
    ).select_related('book', 'book__review_tracker')
    
    transitions = 0
    
    for strategy in strategies:
        try:
            book = strategy.book
            days_since_publish = (timezone.now() - book.published_at).days if book.published_at else 0
            
            # Get review count
            review_count = 0
            if hasattr(book, 'review_tracker'):
                review_count = book.review_tracker.total_reviews
            
            old_phase = strategy.current_phase
            old_price = strategy.current_price_usd
            new_phase = old_phase
            new_price = old_price
            reason = None
            
            # Check transition conditions
            if strategy.current_phase == PricingPhase.LAUNCH:
                # Transition from Launch to Growth
                if days_since_publish >= strategy.days_in_launch_phase:
                    if review_count >= strategy.reviews_threshold_for_growth:
                        new_phase = PricingPhase.GROWTH
                        new_price = Decimal('2.99')
                        reason = f"Launch phase complete ({days_since_publish} days, {review_count} reviews)"
            
            elif strategy.current_phase == PricingPhase.GROWTH:
                # Transition from Growth to Mature
                if days_since_publish >= 30 and review_count >= 50:
                    new_phase = PricingPhase.MATURE
                    new_price = Decimal('3.99')
                    reason = f"Growth complete ({review_count} reviews, {days_since_publish} days)"
            
            elif strategy.current_phase == PricingPhase.PROMO:
                # Check if promo should end
                if strategy.last_promotion_date:
                    days_in_promo = (timezone.now().date() - strategy.last_promotion_date).days
                    if days_in_promo >= 7:
                        new_phase = PricingPhase.MATURE
                        new_price = Decimal('3.99')
                        reason = "Promotional period ended"
            
            # Apply transition if changed
            if new_phase != old_phase or new_price != old_price:
                strategy.current_phase = new_phase
                strategy.current_price_usd = new_price
                strategy.log_price_change(new_price, new_phase, reason)
                strategy.save()
                
                logger.info(f"Transitioned book {book.id} from {old_phase} to {new_phase}")
                transitions += 1
                
                # TODO: Update price on KDP via API
                # TODO: Send admin notification
        
        except Exception as e:
            logger.error(f"Error processing pricing for book {strategy.book_id}: {e}")
    
    logger.info(f"Completed pricing check, {transitions} transitions made")
    return {'transitions': transitions}


@shared_task
def schedule_kindle_countdown():
    """
    Check and schedule Kindle Countdown deals for eligible books.
    Runs periodically to check 90-day intervals.
    """
    from novels.models import PricingStrategy, PricingPhase, PromotionType
    from datetime import timedelta
    from django.utils import timezone
    
    logger.info("Checking for Kindle Countdown scheduling...")
    
    # Get eligible books (KDP Select, mature phase)
    strategies = PricingStrategy.objects.filter(
        is_kdp_select=True,
        current_phase=PricingPhase.MATURE,
        auto_price_enabled=True,
        book__is_deleted=False
    )
    
    scheduled = 0
    today = timezone.now().date()
    
    for strategy in strategies:
        try:
            # Check if enough time since last promotion
            if strategy.last_promotion_date:
                days_since_promo = (today - strategy.last_promotion_date).days
                if days_since_promo < strategy.days_between_promotions:
                    continue
            
            # Schedule new promotion
            promo_date = today + timedelta(days=7)  # Schedule for next week
            
            strategy.next_promotion_date = promo_date
            strategy.next_promotion_type = PromotionType.KINDLE_COUNTDOWN
            strategy.save(update_fields=['next_promotion_date', 'next_promotion_type', 'updated_at'])
            
            scheduled += 1
            logger.info(f"Scheduled Kindle Countdown for book {strategy.book_id} on {promo_date}")
            
            # TODO: Send notification to subscribers
            
        except Exception as e:
            logger.error(f"Error scheduling promotion for book {strategy.book_id}: {e}")
    
    logger.info(f"Scheduled {scheduled} Kindle Countdown deals")
    return {'scheduled': scheduled}
