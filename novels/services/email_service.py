"""
Email Service - Email notifications and ARC reader management.
"""

import logging
from typing import Optional
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails to ARC readers and notifications."""
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def send_arc_invitation(
        self,
        reader_email: str,
        reader_name: str,
        book_title: str,
        book_description: str,
        download_link: str,
        review_deadline: str,
    ) -> bool:
        """
        Send ARC invitation email to a reader.
        
        Args:
            reader_email: Reader's email address
            reader_name: Reader's name
            book_title: Title of the book
            book_description: Brief description
            download_link: Link to download the ARC
            review_deadline: Deadline for review
            
        Returns:
            True if sent successfully
        """
        logger.info(f"Sending ARC invitation to {reader_email}...")
        
        subject = f"ARC Invitation: {book_title}"
        
        context = {
            'reader_name': reader_name,
            'book_title': book_title,
            'book_description': book_description,
            'download_link': download_link,
            'review_deadline': review_deadline,
        }
        
        try:
            # Try to use template if available
            html_content = render_to_string('emails/arc_invitation.html', context)
            text_content = render_to_string('emails/arc_invitation.txt', context)
        except Exception:
            # Fallback to inline template
            text_content = f"""
Hi {reader_name},

You've been invited to read an Advance Review Copy of "{book_title}"!

{book_description}

Download your copy here: {download_link}

Please submit your honest review by {review_deadline}.

Thank you for being a valued reviewer!

Best,
The Author
            """.strip()
            html_content = text_content.replace('\n', '<br>')
        
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[reader_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info(f"ARC invitation sent to {reader_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send ARC invitation: {e}")
            return False
    
    def send_review_reminder(
        self,
        reader_email: str,
        reader_name: str,
        book_title: str,
        review_deadline: str,
        amazon_link: str,
    ) -> bool:
        """
        Send review reminder to ARC reader.
        
        Returns:
            True if sent successfully
        """
        logger.info(f"Sending review reminder to {reader_email}...")
        
        subject = f"Reminder: Review for {book_title}"
        
        text_content = f"""
Hi {reader_name},

This is a friendly reminder that your review for "{book_title}" is due by {review_deadline}.

Please leave your honest review on Amazon: {amazon_link}

Thank you for your support!

Best wishes
        """.strip()
        
        try:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=self.from_email,
                recipient_list=[reader_email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send review reminder: {e}")
            return False
    
    def send_launch_notification(
        self,
        recipient_list: list[str],
        book_title: str,
        amazon_link: str,
        promo_price: str = None,
    ) -> int:
        """
        Send launch notification to subscriber list.
        
        Returns:
            Number of emails sent successfully
        """
        logger.info(f"Sending launch notification to {len(recipient_list)} recipients...")
        
        subject = f"Now Available: {book_title}"
        
        promo_text = f" - On sale for {promo_price}!" if promo_price else ""
        
        text_content = f"""
Great news! "{book_title}" is now available{promo_text}

Get your copy: {amazon_link}

Don't miss out on this new release!
        """.strip()
        
        sent_count = 0
        for email in recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=self.from_email,
                    recipient_list=[email],
                    fail_silently=True,
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to {email}: {e}")
        
        logger.info(f"Sent launch notification to {sent_count}/{len(recipient_list)} recipients")
        return sent_count
    
    def send_dmca_notice(
        self,
        to_email: str,
        infringing_url: str,
        original_title: str,
        dmca_content: str,
    ) -> bool:
        """
        Send DMCA takedown notice.
        
        Returns:
            True if sent successfully
        """
        logger.info(f"Sending DMCA notice to {to_email}...")
        
        subject = f"DMCA Takedown Notice - {original_title}"
        
        try:
            send_mail(
                subject=subject,
                message=dmca_content,
                from_email=self.from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send DMCA notice: {e}")
            return False
