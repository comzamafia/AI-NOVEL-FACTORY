"""
Forms for custom admin views in the AI Novel Factory system.
"""

from django import forms
from django.utils.html import format_html


# =============================================================================
# PHASE 2 — Keyword Research Forms
# =============================================================================

class KeywordApprovalForm(forms.Form):
    """Form for reviewing and approving KDP keyword metadata."""

    # Title & Subtitle
    suggested_title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'style': 'width:100%'}),
        help_text='Must have primary keyword in first 5 words. Max 200 chars.',
    )
    suggested_subtitle = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'style': 'width:100%'}),
        help_text='Include secondary keywords. Max 200 chars.',
    )

    # KDP 7 Backend Keywords
    kdp_keyword_1 = forms.CharField(max_length=50, label='KDP Keyword 1', widget=forms.TextInput(attrs={'class': 'vTextField'}))
    kdp_keyword_2 = forms.CharField(max_length=50, label='KDP Keyword 2', widget=forms.TextInput(attrs={'class': 'vTextField'}))
    kdp_keyword_3 = forms.CharField(max_length=50, label='KDP Keyword 3', widget=forms.TextInput(attrs={'class': 'vTextField'}))
    kdp_keyword_4 = forms.CharField(max_length=50, label='KDP Keyword 4', widget=forms.TextInput(attrs={'class': 'vTextField'}))
    kdp_keyword_5 = forms.CharField(max_length=50, label='KDP Keyword 5', widget=forms.TextInput(attrs={'class': 'vTextField'}))
    kdp_keyword_6 = forms.CharField(max_length=50, label='KDP Keyword 6', widget=forms.TextInput(attrs={'class': 'vTextField'}))
    kdp_keyword_7 = forms.CharField(max_length=50, label='KDP Keyword 7', widget=forms.TextInput(attrs={'class': 'vTextField'}))

    # Categories
    kdp_category_1 = forms.CharField(
        max_length=200,
        label='KDP Category 1',
        widget=forms.TextInput(attrs={'class': 'vTextField', 'style': 'width:100%'}),
        help_text='e.g. Books > Mystery, Thriller & Suspense > Thrillers > Psychological',
    )
    kdp_category_2 = forms.CharField(
        max_length=200,
        label='KDP Category 2',
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'style': 'width:100%'}),
    )

    action = forms.CharField(widget=forms.HiddenInput, initial='approve')

    FORBIDDEN_WORDS = {'best', 'free', 'novel', '#1', 'number one', 'top', 'great', 'sale'}
    AMAZON_FORBIDDEN = {'bestselling', 'bestseller', 'best seller', 'free', 'sale', 'discount'}

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get('suggested_title') or '').lower()
        subtitle = (cleaned.get('suggested_subtitle') or '').lower()

        # Collect backend keywords
        backend_keywords = []
        for i in range(1, 8):
            kw = cleaned.get(f'kdp_keyword_{i}', '').strip().lower()
            if kw:
                backend_keywords.append(kw)

        # Validate: backend keywords must not appear in title/subtitle
        if cleaned.get('action') == 'approve':
            for kw in backend_keywords:
                if kw in title or kw in subtitle:
                    raise forms.ValidationError(
                        f'Backend keyword "{kw}" must not repeat in Title or Subtitle.'
                    )

            # Check Amazon forbidden words
            all_text = title + ' ' + subtitle
            for forbidden in self.FORBIDDEN_WORDS:
                if forbidden in all_text:
                    self.add_error(
                        'suggested_title',
                        f'Amazon forbids the word "{forbidden}" in titles/subtitles.',
                    )

        return cleaned

    def get_backend_keywords(self):
        """Return list of the 7 backend keywords from cleaned data."""
        return [
            self.cleaned_data.get(f'kdp_keyword_{i}', '').strip()
            for i in range(1, 8)
            if self.cleaned_data.get(f'kdp_keyword_{i}', '').strip()
        ]


# =============================================================================
# PHASE 3 — Concept Selection Form
# =============================================================================

class ConceptSelectionForm(forms.Form):
    """Form for selecting which AI-generated book concept to pursue."""

    selected_concept = forms.ChoiceField(
        choices=[],  # Populated dynamically
        widget=forms.RadioSelect,
        label='Select Concept to Develop',
    )
    custom_title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'style': 'width:100%'}),
        label='Override Title (optional)',
    )
    custom_hook = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'style': 'width:100%'}),
        label='Override Hook (optional)',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'style': 'width:100%'}),
        label='Notes for Writer',
    )

    def __init__(self, *args, concepts=None, **kwargs):
        super().__init__(*args, **kwargs)
        if concepts:
            self.fields['selected_concept'].choices = [
                (str(i), f"Concept {i+1}: {c.get('title', 'Untitled')}")
                for i, c in enumerate(concepts)
            ]


# =============================================================================
# PHASE 4 — Book Description Forms
# =============================================================================

class DescriptionApprovalForm(forms.Form):
    """Form for editing and approving book descriptions."""

    AMAZON_MAX_CHARS = 4000

    description_html_a = forms.CharField(
        label='Description — Version A (HTML)',
        widget=forms.Textarea(attrs={'rows': 15, 'style': 'width:100%; font-family:monospace; font-size:12px;'}),
        help_text='Supported tags: <b>, <em>, <br>, <ul>, <li>. Max 4,000 characters.',
    )
    description_html_b = forms.CharField(
        label='Description — Version B (HTML)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 15, 'style': 'width:100%; font-family:monospace; font-size:12px;'}),
    )
    active_version = forms.ChoiceField(
        choices=[('A', 'Version A'), ('B', 'Version B')],
        initial='A',
        widget=forms.RadioSelect,
        label='Active Version (will be used in export)',
    )
    hook_line = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'style': 'width:100%'}),
        label='Hook Line',
    )

    def clean_description_html_a(self):
        html = self.cleaned_data.get('description_html_a', '')
        if len(html) > self.AMAZON_MAX_CHARS:
            raise forms.ValidationError(
                f'Description A exceeds Amazon limit ({len(html)}/{self.AMAZON_MAX_CHARS} chars).'
            )
        return html

    def clean_description_html_b(self):
        html = self.cleaned_data.get('description_html_b', '')
        if html and len(html) > self.AMAZON_MAX_CHARS:
            raise forms.ValidationError(
                f'Description B exceeds Amazon limit ({len(html)}/{self.AMAZON_MAX_CHARS} chars).'
            )
        return html


# =============================================================================
# PHASE 5 — Story Architecture Forms
# =============================================================================

class StoryBibleApprovalForm(forms.Form):
    """Form for reviewing and approving the story bible."""

    world_building = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'style': 'width:100%'}),
        label='World Building & Setting',
    )
    main_characters = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'style': 'width:100%'}),
        label='Main Characters (JSON or text)',
    )
    timeline = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'style': 'width:100%'}),
        help_text='Story timeline and key events.',
    )
    four_act_outline = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8, 'style': 'width:100%'}),
        label='Four-Act Outline',
    )
    clue_tracker = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 6, 'style': 'width:100%'}),
        label='Clue & Red Herring Tracker',
        help_text='List all planted clues and foreshadowing.',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'style': 'width:100%'}),
    )


# =============================================================================
# PHASE 7 — QA Gate + KDP Pre-Flight Checklist
# =============================================================================

class QAReviewForm(forms.Form):
    """QA review form for chapter or full book."""

    DECISION_CHOICES = [
        ('approve', '✅ Approve — Content is good'),
        ('reject', '❌ Reject & Rewrite — AI will rewrite with feedback'),
    ]
    decision = forms.ChoiceField(choices=DECISION_CHOICES, widget=forms.RadioSelect)
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'style': 'width:100%'}),
        help_text='Required if Reject. Feedback is sent to the AI rewrite prompt.',
    )
    originality_6_point_score = forms.IntegerField(
        min_value=0, max_value=6,
        required=False,
        label='6-Point Originality Score (0-6)',
        help_text='Must be ≥ 5 to approve.',
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('decision') == 'reject' and not cleaned.get('feedback'):
            raise forms.ValidationError('Feedback is required when rejecting a chapter.')
        if cleaned.get('decision') == 'approve':
            score = cleaned.get('originality_6_point_score')
            if score is not None and score < 5:
                self.add_error(
                    'originality_6_point_score',
                    'Must score at least 5/6 on the originality checklist before approval.',
                )
        return cleaned


class KDPPreFlightForm(forms.Form):
    """KDP Pre-Flight Checklist that must be 100% completed to unlock Export."""

    ai_disclosure = forms.ChoiceField(
        choices=[
            ('ai_generated', 'AI-Generated (must disclose to KDP)'),
            ('ai_assisted', 'AI-Assisted (human-written, AI-enhanced — no disclosure required)'),
        ],
        widget=forms.RadioSelect,
        label='AI Disclosure Status',
    )
    copyright_check = forms.BooleanField(
        label='No copyrighted characters, place names, or plots from other works',
        required=True,
    )
    trademark_check = forms.BooleanField(
        label='No real brand names or real person names without permission',
        required=True,
    )
    derivative_check = forms.BooleanField(
        label='This is NOT a summary, companion, or derivative of another book',
        required=True,
    )
    quality_check = forms.BooleanField(
        label='Content is readable, coherent, and properly formatted',
        required=True,
    )
    originality_ai_score = forms.DecimalField(
        max_digits=5, decimal_places=2,
        label='AI Detection Score (%) — Target < 20%',
        help_text='From Originality.ai. Must be below 20%.',
    )
    plagiarism_score = forms.DecimalField(
        max_digits=5, decimal_places=2,
        label='Plagiarism Score (%) — Target < 3%',
        help_text='From Copyscape. Must be below 3%.',
    )
    copyright_registered = forms.ChoiceField(
        choices=[
            ('yes', 'Yes — U.S. Copyright registered ($65)'),
            ('after', 'Will register after publish'),
            ('no', 'No — not planning to register'),
        ],
        widget=forms.RadioSelect,
        label='U.S. Copyright Registration Status',
    )
    keyword_metadata_locked = forms.BooleanField(
        label='Title, Subtitle, 7 Keywords, 2 Categories confirmed and locked',
        required=True,
    )

    def clean(self):
        cleaned = super().clean()
        ai_score = cleaned.get('originality_ai_score')
        plag_score = cleaned.get('plagiarism_score')

        if ai_score is not None and ai_score >= 20:
            self.add_error(
                'originality_ai_score',
                f'AI Detection Score is {ai_score}% — must be below 20% before export.',
            )

        if plag_score is not None and plag_score >= 3:
            self.add_error(
                'plagiarism_score',
                f'Plagiarism Score is {plag_score}% — must be below 3% before export.',
            )
        return cleaned


# =============================================================================
# PHASE 10 — Ads Optimization Forms
# =============================================================================

class AdsOptimizationForm(forms.Form):
    """Manual override form for ads keyword decisions."""

    target_acos = forms.DecimalField(
        max_digits=5, decimal_places=2,
        initial=30,
        label='Target ACoS (%)',
        help_text='Amazon Cost of Sale target. Typical: 20-35%.',
    )
    daily_budget = forms.DecimalField(
        max_digits=8, decimal_places=2,
        required=False,
        label='Override Daily Budget (USD)',
    )
    pause_threshold_acos = forms.DecimalField(
        max_digits=5, decimal_places=2,
        initial=70,
        label='Pause Keyword if ACoS > (%)',
    )
    scale_threshold_acos = forms.DecimalField(
        max_digits=5, decimal_places=2,
        initial=25,
        label='Scale Keyword if ACoS < (%)',
    )
