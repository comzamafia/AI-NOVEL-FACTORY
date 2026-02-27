"""
Custom Admin Views for the AI Novel Factory System.
Handles Phase 2â€“7 custom pages outside standard Django Admin.
"""

import json
import logging
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

from novels.models import (
    Book, BookLifecycleStatus, KeywordResearch, BookDescription,
    Chapter, ChapterStatus, StoryBible, ARCReader, ReviewTracker,
    AdsPerformance, PricingStrategy, DistributionChannel, DistributionPlatform,
    CompetitorBook, StyleFingerprint,
)
from novels.forms import (
    KeywordApprovalForm, ConceptSelectionForm, DescriptionApprovalForm,
    StoryBibleApprovalForm, QAReviewForm, KDPPreFlightForm, AdsOptimizationForm,
)

logger = logging.getLogger(__name__)


def get_admin_context(request, title, breadcrumbs=None):
    """Build common admin context dict."""
    ctx = {
        **admin.site.each_context(request),
        'title': title,
        'has_permission': request.user.is_staff,
    }
    if breadcrumbs:
        ctx['breadcrumbs'] = breadcrumbs
    return ctx


# =============================================================================
# PHASE 2 â€” Keyword Research & Approval
# =============================================================================

@staff_member_required
def keyword_research_view(request, book_id):
    """
    Phase 2.3 â€” Keyword Approval Page.
    GET:  Show current keyword data + form for editing.
    POST: Save edits and optionally approve â†’ lifecycle transition.
    """
    book = get_object_or_404(Book, pk=book_id)
    keyword_obj, _ = KeywordResearch.objects.get_or_create(book=book)

    # Build initial data from existing keyword record
    backend_kws = keyword_obj.kdp_backend_keywords or []
    initial = {
        'suggested_title': keyword_obj.suggested_title or book.title,
        'suggested_subtitle': keyword_obj.suggested_subtitle or '',
        'kdp_category_1': keyword_obj.kdp_category_1 or '',
        'kdp_category_2': keyword_obj.kdp_category_2 or '',
    }
    for i, kw in enumerate(backend_kws[:7], 1):
        initial[f'kdp_keyword_{i}'] = kw

    if request.method == 'POST':
        form = KeywordApprovalForm(request.POST, initial=initial)
        action = request.POST.get('action', 'save')
        form.data = form.data.copy()
        form.data['action'] = action

        if form.is_valid():
            # Save edits to DB
            keyword_obj.suggested_title = form.cleaned_data['suggested_title']
            keyword_obj.suggested_subtitle = form.cleaned_data.get('suggested_subtitle', '')
            keyword_obj.kdp_backend_keywords = form.get_backend_keywords()
            keyword_obj.kdp_category_1 = form.cleaned_data.get('kdp_category_1', '')
            keyword_obj.kdp_category_2 = form.cleaned_data.get('kdp_category_2', '')
            keyword_obj.save()

            if action == 'approve':
                # Trigger lifecycle transition
                if book.lifecycle_status == BookLifecycleStatus.KEYWORD_RESEARCH:
                    try:
                        book.approve_keywords()
                        book.save()
                        messages.success(request, f'âœ… Keywords approved! Book "{book.title}" moved to keyword_approved state.')
                        # Trigger description generation task
                        try:
                            from novels.tasks.keywords import generate_kdp_metadata
                            generate_kdp_metadata.delay(book_id)
                        except Exception:
                            pass
                    except Exception as e:
                        messages.error(request, f'Lifecycle transition failed: {e}')
                else:
                    messages.warning(
                        request,
                        f'Book is in "{book.lifecycle_status}" state â€” cannot approve keywords from this state.',
                    )
                return redirect(reverse('admin:novels_book_change', args=[book_id]))
            else:
                messages.success(request, 'Keyword data saved.')
                return redirect(reverse('keyword_research', args=[book_id]))
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = KeywordApprovalForm(initial=initial)

    # Build competitor context
    competitor_asins = keyword_obj.competitor_asins or []
    primary_keywords = keyword_obj.primary_keywords or []

    ctx = get_admin_context(request, f'Keyword Research â€” {book.title}')
    ctx.update({
        'book': book,
        'keyword_obj': keyword_obj,
        'form': form,
        'competitor_asins': competitor_asins,
        'primary_keywords': primary_keywords,
        'can_approve': book.lifecycle_status == BookLifecycleStatus.KEYWORD_RESEARCH,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/keyword_research.html', ctx)


# =============================================================================
# PHASE 3 â€” Idea & Concept Selection
# =============================================================================

@staff_member_required
def concept_selection_view(request, book_id):
    """
    Phase 3 â€” Concept selection dashboard.
    Shows AI-generated concepts and lets admin choose one.
    """
    book = get_object_or_404(Book, pk=book_id)
    concepts = book.book_concepts or []  # JSON field on Book

    if request.method == 'POST':
        form = ConceptSelectionForm(request.POST, concepts=concepts)
        if form.is_valid():
            idx = int(form.cleaned_data['selected_concept'])
            chosen = concepts[idx] if idx < len(concepts) else {}

            # Override with admin edits
            if form.cleaned_data.get('custom_title'):
                chosen['title'] = form.cleaned_data['custom_title']
            if form.cleaned_data.get('custom_hook'):
                chosen['hook'] = form.cleaned_data['custom_hook']

            # Save approved concept to book
            book.title = chosen.get('title', book.title)
            book.synopsis = chosen.get('hook', book.synopsis)
            book.approved_concept = chosen
            book.save()

            # Transition lifecycle and trigger keyword research
            if book.lifecycle_status == BookLifecycleStatus.CONCEPT_PENDING:
                try:
                    book.start_keyword_research()
                    book.save()
                    from novels.tasks.keywords import run_keyword_research
                    run_keyword_research.delay(book_id)
                    messages.success(
                        request,
                        f'âœ… Concept approved! Keyword research started for "{book.title}".',
                    )
                except Exception as e:
                    messages.error(request, f'Lifecycle error: {e}')
            return redirect(reverse('admin:novels_book_change', args=[book_id]))
    else:
        form = ConceptSelectionForm(concepts=concepts)

    ctx = get_admin_context(request, f'Concept Selection â€” {book.title}')
    ctx.update({
        'book': book,
        'concepts': concepts,
        'form': form,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/concept_selection.html', ctx)


@staff_member_required
def generate_concepts_view(request, book_id):
    """Trigger AI concept generation (AJAX)."""
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        try:
            from novels.tasks.content import generate_book_concepts
            task = generate_book_concepts.delay(book_id)
            return JsonResponse({'status': 'started', 'task_id': task.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)


# =============================================================================
# PHASE 4 â€” Book Description Editor
# =============================================================================

@staff_member_required
def description_editor_view(request, book_id):
    """
    Phase 4.2 â€” Book Description Editor with A/B preview.
    """
    book = get_object_or_404(Book, pk=book_id)
    # Get latest A/B descriptions or create blanks
    desc_a = BookDescription.objects.filter(book=book, version='A').order_by('-created_at').first()
    desc_b = BookDescription.objects.filter(book=book, version='B').order_by('-created_at').first()

    initial = {
        'description_html_a': desc_a.description_html if desc_a else '',
        'description_html_b': desc_b.description_html if desc_b else '',
        'active_version': 'A' if (not desc_b or (desc_a and desc_a.is_active)) else 'B',
        'hook_line': desc_a.hook_line if desc_a else '',
    }

    if request.method == 'POST':
        action = request.POST.get('form_action', 'save')
        form = DescriptionApprovalForm(request.POST, initial=initial)
        if form.is_valid():
            cd = form.cleaned_data
            active_version = cd['active_version']

            # Save/update description A
            if cd.get('description_html_a'):
                BookDescription.objects.update_or_create(
                    book=book, version='A',
                    defaults={
                        'description_html': cd['description_html_a'],
                        'hook_line': cd.get('hook_line', ''),
                        'is_active': (active_version == 'A'),
                    }
                )

            # Save/update description B
            if cd.get('description_html_b'):
                BookDescription.objects.update_or_create(
                    book=book, version='B',
                    defaults={
                        'description_html': cd['description_html_b'],
                        'is_active': (active_version == 'B'),
                    }
                )

            if action == 'approve':
                messages.success(request, f'âœ… Description Version {active_version} approved and set as active.')
                return redirect(reverse('admin:novels_book_change', args=[book_id]))
            else:
                messages.success(request, 'Descriptions saved.')
                return redirect(reverse('description_editor', args=[book_id]))
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = DescriptionApprovalForm(initial=initial)

    ctx = get_admin_context(request, f'Description Editor â€” {book.title}')
    ctx.update({
        'book': book,
        'form': form,
        'desc_a': desc_a,
        'desc_b': desc_b,
        'opts': Book._meta,
        'amazon_max': 4000,
    })
    return render(request, 'admin/novels/description_editor.html', ctx)


@staff_member_required
def generate_description_view(request, book_id):
    """Trigger AI description generation (AJAX)."""
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        try:
            from novels.tasks.content import generate_book_description
            task = generate_book_description.delay(book_id)
            return JsonResponse({'status': 'started', 'task_id': task.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)


# =============================================================================
# PHASE 5 â€” Story Architecture Review
# =============================================================================

@staff_member_required
def story_bible_view(request, book_id):
    """
    Phase 5 â€” Story Bible + Chapter Briefs review page.
    """
    book = get_object_or_404(Book, pk=book_id)
    bible, _ = StoryBible.objects.get_or_create(book=book)

    initial = {
        'world_building': bible.world_rules or '',
        'main_characters': json.dumps(bible.characters, indent=2) if bible.characters else '',
        'timeline': bible.timeline or '',
        'four_act_outline': bible.four_act_outline or '',
        'clue_tracker': '',
        'notes': '',
    }

    if request.method == 'POST':
        action = request.POST.get('form_action', 'save')
        form = StoryBibleApprovalForm(request.POST, initial=initial)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                bible.characters = json.loads(cd['main_characters'])
            except (json.JSONDecodeError, ValueError):
                bible.characters = {'raw': cd['main_characters']}

            bible.world_rules = cd['world_building']
            bible.timeline = cd['timeline']
            bible.four_act_outline = cd['four_act_outline']
            bible.save()

            if action == 'approve':
                # Transition to writing
                if book.lifecycle_status in [
                    BookLifecycleStatus.BIBLE_GENERATION,
                    BookLifecycleStatus.KEYWORD_APPROVED,
                ]:
                    try:
                        book.start_writing()
                        book.save()
                        messages.success(
                            request,
                            f'âœ… Story Bible approved! Writing pipeline activated for "{book.title}".',
                        )
                    except Exception as e:
                        messages.error(request, f'Lifecycle transition failed: {e}')
                return redirect(reverse('admin:novels_book_change', args=[book_id]))
            else:
                messages.success(request, 'Story Bible saved.')
        else:
            messages.error(request, 'Fix errors below.')
    else:
        form = StoryBibleApprovalForm(initial=initial)

    chapters = Chapter.objects.filter(book=book).order_by('chapter_number')[:30]

    ctx = get_admin_context(request, f'Story Bible â€” {book.title}')
    ctx.update({
        'book': book,
        'bible': bible,
        'form': form,
        'chapters': chapters,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/story_bible.html', ctx)


# =============================================================================
# PHASE 7 â€” QA Review Gate
# =============================================================================

@staff_member_required
def qa_review_view(request, book_id):
    """
    Phase 7.1 â€” QA Gate UI: review first chapter, twist chapters, and ending.
    """
    book = get_object_or_404(Book, pk=book_id)
    # Get key chapters: first, every 10th, and last
    first_ch = Chapter.objects.filter(book=book, chapter_number=1).first()
    last_ch = Chapter.objects.filter(book=book).order_by('-chapter_number').first()
    twist_chs = Chapter.objects.filter(
        book=book,
        chapter_number__in=[10, 20, 30, 40, 50, 60, 70],
    ).order_by('chapter_number')

    # QA stats from DB
    total_ch = Chapter.objects.filter(book=book).count()
    approved_ch = Chapter.objects.filter(book=book, status=ChapterStatus.APPROVED).count()

    if request.method == 'POST':
        form = QAReviewForm(request.POST)
        chapter_id = request.POST.get('chapter_id')
        if form.is_valid():
            decision = form.cleaned_data['decision']
            feedback = form.cleaned_data.get('feedback', '')

            if chapter_id:
                chapter = get_object_or_404(Chapter, pk=chapter_id, book=book)
                if decision == 'approve':
                    chapter.status = ChapterStatus.APPROVED
                    chapter.save()
                    messages.success(request, f'Chapter {chapter.chapter_number} approved.')
                elif decision == 'reject':
                    chapter.status = ChapterStatus.PENDING_WRITE
                    chapter.qa_feedback = feedback
                    chapter.save()
                    # Trigger AI rewrite
                    try:
                        from novels.tasks.content import rewrite_chapter
                        rewrite_chapter.delay(chapter.id, feedback)
                        messages.warning(
                            request,
                            f'Chapter {chapter.chapter_number} rejected â€” AI rewrite queued with feedback.',
                        )
                    except Exception as e:
                        messages.error(request, f'Rewrite task failed: {e}')
            return redirect(reverse('qa_review', args=[book_id]))
        else:
            messages.error(request, 'Fix errors.')
    else:
        form = QAReviewForm()

    ctx = get_admin_context(request, f'QA Review â€” {book.title}')
    ctx.update({
        'book': book,
        'first_ch': first_ch,
        'last_ch': last_ch,
        'twist_chs': twist_chs,
        'form': form,
        'total_ch': total_ch,
        'approved_ch': approved_ch,
        'completion_pct': round(approved_ch / total_ch * 100, 1) if total_ch else 0,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/qa_review.html', ctx)


# =============================================================================
# PHASE 7.4 â€” KDP Pre-Flight Checklist & Export
# =============================================================================

@staff_member_required
def kdp_preflight_view(request, book_id):
    """
    Phase 7.4 â€” KDP Pre-Flight checklist + Export unlock.
    """
    book = get_object_or_404(Book, pk=book_id)

    # Auto-fill known scores from DB
    qa_scores = {
        'originality_ai_score': None,
        'plagiarism_score': None,
    }
    approved_chapters = Chapter.objects.filter(book=book, status=ChapterStatus.APPROVED)
    if approved_chapters.exists():
        ch = approved_chapters.first()
        qa_scores['originality_ai_score'] = getattr(ch, 'ai_detection_score', None)
        qa_scores['plagiarism_score'] = getattr(ch, 'plagiarism_score', None)

    if request.method == 'POST':
        form = KDPPreFlightForm(request.POST)
        if form.is_valid():
            # Mark book as export ready
            try:
                if book.lifecycle_status in [
                    BookLifecycleStatus.QA_REVIEW,
                    BookLifecycleStatus.WRITING_IN_PROGRESS,
                ]:
                    book.approve_qa()
                    book.save()

                messages.success(
                    request,
                    'âœ… KDP Pre-Flight passed! Book is cleared for export. Click Export below.',
                )
                return redirect(reverse('export_book', args=[book_id]))
            except Exception as e:
                messages.error(request, f'Error: {e}')
        else:
            messages.error(request, 'Pre-flight checklist incomplete. Fix all issues before exporting.')
    else:
        form = KDPPreFlightForm(initial=qa_scores)

    ctx = get_admin_context(request, f'KDP Pre-Flight Checklist â€” {book.title}')
    ctx.update({
        'book': book,
        'form': form,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/kdp_preflight.html', ctx)


# =============================================================================
# PHASE 7.5 â€” Document Export
# =============================================================================

@staff_member_required
def export_book_view(request, book_id):
    """
    Phase 7.5 â€” Document Export: triggers .docx and .epub generation.
    """
    book = get_object_or_404(Book, pk=book_id)

    if request.method == 'POST':
        export_format = request.POST.get('export_format', 'both')
        try:
            from novels.exporters import BookExporter
            exporter = BookExporter(book)

            if export_format in ('docx', 'both'):
                docx_path = exporter.export_docx()
                messages.success(request, f'âœ… DOCX exported: {docx_path}')

            if export_format in ('epub', 'both'):
                epub_path = exporter.export_epub()
                messages.success(request, f'âœ… EPUB exported: {epub_path}')

            # Transition lifecycle state
            if book.lifecycle_status == BookLifecycleStatus.EXPORT_READY:
                book.publish_kdp()
                book.save()
                messages.info(request, 'Book lifecycle moved to published_kdp.')

        except ImportError as e:
            messages.error(request, f'Export library missing: {e}. Install python-docx and ebooklib.')
        except Exception as e:
            messages.error(request, f'Export failed: {e}')
            logger.exception(f'Export failed for book {book_id}')

        return redirect(reverse('admin:novels_book_change', args=[book_id]))

    ctx = get_admin_context(request, f'Export Book â€” {book.title}')
    ctx.update({
        'book': book,
        'opts': Book._meta,
        'chapters_count': Chapter.objects.filter(book=book, status=ChapterStatus.APPROVED).count(),
    })
    return render(request, 'admin/novels/export_book.html', ctx)


# =============================================================================
# PHASE 10 â€” Ads Dashboard
# =============================================================================

@staff_member_required
def ads_dashboard_view(request, book_id):
    """
    Phase 10.3 â€” Ads performance dashboard.
    """
    book = get_object_or_404(Book, pk=book_id)

    # Last 30 days of performance data
    from datetime import timedelta
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    perf_data = AdsPerformance.objects.filter(
        book=book,
        report_date__gte=thirty_days_ago,
    ).order_by('report_date')

    # Compute totals
    totals = {
        'impressions': sum(p.impressions for p in perf_data),
        'clicks': sum(p.clicks for p in perf_data),
        'spend': sum(p.spend_usd for p in perf_data),
        'sales': sum(p.sales_usd for p in perf_data),
    }
    totals['acos'] = round(
        float(totals['spend']) / float(totals['sales']) * 100, 2
    ) if totals['sales'] else None

    if request.method == 'POST':
        form = AdsOptimizationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                from novels.tasks.ads import optimize_ads_keywords
                optimize_ads_keywords.apply_async(
                    kwargs={
                        'book_id': book_id,
                        'target_acos': float(cd['target_acos']),
                    }
                )
                messages.success(request, f'âœ… Ads optimization queued with target ACoS {cd["target_acos"]}%.')
            except Exception as e:
                messages.error(request, f'Optimization task error: {e}')
    else:
        form = AdsOptimizationForm()

    # Chart data (JSON for JS)
    chart_labels = [str(p.report_date) for p in perf_data]
    chart_spend = [float(p.spend_usd) for p in perf_data]
    chart_sales = [float(p.sales_usd) for p in perf_data]
    chart_acos = []
    for p in perf_data:
        if p.spend_usd and p.sales_usd and p.sales_usd > 0:
            chart_acos.append(round(float(p.spend_usd) / float(p.sales_usd) * 100, 2))
        else:
            chart_acos.append(None)

    ctx = get_admin_context(request, f'Ads Dashboard â€” {book.title}')
    ctx.update({
        'book': book,
        'perf_data': perf_data,
        'totals': totals,
        'form': form,
        'chart_labels': json.dumps(chart_labels),
        'chart_spend': json.dumps(chart_spend),
        'chart_sales': json.dumps(chart_sales),
        'chart_acos': json.dumps(chart_acos),
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/ads_dashboard.html', ctx)


# =============================================================================
# PHASE 8 — Dynamic Pricing Strategy
# =============================================================================

@staff_member_required
def pricing_strategy_view(request, book_id):
    """Phase 8 — Dynamic Pricing management for a book."""
    book = get_object_or_404(Book, pk=book_id)
    strategy, created = PricingStrategy.objects.get_or_create(
        book=book,
        defaults={'current_price_usd': '0.99', 'current_phase': 'launch'},
    )

    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        # Manual phase override
        new_phase = request.POST.get('current_phase', strategy.current_phase)
        new_price = request.POST.get('current_price_usd', str(strategy.current_price_usd))
        auto_enabled = request.POST.get('auto_price_enabled') == 'on'
        reviews_threshold = int(request.POST.get('reviews_threshold_for_growth', strategy.reviews_threshold_for_growth))
        days_launch = int(request.POST.get('days_in_launch_phase', strategy.days_in_launch_phase))

        try:
            from decimal import Decimal
            strategy.current_phase = new_phase
            strategy.current_price_usd = Decimal(new_price)
            strategy.auto_price_enabled = auto_enabled
            strategy.reviews_threshold_for_growth = reviews_threshold
            strategy.days_in_launch_phase = days_launch
            strategy.save()

            if action == 'trigger_auto':
                from novels.tasks.pricing import auto_transition_pricing
                auto_transition_pricing.delay()
                messages.success(request, '✅ Auto-pricing task queued. Price transitions will be evaluated.')
            elif action == 'schedule_promo':
                from novels.tasks.pricing import schedule_kindle_countdown
                schedule_kindle_countdown.delay()
                messages.success(request, '✅ Kindle Countdown scheduling task queued.')
            else:
                messages.success(request, f'Pricing strategy saved: ${strategy.current_price_usd} ({strategy.current_phase})')
        except Exception as e:
            messages.error(request, f'Error: {e}')

        return redirect(reverse('pricing_strategy', args=[book_id]))

    # Build price history chart data
    history = strategy.price_history or []
    chart_dates = [h.get('date', '')[:10] for h in history]
    chart_prices = [h.get('price', 0) for h in history]

    ctx = get_admin_context(request, f'Pricing Strategy — {book.title}')
    ctx.update({
        'book': book,
        'strategy': strategy,
        'history': history,
        'chart_dates': json.dumps(chart_dates),
        'chart_prices': json.dumps(chart_prices),
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/pricing_strategy.html', ctx)


# =============================================================================
# PHASE 11 — Review Velocity & ARC Management
# =============================================================================

@staff_member_required
def review_arc_view(request, book_id):
    """Phase 11 — Review tracker + ARC campaign dashboard."""
    book = get_object_or_404(Book, pk=book_id)
    tracker, _ = ReviewTracker.objects.get_or_create(book=book)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'scrape':
            try:
                from novels.tasks.reviews import scrape_amazon_reviews
                scrape_amazon_reviews.delay()
                messages.success(request, '✅ Amazon review scraping task queued.')
            except Exception as e:
                messages.error(request, f'Task error: {e}')
        elif action == 'send_arc':
            try:
                from novels.tasks.reviews import send_arc_emails
                send_arc_emails.delay(book_id)
                messages.success(request, f'✅ ARC email campaign queued for "{book.title}".')
            except Exception as e:
                messages.error(request, f'Task error: {e}')
        elif action == 'update_manual':
            tracker.total_reviews = int(request.POST.get('total_reviews', tracker.total_reviews))
            tracker.avg_rating = float(request.POST.get('avg_rating', tracker.avg_rating))
            tracker.reviews_week_1 = int(request.POST.get('reviews_week_1', tracker.reviews_week_1))
            tracker.reviews_week_2 = int(request.POST.get('reviews_week_2', tracker.reviews_week_2))
            tracker.reviews_week_3 = int(request.POST.get('reviews_week_3', tracker.reviews_week_3))
            tracker.reviews_week_4 = int(request.POST.get('reviews_week_4', tracker.reviews_week_4))
            tracker.save()
            messages.success(request, 'Review data updated manually.')
        return redirect(reverse('review_arc', args=[book_id]))

    arc_readers = ARCReader.objects.filter(is_reliable=True).count()
    velocity_data = [tracker.reviews_week_1, tracker.reviews_week_2,
                     tracker.reviews_week_3, tracker.reviews_week_4]

    ctx = get_admin_context(request, f'Review & ARC — {book.title}')
    ctx.update({
        'book': book,
        'tracker': tracker,
        'arc_readers': arc_readers,
        'velocity_data': json.dumps(velocity_data),
        'low_rating_alert': tracker.avg_rating < 3.5 and tracker.total_reviews > 0,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/review_arc.html', ctx)


@staff_member_required
def arc_reader_list_view(request):
    """Phase 11 — ARC reader database management."""
    readers = ARCReader.objects.all().order_by('-reviews_left_count')
    genre_filter = request.GET.get('genre', '')
    reliable_filter = request.GET.get('reliable', '')

    if genre_filter:
        readers = [r for r in readers if genre_filter.lower() in
                   [g.lower() for g in (r.genres_interested or [])]]
    if reliable_filter == '1':
        readers = ARCReader.objects.filter(is_reliable=True).order_by('-reviews_left_count')
    elif reliable_filter == '0':
        readers = ARCReader.objects.filter(is_reliable=False).order_by('-reviews_left_count')

    ctx = get_admin_context(request, 'ARC Reader Database')
    ctx.update({
        'readers': readers,
        'total': ARCReader.objects.count(),
        'reliable': ARCReader.objects.filter(is_reliable=True).count(),
        'unreliable': ARCReader.objects.filter(is_reliable=False).count(),
        'genre_filter': genre_filter,
        'reliable_filter': reliable_filter,
        'opts': ARCReader._meta,
    })
    return render(request, 'admin/novels/arc_readers.html', ctx)


@staff_member_required
def arc_reader_import_view(request):
    """Phase 11 — CSV import for ARC readers."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        import csv, io
        csv_file = request.FILES['csv_file']
        try:
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            imported = 0
            errors = []
            for row in reader:
                try:
                    email = row.get('email', '').strip()
                    name = row.get('name', '').strip()
                    genres = [g.strip() for g in row.get('genres', '').split(',') if g.strip()]
                    if email and name:
                        ARCReader.objects.update_or_create(
                            email=email,
                            defaults={'name': name, 'genres_interested': genres}
                        )
                        imported += 1
                except Exception as e:
                    errors.append(f"Row error: {e}")
            messages.success(request, f'✅ Imported {imported} ARC readers.')
            if errors:
                messages.warning(request, f'{len(errors)} rows had errors.')
        except Exception as e:
            messages.error(request, f'CSV parse error: {e}')
        return redirect(reverse('arc_reader_list'))

    ctx = get_admin_context(request, 'Import ARC Readers from CSV')
    ctx.update({'opts': ARCReader._meta})
    return render(request, 'admin/novels/arc_import.html', ctx)


# =============================================================================
# PHASE 12 — Multi-Platform Distribution Tracker
# =============================================================================

@staff_member_required
def distribution_tracker_view(request, book_id):
    """Phase 12 — Distribution channel revenue tracker."""
    from novels.models import DistributionChannel, DistributionPlatform
    book = get_object_or_404(Book, pk=book_id)
    channels = DistributionChannel.objects.filter(book=book).order_by('platform')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'add_channel':
            platform = request.POST.get('platform', '')
            asin_id = request.POST.get('asin_or_id', '')
            pub_url = request.POST.get('published_url', '')
            royalty = float(request.POST.get('royalty_rate', 0.70))
            if platform:
                DistributionChannel.objects.update_or_create(
                    book=book, platform=platform,
                    defaults={
                        'asin_or_id': asin_id,
                        'published_url': pub_url,
                        'royalty_rate': royalty,
                        'is_active': True,
                    }
                )
                messages.success(request, f'✅ Distribution channel "{platform}" added.')
        elif action == 'sync':
            try:
                from novels.tasks.distribution import sync_platform_revenue
                sync_platform_revenue.delay()
                messages.success(request, '✅ Revenue sync task queued for all platforms.')
            except Exception as e:
                messages.error(request, f'Task error: {e}')
        elif action == 'toggle':
            ch_id = request.POST.get('channel_id')
            ch = DistributionChannel.objects.filter(pk=ch_id, book=book).first()
            if ch:
                ch.is_active = not ch.is_active
                ch.save()
                messages.success(request, f'Channel toggled: {"Active" if ch.is_active else "Inactive"}')
        return redirect(reverse('distribution_tracker', args=[book_id]))

    total_revenue = sum(c.revenue_usd for c in channels)
    platform_labels = [c.get_platform_display() for c in channels]
    platform_revenues = [float(c.revenue_usd) for c in channels]

    ctx = get_admin_context(request, f'Distribution Tracker — {book.title}')
    ctx.update({
        'book': book,
        'channels': channels,
        'total_revenue': total_revenue,
        'platform_choices': DistributionPlatform.CHOICES,
        'platform_labels': json.dumps(platform_labels),
        'platform_revenues': json.dumps(platform_revenues),
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/distribution_tracker.html', ctx)


# =============================================================================
# PHASE 13 — Competitor Intelligence Dashboard
# =============================================================================

@staff_member_required
def competitor_intelligence_view(request):
    """Phase 13 — Competitor landscape analysis dashboard."""
    from novels.models import CompetitorBook
    competitors = CompetitorBook.objects.all().order_by('bsr')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update':
            try:
                from novels.tasks.distribution import update_competitor_data
                update_competitor_data.delay()
                messages.success(request, '✅ Competitor data update task queued.')
            except Exception as e:
                messages.error(request, f'Task error: {e}')
        elif action == 'add':
            asin = request.POST.get('asin', '').strip()
            title = request.POST.get('title', '').strip()
            author = request.POST.get('author', '').strip()
            genre = request.POST.get('genre', '').strip()
            if asin and title:
                from decimal import Decimal
                CompetitorBook.objects.update_or_create(
                    asin=asin,
                    defaults={
                        'title': title,
                        'author': author,
                        'genre': genre,
                        'price_usd': Decimal(request.POST.get('price_usd', '3.99')),
                        'review_count': int(request.POST.get('review_count', 0)),
                        'avg_rating': float(request.POST.get('avg_rating', 0)),
                        'bsr': int(request.POST.get('bsr', 999999)),
                    }
                )
                messages.success(request, f'✅ Competitor "{title}" added.')
        return redirect(reverse('competitor_intelligence'))

    # Price distribution
    prices = [float(c.price_usd) for c in competitors if c.price_usd]
    price_buckets = {'<$1': 0, '$1-$2': 0, '$2-$4': 0, '$4-$6': 0, '>=$6': 0}
    for p in prices:
        if p < 1: price_buckets['<$1'] += 1
        elif p < 2: price_buckets['$1-$2'] += 1
        elif p < 4: price_buckets['$2-$4'] += 1
        elif p < 6: price_buckets['$4-$6'] += 1
        else: price_buckets['>=$6'] += 1

    ctx = get_admin_context(request, 'Competitor Intelligence Dashboard')
    ctx.update({
        'competitors': competitors,
        'total': competitors.count(),
        'avg_price': round(sum(prices) / len(prices), 2) if prices else 0,
        'avg_reviews': round(sum(c.review_count for c in competitors) / competitors.count(), 0) if competitors.count() else 0,
        'price_buckets': json.dumps(list(price_buckets.values())),
        'price_labels': json.dumps(list(price_buckets.keys())),
        'opts': CompetitorBook._meta,
    })
    return render(request, 'admin/novels/competitor_intelligence.html', ctx)


# =============================================================================
# PHASE 14 — Style Fingerprint Analyzer
# =============================================================================

@staff_member_required
def style_fingerprint_view(request, pen_name_id):
    """Phase 14 — Style fingerprint analysis for a PenName."""
    from novels.models import PenName, StyleFingerprint
    pen_name = get_object_or_404(PenName, pk=pen_name_id)
    fingerprint, created = StyleFingerprint.objects.get_or_create(pen_name=pen_name)

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        if action == 'recalculate':
            try:
                from novels.tasks.distribution import recalculate_style_fingerprint
                recalculate_style_fingerprint.delay(pen_name_id)
                messages.success(request, '✅ Style fingerprint recalculation queued.')
            except Exception as e:
                messages.error(request, f'Task error: {e}')
        else:
            # Manual save
            fingerprint.style_system_prompt = request.POST.get('style_system_prompt', fingerprint.style_system_prompt)
            forbidden_raw = request.POST.get('forbidden_words', '')
            fingerprint.forbidden_words = [w.strip() for w in forbidden_raw.split(',') if w.strip()]
            fingerprint.save()
            messages.success(request, 'Style fingerprint saved.')
        return redirect(reverse('style_fingerprint', args=[pen_name_id]))

    # Metrics for radar chart
    metrics = {
        'avg_sentence_length': fingerprint.avg_sentence_length,
        'avg_paragraph_length': fingerprint.avg_paragraph_length,
        'dialogue_ratio': round((fingerprint.dialogue_ratio or 0) * 100, 1),
        'adverb_frequency': round((fingerprint.adverb_frequency or 0) * 100, 1),
        'passive_voice_ratio': round((fingerprint.passive_voice_ratio or 0) * 100, 1),
    }

    ctx = get_admin_context(request, f'Style Fingerprint — {pen_name.name}')
    ctx.update({
        'pen_name': pen_name,
        'fingerprint': fingerprint,
        'metrics': metrics,
        'metrics_json': json.dumps(metrics),
        'forbidden_words_str': ', '.join(fingerprint.forbidden_words or []),
        'opts': PenName._meta,
    })
    return render(request, 'admin/novels/style_fingerprint.html', ctx)


# =============================================================================
# PHASE 15 — Full KPI Dashboard
# =============================================================================

@staff_member_required
def kpi_dashboard_view(request):
    """Phase 15 — Aggregated KPI dashboard across all books and platforms."""
    from django.db.models import Sum, Avg, Count, F
    from novels.models import (
        Book, BookLifecycleStatus, Chapter, ChapterStatus,
        AdsPerformance, ReviewTracker, DistributionChannel,
    )
    from datetime import timedelta

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # === PRODUCTION KPIs ===
    books_qs = Book.objects.filter(is_deleted=False)
    total_books = books_qs.count()
    books_in_progress = books_qs.filter(lifecycle_status=BookLifecycleStatus.WRITING_IN_PROGRESS).count()
    books_published = books_qs.filter(
        lifecycle_status__in=[BookLifecycleStatus.PUBLISHED_KDP, BookLifecycleStatus.PUBLISHED_ALL]
    ).count()

    chapters_qs = Chapter.objects.filter(book__is_deleted=False)
    total_chapters = chapters_qs.count()
    approved_chapters = chapters_qs.filter(status=ChapterStatus.APPROVED).count()
    chapter_completion_rate = round(approved_chapters / total_chapters * 100, 1) if total_chapters else 0
    avg_ai_detection = chapters_qs.aggregate(avg=Avg('ai_detection_score'))['avg'] or 0
    avg_plagiarism = chapters_qs.aggregate(avg=Avg('plagiarism_score'))['avg'] or 0

    # === SALES & REVENUE KPIs ===
    revenue_qs = DistributionChannel.objects.filter(book__is_deleted=False)
    total_revenue = revenue_qs.aggregate(total=Sum('revenue_usd'))['total'] or 0
    total_units = revenue_qs.aggregate(total=Sum('units_sold'))['total'] or 0

    # === MARKETING KPIs ===
    ads_30d = AdsPerformance.objects.filter(
        book__is_deleted=False,
        report_date__gte=thirty_days_ago.date()
    ).aggregate(
        total_spend=Sum('spend_usd'),
        total_sales=Sum('sales_usd'),
        total_impressions=Sum('impressions'),
        total_clicks=Sum('clicks'),
    )
    total_spend = float(ads_30d['total_spend'] or 0)
    total_ad_sales = float(ads_30d['total_sales'] or 0)
    overall_acos = round(total_spend / total_ad_sales * 100, 2) if total_ad_sales else None
    roas = round(total_ad_sales / total_spend, 2) if total_spend else None

    reviews_qs = ReviewTracker.objects.filter(book__is_deleted=False)
    avg_rating = reviews_qs.aggregate(avg=Avg('avg_rating'))['avg'] or 0
    total_reviews = reviews_qs.aggregate(total=Sum('total_reviews'))['total'] or 0

    # Alerts
    alerts = []
    books_low_rating = ReviewTracker.objects.filter(avg_rating__lt=3.5, avg_rating__gt=0).count()
    if books_low_rating:
        alerts.append({'level': 'URGENT', 'message': f'{books_low_rating} book(s) have avg rating below 3.5★'})
    if overall_acos and overall_acos > 50:
        alerts.append({'level': 'WARNING', 'message': f'Overall ACOS is {overall_acos}% — above 50% threshold'})
    if avg_ai_detection > 30:
        alerts.append({'level': 'URGENT', 'message': f'Average AI detection score is {avg_ai_detection:.1f}% — above 30% threshold'})
    if avg_plagiarism > 5:
        alerts.append({'level': 'CRITICAL', 'message': f'Average plagiarism score is {avg_plagiarism:.1f}% — above 5% threshold'})

    ctx = get_admin_context(request, 'KPI Dashboard')
    ctx.update({
        'total_books': total_books,
        'books_in_progress': books_in_progress,
        'books_published': books_published,
        'total_chapters': total_chapters,
        'approved_chapters': approved_chapters,
        'chapter_completion_rate': chapter_completion_rate,
        'avg_ai_detection': round(avg_ai_detection, 1),
        'avg_plagiarism': round(avg_plagiarism, 1),
        'total_revenue': total_revenue,
        'total_units': total_units,
        'total_spend_30d': round(total_spend, 2),
        'total_ad_sales_30d': round(total_ad_sales, 2),
        'overall_acos': overall_acos,
        'roas': roas,
        'avg_rating': round(avg_rating, 2),
        'total_reviews': total_reviews,
        'alerts': alerts,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/kpi_dashboard.html', ctx)


# =============================================================================
# PHASE 16 — Legal Protection & Copyright Automation
# =============================================================================

@staff_member_required
def legal_protection_view(request, book_id):
    """Phase 16 — Legal protection tools: DMCA generator, copyright reminder."""
    book = get_object_or_404(Book, pk=book_id)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'check_theft':
            try:
                from novels.tasks.legal import check_content_theft
                check_content_theft.delay(book_id)
                messages.success(request, '✅ Plagiarism inbound scan queued via Copyscape.')
            except Exception as e:
                messages.error(request, f'Task error: {e}')
        elif action == 'generate_dmca':
            infringing_url = request.POST.get('infringing_url', '').strip()
            if infringing_url:
                pen_name = book.pen_name
                from django.utils import timezone as _tz
                dmca_letter = (
                    f"DMCA TAKEDOWN NOTICE\n"
                    f"Date: {_tz.now().strftime('%B %d, %Y')}\n\n"
                    f"To Whom It May Concern:\n\n"
                    f"I am the copyright owner of the following original work:\n"
                    f"  Title: {book.title}\n"
                    f"  Author: {pen_name.name if pen_name else 'Author'}\n"
                    f"  ASIN: {book.asin or 'Pending'}\n"
                    f"  Published via Amazon Kindle Direct Publishing\n\n"
                    f"I have discovered that my copyrighted work is being reproduced without authorization at:\n"
                    f"  {infringing_url}\n\n"
                    f"I hereby request that you immediately remove or disable access to the infringing material.\n\n"
                    f"I have a good faith belief that use of the described material in the manner complained of "
                    f"is not authorized by the copyright owner, the copyright owner's agent, or by operation of law.\n\n"
                    f"The information provided in this notification is accurate. Under penalty of perjury, I am "
                    f"authorized to act on behalf of the copyright owner.\n\n"
                    f"Signed electronically: {pen_name.name if pen_name else 'Author'}\n"
                    f"Date: {_tz.now().strftime('%B %d, %Y')}\n"
                )
                messages.success(request, 'DMCA notice generated — see below.')
                disclaimer = (
                    f'This is a work of fiction. Names, characters, places, and incidents either are the products '
                    f'of the author\'s imagination or are used fictitiously. Any resemblance to actual persons, living '
                    f'or dead, events, or locales is entirely coincidental.\n\n'
                    f'Copyright © {timezone.now().year} {pen_name.name if pen_name else "Author"}. All rights reserved.'
                )
                ctx = get_admin_context(request, f'Legal Protection — {book.title}')
                ctx.update({
                    'book': book,
                    'dmca_letter': dmca_letter,
                    'infringing_url': infringing_url,
                    'disclaimer': disclaimer,
                    'copyright_registered': book.copyright_registered,
                    'opts': Book._meta,
                })
                return render(request, 'admin/novels/legal_protection.html', ctx)
            else:
                messages.error(request, 'Please provide the infringing URL.')
        elif action == 'setup_alerts':
            try:
                from novels.tasks.legal import setup_google_alerts
                setup_google_alerts.delay(book_id)
                messages.success(request, '✅ Google Alerts setup task queued.')
            except Exception as e:
                messages.error(request, f'Task error: {e}')
        return redirect(reverse('legal_protection', args=[book_id]))

    # Generate legal disclaimer preview
    pen_name = book.pen_name
    disclaimer = (
        f'This is a work of fiction. Names, characters, places, and incidents either are the products '
        f'of the author\'s imagination or are used fictitiously. Any resemblance to actual persons, living '
        f'or dead, events, or locales is entirely coincidental.\n\n'
        f'Copyright © {timezone.now().year} {pen_name.name if pen_name else "Author"}. All rights reserved.\n\n'
        f'No part of this publication may be reproduced, distributed, or transmitted in any form or by any '
        f'means, including photocopying, recording, or other electronic or mechanical methods, without the '
        f'prior written permission of the publisher, except in the case of brief quotations embodied in '
        f'critical reviews and certain other non-commercial uses permitted by copyright law.'
    )

    ctx = get_admin_context(request, f'Legal Protection — {book.title}')
    ctx.update({
        'book': book,
        'disclaimer': disclaimer,
        'copyright_registered': book.copyright_registered,
        'opts': Book._meta,
    })
    return render(request, 'admin/novels/legal_protection.html', ctx)


# =============================================================================
# URL Registration Helper
# =============================================================================

def get_custom_admin_urls():
    """Return URL patterns for all custom admin views."""
    return [
        path(
            'novels/book/<int:book_id>/keywords/',
            keyword_research_view,
            name='keyword_research',
        ),
        path(
            'novels/book/<int:book_id>/keywords/generate/',
            generate_concepts_view,
            name='generate_concepts',
        ),
        path(
            'novels/book/<int:book_id>/concepts/',
            concept_selection_view,
            name='concept_selection',
        ),
        path(
            'novels/book/<int:book_id>/description/',
            description_editor_view,
            name='description_editor',
        ),
        path(
            'novels/book/<int:book_id>/description/generate/',
            generate_description_view,
            name='generate_description',
        ),
        path(
            'novels/book/<int:book_id>/story-bible/',
            story_bible_view,
            name='story_bible',
        ),
        path(
            'novels/book/<int:book_id>/qa/',
            qa_review_view,
            name='qa_review',
        ),
        path(
            'novels/book/<int:book_id>/kdp-preflight/',
            kdp_preflight_view,
            name='kdp_preflight',
        ),
        path(
            'novels/book/<int:book_id>/export/',
            export_book_view,
            name='export_book',
        ),
        path(
            'novels/book/<int:book_id>/ads/',
            ads_dashboard_view,
            name='ads_dashboard',
        ),
        # Phase 8 — Dynamic Pricing
        path(
            'novels/book/<int:book_id>/pricing/',
            pricing_strategy_view,
            name='pricing_strategy',
        ),
        # Phase 11 — Reviews & ARC
        path(
            'novels/book/<int:book_id>/reviews/',
            review_arc_view,
            name='review_arc',
        ),
        path(
            'novels/arc-readers/',
            arc_reader_list_view,
            name='arc_reader_list',
        ),
        path(
            'novels/arc-readers/import/',
            arc_reader_import_view,
            name='arc_reader_import',
        ),
        # Phase 12 — Distribution
        path(
            'novels/book/<int:book_id>/distribution/',
            distribution_tracker_view,
            name='distribution_tracker',
        ),
        # Phase 13 — Competitor Intelligence
        path(
            'novels/competitor-intelligence/',
            competitor_intelligence_view,
            name='competitor_intelligence',
        ),
        # Phase 14 — Style Fingerprint
        path(
            'novels/pen-name/<int:pen_name_id>/style-fingerprint/',
            style_fingerprint_view,
            name='style_fingerprint',
        ),
        # Phase 15 — KPI Dashboard
        path(
            'novels/kpi-dashboard/',
            kpi_dashboard_view,
            name='kpi_dashboard',
        ),
        # Phase 16 — Legal Protection
        path(
            'novels/book/<int:book_id>/legal/',
            legal_protection_view,
            name='legal_protection',
        ),
    ]

