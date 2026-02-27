"""
Subscription and Payment models for the Storefront.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from .base import BaseModel


class SubscriptionPlan:
    """Subscription plan choices."""
    FREE = 'free'
    CHAPTER = 'chapter'
    MONTHLY = 'monthly'
    ANNUAL = 'annual'
    
    CHOICES = [
        (FREE, 'Free (Limited Access)'),
        (CHAPTER, 'Pay Per Chapter'),
        (MONTHLY, 'Monthly Subscription ($9.99/mo)'),
        (ANNUAL, 'Annual Subscription ($99.99/yr)'),
    ]


class SubscriptionStatus:
    """Subscription status choices."""
    ACTIVE = 'active'
    CANCELED = 'canceled'
    PAST_DUE = 'past_due'
    EXPIRED = 'expired'
    TRIALING = 'trialing'
    
    CHOICES = [
        (ACTIVE, 'Active'),
        (CANCELED, 'Canceled'),
        (PAST_DUE, 'Past Due'),
        (EXPIRED, 'Expired'),
        (TRIALING, 'Trial'),
    ]


class Subscription(BaseModel):
    """
    User subscription for the storefront.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    
    # Plan Details
    plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.CHOICES,
        default=SubscriptionPlan.FREE
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.CHOICES,
        default=SubscriptionStatus.ACTIVE
    )
    
    # Stripe Integration
    stripe_customer_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )
    stripe_subscription_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )
    
    # Billing Dates
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    # Trial
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Revenue Tracking
    total_spent_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return f"{self.user.username} - {self.get_plan_display()} ({self.status})"

    def is_premium(self):
        """Check if user has premium access."""
        return (
            self.plan in [SubscriptionPlan.MONTHLY, SubscriptionPlan.ANNUAL]
            and self.status == SubscriptionStatus.ACTIVE
        )


class ChapterPurchase(BaseModel):
    """
    Individual chapter purchase (pay-per-chapter).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chapter_purchases'
    )
    chapter = models.ForeignKey(
        'novels.Chapter',
        on_delete=models.PROTECT,
        related_name='purchases'
    )
    
    # Payment Details
    price_usd = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stripe_payment_intent_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )
    
    # Status
    is_refunded = models.BooleanField(default=False)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Chapter Purchase"
        verbose_name_plural = "Chapter Purchases"
        unique_together = ['user', 'chapter']

    def __str__(self):
        return f"{self.user.username} purchased {self.chapter}"


class WebhookEvent(BaseModel):
    """
    Log of Stripe webhook events for debugging and auditing.
    """
    stripe_event_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)

    class Meta:
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        ordering = ['-created_at']

    def __str__(self):
        status = "Processed" if self.processed else "Pending"
        return f"{self.event_type} ({status})"
