"""
AI Writer Service — facade over the configured LLM provider.

Usage:
    writer = AIWriterService()
    result = writer.write_chapter(chapter)   # Chapter model instance
    print(result['content'])

Swap provider: set LLM_PROVIDER='gemini' in .env (no code change needed).
"""

import json
import logging
import re

from .llm_providers import get_llm_provider

logger = logging.getLogger(__name__)


class AIWriterService:
    """
    High-level AI writing operations.
    All public methods accept Django model instances and return plain dicts.
    """

    def __init__(self):
        self.llm = get_llm_provider()
        logger.info(f"AIWriterService initialised with provider: {self.llm.__class__.__name__}")

    # =========================================================================
    # CHAPTER WRITING
    # =========================================================================

    def write_chapter(self, chapter) -> dict:
        """
        Generate content for a chapter.

        Args:
            chapter: Chapter model instance

        Returns:
            {"content": str, "model": str, "tokens_used": int, "cost_usd": float}
        """
        book = chapter.book
        genre = book.pen_name.niche_genre if book.pen_name else "fiction"

        system_prompt = (
            f"You are an expert fiction writer specializing in {genre}. "
            "Write vivid, engaging prose with strong pacing and distinct character voices. "
            "Follow the chapter brief exactly. Maintain consistency with the story bible. "
            "Target approximately 1,000 words. Write the chapter directly — no preamble."
        )

        user_prompt = (
            f"## Story Bible\n{self._format_story_bible(getattr(book, 'story_bible', None))}\n\n"
            f"## Writing Style\n{self._get_style_fingerprint(book)}\n\n"
            f"## Previous Chapter Excerpt (last ~300 words)\n{self._get_previous_chapter_excerpt(chapter)}\n\n"
            f"## Chapter {chapter.chapter_number} Brief\n{self._format_chapter_brief(chapter)}\n\n"
            f"---\nWrite Chapter {chapter.chapter_number}: \"{chapter.title or 'Untitled'}\" now."
        )

        result = self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.8,
        )

        return {
            "content": result["content"].strip(),
            "model": result["model"],
            "tokens_used": result["tokens_in"] + result["tokens_out"],
            "cost_usd": result["cost_usd"],
        }

    def rewrite_chapter(self, chapter, feedback: str) -> dict:
        """
        Rewrite a rejected chapter incorporating QA feedback.

        Returns:
            {"content": str, "model": str, "tokens_used": int, "cost_usd": float}
        """
        book = chapter.book
        genre = book.pen_name.niche_genre if book.pen_name else "fiction"

        system_prompt = (
            f"You are an expert fiction editor and rewriter specializing in {genre}. "
            "Rewrite the chapter draft to address all QA feedback while preserving "
            "core plot events and character voices. Write the chapter directly — no preamble."
        )

        user_prompt = (
            f"## Original Chapter Draft\n{chapter.content[:3000] if chapter.content else '(Empty)'}\n\n"
            f"## QA Feedback to Address\n{feedback}\n\n"
            f"## Writing Style\n{self._get_style_fingerprint(book)}\n\n"
            "---\nWrite the complete rewritten chapter now."
        )

        result = self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.7,
        )

        return {
            "content": result["content"].strip(),
            "model": result["model"],
            "tokens_used": result["tokens_in"] + result["tokens_out"],
            "cost_usd": result["cost_usd"],
        }

    # =========================================================================
    # CONCEPT & PLANNING
    # =========================================================================

    def generate_book_concepts(self, book) -> list[dict]:
        """
        Generate 3 distinct book concepts for admin review.

        Returns:
            List of 3 dicts: [{"title", "hook", "core_twist", "synopsis", "comparable_titles"}, ...]
        """
        genre = book.pen_name.niche_genre if book.pen_name else "fiction"
        style_hint = ""
        if book.pen_name and book.pen_name.writing_style_prompt:
            style_hint = f"Author style: {book.pen_name.writing_style_prompt[:200]}"

        result = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a bestselling {genre} author and book market analyst. "
                        "Generate highly commercial book concepts. "
                        "Respond with valid JSON only — no markdown, no extra text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate 3 distinct commercial {genre} novel concepts.\n"
                        f"{style_hint}\n\n"
                        "Return a JSON array of exactly 3 objects, each with keys:\n"
                        "title, hook (one gripping sentence), core_twist, synopsis (2-3 sentences), "
                        "comparable_titles (list of 3 bestsellers).\n\n"
                        'Example: [{"title": "...", "hook": "...", "core_twist": "...", '
                        '"synopsis": "...", "comparable_titles": ["A", "B", "C"]}]'
                    ),
                },
            ],
            max_tokens=1200,
            temperature=0.9,
            json_mode=True,
        )

        concepts = self._parse_json(result["content"], fallback=[])
        # Some models wrap in {"concepts": [...]}
        if isinstance(concepts, dict):
            concepts = concepts.get("concepts", list(concepts.values())[0] if concepts else [])
        return concepts[:3] if isinstance(concepts, list) else []

    def create_story_bible(self, book) -> dict:
        """
        Generate a comprehensive story bible for a book.

        Returns:
            Story bible dict with keys: characters, world_rules, four_act_outline, timeline
        """
        genre = book.pen_name.niche_genre if book.pen_name else "fiction"
        n = book.target_chapter_count or 30

        result = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a master {genre} storyteller. "
                        "Create a comprehensive story bible to guide a full novel. "
                        "Respond with valid JSON only — no markdown fences."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Create a story bible for this {genre} novel:\n\n"
                        f"Title: {book.title}\n"
                        f"Synopsis: {book.synopsis or 'Invent an appropriate story.'}\n"
                        f"Hook: {book.hook or ''}\n"
                        f"Core Twist: {book.core_twist or ''}\n"
                        f"Comparable Titles: {', '.join(book.comparable_titles) if book.comparable_titles else 'top genre bestsellers'}\n"
                        f"Target Chapters: {n}\n\n"
                        "Return JSON with exactly these keys:\n"
                        "characters (protagonist, antagonist, supporting[]), "
                        "world_rules (setting, time_period, key_locations[], atmosphere, important_rules[]), "
                        "four_act_outline (act_1_setup, act_2_confrontation, act_3_complication, act_4_resolution — "
                        "each with chapters[], summary, key_events[]), "
                        "timeline (array of {day, event, chapter_range[]}), "
                        "thematic_elements (themes[], motifs[])."
                    ),
                },
            ],
            max_tokens=3000,
            temperature=0.7,
            json_mode=True,
        )

        return self._parse_json(result["content"], fallback={})

    def generate_chapter_briefs(self, book, story_bible: dict) -> list[dict]:
        """
        Generate individual chapter briefs for the full book.

        Returns:
            List of chapter brief dicts
        """
        genre = book.pen_name.niche_genre if book.pen_name else "fiction"
        n = book.target_chapter_count or 30
        outline_summary = json.dumps(
            story_bible.get("four_act_outline", {}), indent=2
        )[:1200]

        result = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an expert {genre} story architect. "
                        "Create tight chapter outlines with tension on every page. "
                        "Respond with valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate {n} chapter briefs for \"{book.title}\".\n\n"
                        f"Four-Act Structure:\n{outline_summary}\n\n"
                        f"Each chapter brief must be a JSON object with keys:\n"
                        "chapter_number (int), title (str), opening_hook (str), "
                        "key_events (list of str), ending_hook (str), mood (str), "
                        "pov_character (str), word_count_target (int, default 1000).\n\n"
                        f"Return a JSON array of exactly {n} chapter brief objects."
                    ),
                },
            ],
            max_tokens=4000,
            temperature=0.7,
            json_mode=True,
        )

        briefs = self._parse_json(result["content"], fallback=[])
        if isinstance(briefs, dict):
            briefs = briefs.get("chapters", list(briefs.values())[0] if briefs else [])
        return briefs if isinstance(briefs, list) else []

    def generate_book_description(self, book) -> dict:
        """
        Generate A/B Amazon book descriptions.

        Returns:
            {"version_a": str, "version_b": str, "hook_a": str, "hook_b": str}
        """
        genre = book.pen_name.niche_genre if book.pen_name else "fiction"
        kw = getattr(book, 'keyword_research', None)
        keywords = (kw.kdp_backend_keywords[:4] if kw else []) or [genre]
        comparable = book.comparable_titles or [f"top {genre} bestsellers"]

        result = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a bestselling {genre} book marketer. "
                        "Write Amazon blurbs that convert browsers into buyers. "
                        "Use only Amazon HTML: <b>, <em>, <br>, <ul>, <li>. "
                        "Respond with valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Write A/B Amazon descriptions for:\n\n"
                        f"Title: {book.title}\n"
                        f"Synopsis: {book.synopsis or 'A gripping ' + genre + ' novel.'}\n"
                        f"Hook: {book.hook or ''}\n"
                        f"Core Twist: {book.core_twist or ''}\n"
                        f"Keywords: {', '.join(keywords)}\n"
                        f"Comp titles: {', '.join(comparable)}\n\n"
                        "Version A = emotional/character angle.\n"
                        "Version B = stakes/thriller angle.\n\n"
                        "Each follows: HOOK (bold) → SETUP → STAKES → TWIST TEASE (em) → CTA (bold).\n\n"
                        "Return JSON:\n"
                        '{"version_a": "html string", "version_b": "html string", '
                        '"hook_a": "short hook A", "hook_b": "short hook B"}'
                    ),
                },
            ],
            max_tokens=1500,
            temperature=0.8,
            json_mode=True,
        )

        data = self._parse_json(result["content"], fallback={})
        return {
            "version_a": data.get("version_a", ""),
            "version_b": data.get("version_b", ""),
            "hook_a": data.get("hook_a", ""),
            "hook_b": data.get("hook_b", ""),
        }

    def check_consistency(self, book, chapters) -> list[dict]:
        """
        Check chapters for plot/character/timeline inconsistencies.

        Returns:
            List of issue dicts: [{"chapter": int, "type": str, "description": str}]
        """
        story_bible_text = self._format_story_bible(getattr(book, 'story_bible', None))

        summaries = []
        for ch in list(chapters)[:12]:  # Cap to fit context window
            excerpt = (ch.content or "")[:350]
            summaries.append(f"Ch {ch.chapter_number} ({ch.title or 'Untitled'}):\n{excerpt}")
        chapters_text = "\n\n".join(summaries)

        result = self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional continuity editor. "
                        "Find plot holes, character inconsistencies, and timeline errors. "
                        "Respond with valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"## Story Bible\n{story_bible_text}\n\n"
                        f"## Chapter Excerpts\n{chapters_text}\n\n"
                        "List all consistency issues found.\n"
                        'Return JSON: {"issues": [{"chapter": 1, "type": "character|plot|timeline|world", '
                        '"description": "..."}]}\n'
                        'If no issues: {"issues": []}'
                    ),
                },
            ],
            max_tokens=800,
            temperature=0.2,
            json_mode=True,
        )

        data = self._parse_json(result["content"], fallback={"issues": []})
        return data.get("issues", [])

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _format_story_bible(self, story_bible) -> str:
        if story_bible is None:
            return "No story bible yet."
        parts = []
        chars = story_bible.characters or {}
        protagonist = chars.get("protagonist", {})
        if protagonist:
            parts.append(
                f"PROTAGONIST: {protagonist.get('name', '?')} — "
                f"{protagonist.get('occupation', '')}. "
                f"Goal: {protagonist.get('goal', '')}."
            )
        antagonist = chars.get("antagonist", {})
        if antagonist:
            parts.append(f"ANTAGONIST: {antagonist.get('name', '?')} — {antagonist.get('motivation', '')}.")
        world = story_bible.world_rules or {}
        if world:
            parts.append(f"SETTING: {world.get('setting', '')} ({world.get('time_period', '')}).")
            locs = world.get("key_locations", [])
            if locs:
                parts.append(f"KEY LOCATIONS: {', '.join(locs[:4])}.")
        outline = story_bible.four_act_outline or {}
        for key in ["act_1_setup", "act_2_confrontation", "act_3_complication", "act_4_resolution"]:
            act = outline.get(key, {})
            if act:
                parts.append(f"{key.replace('_', ' ').title()}: {act.get('summary', '')}.")
        return "\n".join(parts) if parts else "Story bible empty."

    def _format_chapter_brief(self, chapter) -> str:
        brief = chapter.brief or {}
        if not brief:
            return f"Continue the story naturally for chapter {chapter.chapter_number}."
        lines = []
        if brief.get("opening_hook"):
            lines.append(f"Opening: {brief['opening_hook']}")
        for i, event in enumerate(brief.get("key_events", []), 1):
            lines.append(f"  Event {i}: {event}")
        if brief.get("ending_hook"):
            lines.append(f"Ending: {brief['ending_hook']}")
        if brief.get("mood"):
            lines.append(f"Mood: {brief['mood']}")
        if brief.get("pov_character"):
            lines.append(f"POV: {brief['pov_character']}")
        return "\n".join(lines)

    def _get_previous_chapter_excerpt(self, chapter) -> str:
        try:
            prev = chapter.book.chapters.filter(
                chapter_number=chapter.chapter_number - 1,
                is_deleted=False,
            ).first()
            if prev and prev.content:
                words = prev.content.split()
                return " ".join(words[-300:])
        except Exception:
            pass
        return "(First chapter — no prior content.)"

    def _get_style_fingerprint(self, book) -> str:
        try:
            pen_name = book.pen_name
            if pen_name:
                sf = getattr(pen_name, 'style_fingerprint', None)
                if sf and sf.style_system_prompt:
                    return sf.style_system_prompt[:500]
                if pen_name.writing_style_prompt:
                    return pen_name.writing_style_prompt[:500]
        except Exception:
            pass
        return "Write in a clear, engaging style appropriate for commercial fiction."

    def _parse_json(self, text: str, fallback=None):
        """Parse JSON from LLM output — handles markdown fences."""
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        logger.warning(f"JSON parse failed on: {text[:150]}")
        return fallback if fallback is not None else {}
