"""
Management command to seed the database with realistic sample data for testing.

Usage:
    python manage.py seed_data              # seed everything
    python manage.py seed_data --clear      # wipe novels data first, then seed
    python manage.py seed_data --minimal    # only 1 pen name, 2 books (fast)
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed the database with sample data for development/testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all novels data before seeding.",
        )
        parser.add_argument(
            "--minimal",
            action="store_true",
            help="Seed minimal data only (1 pen name, 2 books).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()

        self.stdout.write(self.style.MIGRATE_HEADING("🌱 Seeding database..."))

        minimal = options["minimal"]

        users = self._seed_users()
        pen_names = self._seed_pen_names(minimal)
        books = self._seed_books(pen_names, minimal)
        self._seed_keyword_research(books)
        self._seed_book_descriptions(books)
        self._seed_story_bibles(books)
        self._seed_chapters(books, minimal)
        self._seed_pricing(books)
        self._seed_ads(books)
        self._seed_reviews(books)
        self._seed_arc_readers(pen_names)
        self._seed_competitor_books(books)
        self._seed_subscriptions(users)
        self._seed_distribution(books)

        self.stdout.write(self.style.SUCCESS("\n✅  Seed complete!"))
        self.stdout.write(
            f"   Pen names: {len(pen_names)} | Books: {len(books)} | Users: {len(users)}"
        )
        self.stdout.write("   Admin → http://localhost:8000/admin/")
        self.stdout.write("   Login: admin / admin123")

    # =========================================================================
    # CLEAR
    # =========================================================================

    def _clear_data(self):
        from novels.models import (
            PenName, Book, StoryBible, Chapter, KeywordResearch,
            BookDescription, PricingStrategy, AdsPerformance, ReviewTracker,
            ARCReader, CompetitorBook, DistributionChannel, StyleFingerprint,
        )
        from novels.models.subscription import Subscription, ChapterPurchase

        self.stdout.write("🗑  Clearing existing data…")
        for model in [
            ChapterPurchase, Subscription, AdsPerformance, ReviewTracker,
            ARCReader, CompetitorBook, DistributionChannel, PricingStrategy,
            BookDescription, KeywordResearch, Chapter, StoryBible,
            StyleFingerprint, Book, PenName,
        ]:
            count = model.objects.all().count()
            model.objects.all().delete()
            self.stdout.write(f"   Deleted {count} {model.__name__} records")

    # =========================================================================
    # USERS
    # =========================================================================

    def _seed_users(self):
        users = []

        # Superuser for admin
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        admin.set_password("admin123")
        admin.save()

        # Regular readers
        reader_data = [
            ("sarah_read", "sarah@example.com", "Sarah", "Johnson"),
            ("mike_books", "mike@example.com", "Mike", "Thompson"),
            ("thriller_fan", "thriller@example.com", "Emma", "Davies"),
            ("mystery_lover", "mystery@example.com", "James", "Wilson"),
        ]
        for uname, email, first, last in reader_data:
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "is_staff": False,
                },
            )
            u.set_password("reader123")
            u.save()
            users.append(u)

        self.stdout.write(f"  ✓ Users: {User.objects.count()} total")
        return users

    # =========================================================================
    # PEN NAMES
    # =========================================================================

    def _seed_pen_names(self, minimal=False):
        from novels.models import PenName
        from novels.models.distribution import StyleFingerprint

        pen_name_data = [
            {
                "name": "Victoria Blackwood",
                "niche_genre": "Psychological Thriller",
                "bio": (
                    "Victoria Blackwood writes gripping psychological thrillers that explore "
                    "the darkest corners of the human mind. A former criminal psychologist, "
                    "she brings clinical authenticity to her complex characters and twisty plots. "
                    "Her debut series has sold over 50,000 copies on Amazon Kindle."
                ),
                "writing_style_prompt": (
                    "Write in a tense, atmospheric style with short punchy sentences during action "
                    "and longer, introspective passages for character study. Use unreliable narration "
                    "subtly. Plant red herrings naturally. Dark, literary tone — think Tana French "
                    "meets Gillian Flynn. First-person past tense. Rich internal monologue."
                ),
                "website_url": "https://victoriablackwood.com",
                "twitter_handle": "@VBlackwoodBooks",
                "total_books_published": 3,
                "total_revenue_usd": Decimal("18420.50"),
                "style": {
                    "avg_sentence_length": 14.2,
                    "dialogue_ratio": 0.28,
                    "passive_voice_ratio": 0.08,
                    "adverb_frequency": 0.012,
                    "top_bigrams": ["dark eyes", "couldn't breathe", "something wrong"],
                    "style_system_prompt": (
                        "You are Victoria Blackwood. Write tense psychological thriller prose. "
                        "Use short sentences for tension. Plant subtle clues. Dark, atmospheric. "
                        "Unreliable narrator voice. Avoid adverbs. Show don't tell."
                    ),
                },
            },
            {
                "name": "Rosie Callahan",
                "niche_genre": "Cozy Mystery",
                "bio": (
                    "Rosie Callahan writes warm, witty cozy mysteries set in small-town America. "
                    "Her amateur sleuth series featuring bakery owner Millie Hart has a devoted "
                    "following of readers who love comfort reads with clever plots. "
                    "When not writing, Rosie bakes sourdough and tends her herb garden in Vermont."
                ),
                "writing_style_prompt": (
                    "Warm, cozy, witty prose. Charming small-town setting with vivid sensory details "
                    "(food smells, seasons, community). Amateur sleuth voice — curious and slightly "
                    "nosy but kind. Light humor. Clean romance subplot. Third-person limited past tense. "
                    "Think Diane Mott Davidson meets Joanne Fluke."
                ),
                "website_url": "https://rosiecallahan.com",
                "twitter_handle": "@RosieCozyMystery",
                "total_books_published": 5,
                "total_revenue_usd": Decimal("31250.00"),
                "style": {
                    "avg_sentence_length": 18.5,
                    "dialogue_ratio": 0.42,
                    "passive_voice_ratio": 0.05,
                    "adverb_frequency": 0.021,
                    "top_bigrams": ["smelled like", "small town", "can't help"],
                    "style_system_prompt": (
                        "You are Rosie Callahan. Write warm cozy mystery prose. "
                        "Rich sensory details. Charming characters. Light humor. "
                        "Third-person Millie's perspective. Comfort and community themes."
                    ),
                },
            },
            {
                "name": "James Harrow",
                "niche_genre": "Legal Thriller",
                "bio": (
                    "James Harrow is the pseudonym of a former criminal defense attorney who brings "
                    "unmatched authenticity to his courtroom thrillers. His novels feature flawed "
                    "lawyers navigating corrupt systems, explosive trials, and moral gray zones. "
                    "USA Today bestselling author."
                ),
                "writing_style_prompt": (
                    "Crisp, authoritative legal thriller prose. Courtroom scenes with authentic "
                    "procedure. Morally complex protagonist. Fast-paced chapters ending on hooks. "
                    "Male POV, first-person. Think Scott Turow meets John Grisham but grittier. "
                    "Legal jargon used accurately but explained naturally in context."
                ),
                "website_url": "https://jamesharrowbooks.com",
                "twitter_handle": "@JamesHarrowLegal",
                "total_books_published": 2,
                "total_revenue_usd": Decimal("9870.25"),
                "style": {
                    "avg_sentence_length": 16.8,
                    "dialogue_ratio": 0.35,
                    "passive_voice_ratio": 0.11,
                    "adverb_frequency": 0.009,
                    "top_bigrams": ["objection sustained", "your honor", "beyond doubt"],
                    "style_system_prompt": (
                        "You are James Harrow, former attorney. Write crisp legal thrillers. "
                        "Authentic courtroom procedure. Morally complex characters. "
                        "Hook every chapter ending. First-person male attorney POV."
                    ),
                },
            },
        ]

        if minimal:
            pen_name_data = pen_name_data[:1]

        created = []
        for data in pen_name_data:
            style_data = data.pop("style")
            pn, _ = PenName.objects.get_or_create(
                name=data["name"], defaults=data
            )
            # Create StyleFingerprint
            StyleFingerprint.objects.get_or_create(
                pen_name=pn,
                defaults={
                    "avg_sentence_length": style_data["avg_sentence_length"],
                    "dialogue_ratio": style_data["dialogue_ratio"],
                    "passive_voice_ratio": style_data["passive_voice_ratio"],
                    "adverb_frequency": style_data["adverb_frequency"],
                    "common_word_patterns": {
                        "sentence_starters": style_data["top_bigrams"],
                        "transitions": ["Meanwhile", "However", "Even so"],
                        "descriptive_patterns": ["the way she", "as if", "in the silence"],
                    },
                    "style_system_prompt": style_data["style_system_prompt"],
                    "chapters_analyzed": random.randint(5, 30),
                    "last_recalculated": timezone.now(),
                },
            )
            created.append(pn)

        self.stdout.write(f"  ✓ Pen names: {len(created)}")
        return created

    # =========================================================================
    # BOOKS
    # =========================================================================

    def _seed_books(self, pen_names, minimal=False):
        from novels.models import Book, BookLifecycleStatus

        pn_victoria = pen_names[0]
        pn_rosie = pen_names[1] if len(pen_names) > 1 else pen_names[0]
        pn_james = pen_names[2] if len(pen_names) > 2 else pen_names[0]

        now = timezone.now()

        books_data = [
            # Victoria Blackwood — Psychological Thriller
            {
                "title": "The Silent Witness",
                "subtitle": "A gripping psychological thriller with a shocking twist",
                "synopsis": (
                    "When forensic psychologist Dr. Claire Meadows is hired to evaluate the "
                    "sole witness to a brutal murder, she quickly realizes the witness knows "
                    "more than she's saying — and so does Claire's new client. As the trial "
                    "approaches, Claire uncovers a web of lies that implicates everyone she "
                    "trusted, including herself."
                ),
                "pen_name": pn_victoria,
                "hook": "What if the only witness to a murder is the killer herself?",
                "core_twist": "Claire's patient is her long-lost twin sister, who staged her own death 20 years ago.",
                "target_audience": "Women 30–55, fans of Gillian Flynn and Tana French",
                "comparable_titles": ["Gone Girl", "The Silent Patient", "Behind Closed Doors"],
                "lifecycle_status": BookLifecycleStatus.PUBLISHED_KDP,
                "asin": "B0CXTEST001",
                "bsr": 1842,
                "published_at": now - timedelta(days=65),
                "cover_image_url": "https://placehold.co/400x600/1a1a2e/ffffff?text=The+Silent+Witness",
                "amazon_url": "https://amazon.com/dp/B0CXTEST001",
                "current_price_usd": Decimal("3.99"),
                "ai_detection_score": 12.4,
                "plagiarism_score": 0.8,
                "total_revenue_usd": Decimal("8240.50"),
                "target_chapter_count": 45,
                "target_word_count": 75000,
                "current_word_count": 72400,
                "kdp_preflight_passed": True,
                "is_ai_generated_disclosure": True,
                "book_concepts": [
                    {
                        "title": "The Silent Witness",
                        "hook": "What if the only witness to a murder is the killer herself?",
                        "core_twist": "Twin sister staged her own death",
                        "comparable_titles": ["Gone Girl", "The Silent Patient"],
                    }
                ],
            },
            {
                "title": "Every Lie You Told",
                "subtitle": "A domestic thriller that keeps you guessing until the final page",
                "synopsis": (
                    "Marketing executive Nora Blake returns home for her parents' anniversary "
                    "and discovers her childhood home has been sold — with her family still inside. "
                    "As she digs into her parents' finances, she unravels a 30-year secret that "
                    "threatens to destroy everything she thought she knew about herself."
                ),
                "pen_name": pn_victoria,
                "hook": "Some family secrets were buried for a reason.",
                "core_twist": "Nora was adopted, and her biological mother is the woman her father is charged with killing.",
                "target_audience": "Women 25–50, domestic thriller readers",
                "comparable_titles": ["Big Little Lies", "The Woman in the Window", "The Couple Next Door"],
                "lifecycle_status": BookLifecycleStatus.WRITING_IN_PROGRESS,
                "cover_image_url": "https://placehold.co/400x600/2d1b69/ffffff?text=Every+Lie+You+Told",
                "current_price_usd": Decimal("0.99"),
                "ai_detection_score": 14.2,
                "plagiarism_score": 1.1,
                "total_revenue_usd": Decimal("0.00"),
                "target_chapter_count": 40,
                "target_word_count": 70000,
                "current_word_count": 28000,
                "kdp_preflight_passed": False,
                "is_ai_generated_disclosure": True,
            },
            {
                "title": "The Memory Thief",
                "subtitle": "A psychological thriller about identity, memory, and obsession",
                "synopsis": (
                    "Neuroscientist Dr. Maya Singh wakes in a hospital with no memory of the past "
                    "six months. The police say she murdered a colleague. Her husband says she's "
                    "been having an affair. Her therapist says she's suppressing trauma. "
                    "Maya must piece together who she was before she can prove who she is."
                ),
                "pen_name": pn_victoria,
                "hook": "She can't remember the crime. But her body does.",
                "core_twist": "Maya erased her own memory to protect herself from what she witnessed.",
                "target_audience": "Psychological thriller readers, medical mystery fans",
                "comparable_titles": ["Before I Go to Sleep", "The Girl on the Train", "Still Alice"],
                "lifecycle_status": BookLifecycleStatus.BIBLE_APPROVED,
                "cover_image_url": "https://placehold.co/400x600/0d0d0d/ffffff?text=The+Memory+Thief",
                "current_price_usd": None,
                "total_revenue_usd": Decimal("0.00"),
                "target_chapter_count": 42,
                "target_word_count": 72000,
                "current_word_count": 0,
                "kdp_preflight_passed": False,
                "is_ai_generated_disclosure": True,
            },

            # Rosie Callahan — Cozy Mystery
            {
                "title": "Murder at the Maple Syrup Festival",
                "subtitle": "A Millie Hart Bakery Mystery",
                "synopsis": (
                    "Maple Creek's annual syrup festival turns sour when town gossip "
                    "Harriet Pruitt is found dead in the sugar shack — face down in a vat of "
                    "maple syrup. Millie Hart, local bakery owner and reluctant amateur sleuth, "
                    "has 48 hours to unmask the killer before the festival ends and the suspect "
                    "disappears into the Vermont countryside."
                ),
                "pen_name": pn_rosie,
                "hook": "The sweetest small town is hiding a very bitter secret.",
                "core_twist": "The killer is the beloved festival organizer who has been embezzling from the town for years.",
                "target_audience": "Cozy mystery readers 35+, food mystery fans",
                "comparable_titles": ["Flipped Off", "Double Fudge", "Chocolate Chip Cookie Murder"],
                "lifecycle_status": BookLifecycleStatus.PUBLISHED_ALL,
                "asin": "B0CXTEST004",
                "bsr": 3241,
                "published_at": now - timedelta(days=120),
                "cover_image_url": "https://placehold.co/400x600/8B4513/fff8dc?text=Murder+at+Maple+Festival",
                "amazon_url": "https://amazon.com/dp/B0CXTEST004",
                "current_price_usd": Decimal("3.99"),
                "ai_detection_score": 9.8,
                "plagiarism_score": 0.5,
                "total_revenue_usd": Decimal("14210.00"),
                "target_chapter_count": 25,
                "target_word_count": 60000,
                "current_word_count": 58500,
                "kdp_preflight_passed": True,
                "is_ai_generated_disclosure": True,
                "book_concepts": [],
            },
            {
                "title": "Death by Peach Cobbler",
                "subtitle": "A Millie Hart Bakery Mystery Book 2",
                "synopsis": (
                    "When a big-city food critic arrives to review Millie's bakery and ends up "
                    "dead after eating the peach cobbler special, Millie finds herself at the "
                    "center of a poisoning investigation. She must clear her name — and figure "
                    "out what secret ingredient really killed him — before the health department "
                    "shuts her down for good."
                ),
                "pen_name": pn_rosie,
                "hook": "Someone didn't like Millie's cooking. Fatally.",
                "core_twist": "The critic wasn't poisoned by Millie's food — he was already dying, and someone used it as cover.",
                "target_audience": "Cozy mystery readers, food mystery fans",
                "comparable_titles": ["Double Fudge", "If Looks Could Chill", "Chocolate Chip Cookie Murder"],
                "lifecycle_status": BookLifecycleStatus.QA_REVIEW,
                "cover_image_url": "https://placehold.co/400x600/D2691E/fff8dc?text=Death+by+Peach+Cobbler",
                "current_price_usd": Decimal("0.99"),
                "ai_detection_score": 11.2,
                "plagiarism_score": 0.7,
                "total_revenue_usd": Decimal("0.00"),
                "target_chapter_count": 25,
                "target_word_count": 60000,
                "current_word_count": 57200,
                "kdp_preflight_passed": False,
                "is_ai_generated_disclosure": True,
            },

            # James Harrow — Legal Thriller
            {
                "title": "Reasonable Doubt",
                "subtitle": "A courtroom thriller where justice is anything but certain",
                "synopsis": (
                    "Defense attorney Jack Malone takes on an indefensible case: a teenage boy "
                    "found holding the murder weapon over his grandmother's body. The evidence is "
                    "overwhelming. The confession is damning. But Jack doesn't believe in "
                    "coincidences, and there are too many of them in this case."
                ),
                "pen_name": pn_james,
                "hook": "The guilty verdict is guaranteed. Unless Jack can find the impossible.",
                "core_twist": "The grandmother staged her own murder to frame the boy who exposed her as an FBI informant.",
                "target_audience": "Legal thriller readers, John Grisham fans 40–65",
                "comparable_titles": ["The Firm", "A Time to Kill", "The Lincoln Lawyer"],
                "lifecycle_status": BookLifecycleStatus.PUBLISHED_KDP,
                "asin": "B0CXTEST006",
                "bsr": 5821,
                "published_at": now - timedelta(days=45),
                "cover_image_url": "https://placehold.co/400x600/1a1a1a/c0c0c0?text=Reasonable+Doubt",
                "amazon_url": "https://amazon.com/dp/B0CXTEST006",
                "current_price_usd": Decimal("2.99"),
                "ai_detection_score": 16.8,
                "plagiarism_score": 1.3,
                "total_revenue_usd": Decimal("5430.75"),
                "target_chapter_count": 35,
                "target_word_count": 80000,
                "current_word_count": 79500,
                "kdp_preflight_passed": True,
                "is_ai_generated_disclosure": True,
                "book_concepts": [],
            },
            {
                "title": "The Verdict",
                "subtitle": "Some cases change everything",
                "synopsis": (
                    "Jack Malone is hired to overturn a 20-year-old wrongful conviction, but as "
                    "he digs into the original trial transcripts, he realizes the man in prison "
                    "may not be as innocent as his family claims — and the real killer may be "
                    "closer to home than anyone imagined."
                ),
                "pen_name": pn_james,
                "hook": "What if the man you're fighting to free is exactly where he belongs?",
                "core_twist": "The prisoner committed a different murder entirely — and Jack's own father prosecuted the original case knowing this.",
                "target_audience": "Legal thriller readers",
                "comparable_titles": ["The Innocent Man", "Wrongful Death", "The Confession"],
                "lifecycle_status": BookLifecycleStatus.KEYWORD_APPROVED,
                "cover_image_url": "https://placehold.co/400x600/2c2c2c/d4af37?text=The+Verdict",
                "current_price_usd": None,
                "total_revenue_usd": Decimal("0.00"),
                "target_chapter_count": 38,
                "target_word_count": 85000,
                "current_word_count": 0,
                "kdp_preflight_passed": False,
                "is_ai_generated_disclosure": True,
            },
        ]

        if minimal:
            books_data = books_data[:2]

        created = []
        for data in books_data:
            # Separate FSM field — set directly after creation
            status = data.pop("lifecycle_status")
            published_at = data.pop("published_at", None)

            book, _ = Book.objects.get_or_create(
                title=data["title"],
                pen_name=data["pen_name"],
                defaults={**data, "lifecycle_status": status},
            )
            if published_at:
                book.published_at = published_at
                book.save(update_fields=["published_at"])
            created.append(book)

        self.stdout.write(f"  ✓ Books: {len(created)}")
        return created

    # =========================================================================
    # KEYWORD RESEARCH
    # =========================================================================

    def _seed_keyword_research(self, books):
        from novels.models import KeywordResearch, BookLifecycleStatus

        eligible_statuses = {
            BookLifecycleStatus.KEYWORD_APPROVED,
            BookLifecycleStatus.DESCRIPTION_GENERATION,
            BookLifecycleStatus.DESCRIPTION_APPROVED,
            BookLifecycleStatus.BIBLE_GENERATION,
            BookLifecycleStatus.BIBLE_APPROVED,
            BookLifecycleStatus.WRITING_IN_PROGRESS,
            BookLifecycleStatus.QA_REVIEW,
            BookLifecycleStatus.EXPORT_READY,
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL,
        }

        count = 0
        for book in books:
            if book.lifecycle_status not in eligible_statuses:
                continue

            genre_kw = {
                "Psychological Thriller": {
                    "primary": [
                        {"keyword": "psychological thriller", "volume": 18500, "competition": "high"},
                        {"keyword": "domestic thriller books", "volume": 12000, "competition": "medium"},
                        {"keyword": "unreliable narrator thriller", "volume": 4200, "competition": "low"},
                        {"keyword": "dark psychological fiction", "volume": 8800, "competition": "medium"},
                        {"keyword": "suspense novels for women", "volume": 22000, "competition": "high"},
                    ],
                    "backend": [
                        "psychological suspense female protagonist",
                        "dark domestic thriller plot twist",
                        "unreliable narrator mystery",
                        "women in jeopardy thriller",
                        "tana french gillian flynn fans",
                        "female detective psychological",
                        "book club thriller discussion",
                    ],
                    "cat1": "Fiction > Thrillers & Suspense > Psychological",
                    "cat2": "Fiction > Mystery, Thriller & Suspense > Women Sleuths",
                },
                "Cozy Mystery": {
                    "primary": [
                        {"keyword": "cozy mystery books", "volume": 28000, "competition": "high"},
                        {"keyword": "bakery mystery novels", "volume": 9500, "competition": "medium"},
                        {"keyword": "small town mystery series", "volume": 15000, "competition": "high"},
                        {"keyword": "amateur sleuth mystery", "volume": 11000, "competition": "medium"},
                        {"keyword": "cozy mystery series women", "volume": 19000, "competition": "high"},
                    ],
                    "backend": [
                        "cozy mystery series amateur sleuth",
                        "food mystery bakery culinary",
                        "small town Vermont mystery",
                        "clean mystery no violence",
                        "female protagonist cozy",
                        "joanne fluke diane davidson fans",
                        "light mystery with recipes",
                    ],
                    "cat1": "Fiction > Mystery, Thriller & Suspense > Cozy",
                    "cat2": "Fiction > Mystery, Thriller & Suspense > Amateur Sleuths",
                },
                "Legal Thriller": {
                    "primary": [
                        {"keyword": "legal thriller novels", "volume": 14500, "competition": "high"},
                        {"keyword": "courtroom drama books", "volume": 9800, "competition": "medium"},
                        {"keyword": "lawyer thriller series", "volume": 6200, "competition": "medium"},
                        {"keyword": "wrongful conviction thriller", "volume": 4100, "competition": "low"},
                        {"keyword": "grisham fans legal fiction", "volume": 7800, "competition": "medium"},
                    ],
                    "backend": [
                        "courtroom legal thriller attorney",
                        "wrongful conviction innocence",
                        "defense lawyer criminal case",
                        "grisham turow fans legal fiction",
                        "law thriller plot twist ending",
                        "criminal justice corruption",
                        "trial drama suspense courtroom",
                    ],
                    "cat1": "Fiction > Thrillers & Suspense > Legal",
                    "cat2": "Fiction > Mystery, Thriller & Suspense > Hard-Boiled",
                },
            }

            genre = book.pen_name.niche_genre
            kw = genre_kw.get(genre, genre_kw["Psychological Thriller"])

            competitors = [
                {"asin": f"B0TEST{i:04d}", "title": f"Comparable Book {i}", "bsr": random.randint(500, 15000), "reviews": random.randint(50, 5000), "rating": round(random.uniform(3.8, 4.8), 1), "price": round(random.uniform(0.99, 4.99), 2)}
                for i in range(1, 6)
            ]

            KeywordResearch.objects.get_or_create(
                book=book,
                defaults={
                    "primary_keywords": kw["primary"],
                    "kdp_backend_keywords": kw["backend"],
                    "kdp_category_1": kw["cat1"],
                    "kdp_category_2": kw["cat2"],
                    "suggested_title": book.title,
                    "suggested_subtitle": book.subtitle or f"A {genre} Novel",
                    "competitor_asins": competitors,
                    "avg_competitor_reviews": sum(c["reviews"] for c in competitors) // len(competitors),
                    "avg_competitor_bsr": sum(c["bsr"] for c in competitors) // len(competitors),
                    "keyword_search_volume": {kw["primary"][0]["keyword"]: kw["primary"][0]["volume"]},
                    "is_approved": True,
                    "approved_at": timezone.now() - timedelta(days=random.randint(5, 90)),
                },
            )
            count += 1

        self.stdout.write(f"  ✓ Keyword research: {count}")

    # =========================================================================
    # BOOK DESCRIPTIONS
    # =========================================================================

    def _seed_book_descriptions(self, books):
        from novels.models import BookDescription, BookLifecycleStatus

        eligible = {
            BookLifecycleStatus.DESCRIPTION_APPROVED,
            BookLifecycleStatus.BIBLE_GENERATION,
            BookLifecycleStatus.BIBLE_APPROVED,
            BookLifecycleStatus.WRITING_IN_PROGRESS,
            BookLifecycleStatus.QA_REVIEW,
            BookLifecycleStatus.EXPORT_READY,
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL,
        }

        descriptions = {
            "The Silent Witness": {
                "A": {
                    "html": "<b>She heard everything. Said nothing. And now someone wants her dead.</b>\n\n"
                            "Forensic psychologist Dr. Claire Meadows thought she'd seen it all—until she's assigned "
                            "to evaluate the sole witness to a brutal murder. The witness is terrified. The evidence "
                            "is clear. And Claire's new client is hiding something.\n\n"
                            "As the trial approaches, Claire discovers that everyone involved knew the victim—including "
                            "herself. And the truth, once uncovered, will shatter the life she's spent two decades "
                            "building.\n\n"
                            "<em>Because the most dangerous secrets are the ones we keep from ourselves.</em>\n\n"
                            "<b>Perfect for fans of Tana French and Gillian Flynn. Download now and start reading in seconds.</b>",
                    "hook": "She heard everything. Said nothing. And now someone wants her dead.",
                },
                "B": {
                    "html": "<b>The witness knows who did it. She's not talking. And Claire Meadows is running out of time.</b>\n\n"
                            "A brutal murder. One witness. And a psychologist who can't stop asking the wrong questions.\n\n"
                            "Dr. Claire Meadows has built her career on reading people. She knows when someone is lying. "
                            "She knows when someone is scared. But she's never worked a case where the answers lead back "
                            "to her own front door.\n\n"
                            "With the trial just days away, Claire must choose: expose the truth and destroy "
                            "everything, or stay silent and let a killer walk free.\n\n"
                            "<em>No one is innocent in <b>The Silent Witness</b>.</em>\n\n"
                            "<b>Scroll up and grab your copy before the ending is spoiled for you.</b>",
                    "hook": "The witness knows who did it. She's not talking.",
                },
            },
            "Murder at the Maple Syrup Festival": {
                "A": {
                    "html": "<b>The sweetest small town in Vermont is hiding a very bitter secret.</b>\n\n"
                            "Millie Hart never wanted to be a detective. She just wanted to bake sourdough, chat with "
                            "her regulars, and get through the Maple Creek Annual Festival without incident. "
                            "Then she found Harriet Pruitt face-down in the sugar shack—and suddenly Millie's got "
                            "more on her hands than rising bread dough.\n\n"
                            "With 48 hours before the festival closes and every suspect packing up to leave, "
                            "Millie must sift through lies, maple syrup, and small-town gossip to find a killer "
                            "who's hiding in plain sight.\n\n"
                            "<em>In Maple Creek, everyone knows everyone. And everyone has something to hide.</em>\n\n"
                            "<b>Perfect for fans of Joanne Fluke and Diane Mott Davidson. A complete, satisfying mystery with a bonus scone recipe!</b>",
                    "hook": "The sweetest small town in Vermont is hiding a very bitter secret.",
                },
                "B": {
                    "html": "<b>Death never tasted so sweet.</b>\n\n"
                            "It's the most popular weekend in Maple Creek—and someone decided the festival's biggest gossip "
                            "would make a perfect murder victim.\n\n"
                            "Bakery owner Millie Hart didn't ask to find the body. She didn't ask to become the "
                            "town's unofficial detective. But when the local sheriff keeps arresting the wrong person, "
                            "Millie has no choice but to roll up her apron strings and start asking questions.\n\n"
                            "Questions that someone very powerful doesn't want answered.\n\n"
                            "<em>Murder at the Maple Syrup Festival: where the clues are as sweet as the syrup, and the killer is hiding in plain sight.</em>\n\n"
                            "<b>One-click to start this fast-paced cozy mystery today!</b>",
                    "hook": "Death never tasted so sweet.",
                },
            },
            "Reasonable Doubt": {
                "A": {
                    "html": "<b>Everyone says he's guilty. Jack Malone isn't so sure.</b>\n\n"
                            "Defense attorney Jack Malone has seen impossible cases. This isn't one—it's worse. "
                            "His client, a teenage boy, was found holding the murder weapon over his grandmother's body. "
                            "The confession is on tape. The jury is ready to convict.\n\n"
                            "But Jack doesn't believe in coincidences. And in 20 years of criminal law, "
                            "he's learned one thing: the most air-tight cases are usually the most carefully constructed lies.\n\n"
                            "<em>The truth is buried under 40 years of secrets. And someone will kill to keep it there.</em>\n\n"
                            "<b>For fans of John Grisham and Scott Turow. A legal thriller you won't be able to put down.</b>",
                    "hook": "Everyone says he's guilty. Jack Malone isn't so sure.",
                },
                "B": {
                    "html": "<b>The verdict is guaranteed. The evidence is perfect. That's exactly what worries him.</b>\n\n"
                            "Jack Malone has defended murderers, fraudsters, and worse. But he's never defended "
                            "someone this young, this frightened, or this obviously set up.\n\n"
                            "As Jack peels back the layers of a case that was designed to be airtight, "
                            "he uncovers a conspiracy that reaches from a small midwestern courtroom to the "
                            "highest levels of law enforcement—and lands squarely in his own past.\n\n"
                            "To save his client, Jack will have to do the one thing defense attorneys never do: "
                            "<em>tell the whole truth.</em>\n\n"
                            "<b>Download Reasonable Doubt and find out why lawyers make the most dangerous enemies.</b>",
                    "hook": "The verdict is guaranteed. The evidence is perfect. That worries him.",
                },
            },
        }

        count = 0
        for book in books:
            if book.lifecycle_status not in eligible:
                continue
            if book.title not in descriptions:
                continue

            for version, data in descriptions[book.title].items():
                BookDescription.objects.get_or_create(
                    book=book,
                    version=version,
                    defaults={
                        "description_html": data["html"],
                        "hook_line": data["hook"],
                        "is_active": (version == "A"),
                        "approved_at": timezone.now() - timedelta(days=random.randint(3, 80)),
                        "character_count": len(data["html"]),
                    },
                )
            count += 1

        self.stdout.write(f"  ✓ Book descriptions: {count} books")

    # =========================================================================
    # STORY BIBLES
    # =========================================================================

    def _seed_story_bibles(self, books):
        from novels.models import StoryBible, BookLifecycleStatus

        eligible = {
            BookLifecycleStatus.BIBLE_APPROVED,
            BookLifecycleStatus.WRITING_IN_PROGRESS,
            BookLifecycleStatus.QA_REVIEW,
            BookLifecycleStatus.EXPORT_READY,
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL,
        }

        bibles = {
            "The Silent Witness": {
                "characters": {
                    "protagonist": {
                        "name": "Dr. Claire Meadows",
                        "age": 42,
                        "occupation": "Forensic Psychologist",
                        "personality": "Analytical, empathetic but guarded, perfectionist. Hides emotional wounds behind professional competence.",
                        "wound": "Lost a patient to suicide 8 years ago. Carries guilt she's never processed.",
                        "goal": "Uncover the truth about the witness without destroying the case—or herself.",
                        "arc": "From hiding behind clinical detachment to confronting her own buried trauma.",
                    },
                    "antagonist": {
                        "name": "Lydia Haines (a.k.a. Dr. Sarah Meadows)",
                        "age": 42,
                        "occupation": "Art restorer",
                        "motivation": "Has been living in hiding for 20 years after escaping an abusive relationship. Will do anything to stay disappeared.",
                        "method": "Manipulation through partial truths. Uses Claire's empathy against her.",
                    },
                    "supporting": [
                        {"name": "Det. Marcus Webb", "role": "Lead detective, professional respect for Claire, complicated personal history"},
                        {"name": "Peter Meadows", "role": "Claire's ex-husband, knows a secret about her past"},
                        {"name": "Dr. Howard Kane", "role": "Victim, art dealer with criminal connections"},
                    ],
                },
                "world_rules": {
                    "setting": "Boston, Massachusetts — courtrooms, forensic labs, upscale art world",
                    "time_period": "Contemporary (2024)",
                    "key_locations": [
                        "Suffolk County Superior Court",
                        "Claire's therapy office (Beacon Hill)",
                        "Kane Gallery (Newbury Street)",
                        "Lydia's apartment (South End)",
                        "Claire's childhood home (Newton)",
                    ],
                    "atmosphere": "Tense, claustrophobic, paranoid. Autumn setting — grey skies, falling leaves symbolizing hidden pasts.",
                    "important_rules": [
                        "Claire cannot discuss case details outside formal settings — creates dramatic irony",
                        "Lydia has a tell: touches her left ear when lying",
                        "The twin connection is hinted at through identical mannerisms Claire notices subconsciously",
                    ],
                },
                "four_act_outline": {
                    "act_1_setup": {
                        "chapters": [1, 11],
                        "summary": "Claire is hired to evaluate witness Lydia Haines. She notices odd contradictions but attributes them to trauma. The murder case is introduced.",
                        "key_events": [
                            "Claire assigned to case (Ch 1)",
                            "First session with Lydia — odd resonance Claire can't explain (Ch 3)",
                            "Claire discovers victim Kane had criminal connections (Ch 8)",
                            "Inciting incident: Claire finds a photo that shouldn't exist (Ch 11)",
                        ],
                    },
                    "act_2_confrontation": {
                        "chapters": [12, 24],
                        "summary": "Claire digs into Lydia's background. Red herrings point to other suspects. Claire and Lydia develop uneasy connection.",
                        "key_events": [
                            "Background check on Lydia returns inconsistencies (Ch 14)",
                            "Claire confronted by Kane's business partner (Ch 17)",
                            "Claire's ex-husband warns her to drop the case (Ch 20)",
                            "Second clue: Lydia knows Claire's childhood nickname (Ch 24)",
                        ],
                    },
                    "act_3_complication": {
                        "chapters": [25, 37],
                        "summary": "Claire learns about her own adoption. The twin theory emerges but seems impossible. Another murder attempt on Lydia — or was it staged?",
                        "key_events": [
                            "Claire discovers she was adopted (Ch 27)",
                            "Hospital records reveal twin birth — one declared stillborn (Ch 31)",
                            "Lydia nearly killed in hit and run (Ch 34)",
                            "Claire finds Lydia's original identity documents (Ch 37)",
                        ],
                    },
                    "act_4_resolution": {
                        "chapters": [38, 45],
                        "summary": "Climactic confrontation. Lydia's truth revealed. Kane had been using Lydia's real identity to commit fraud — she killed him in self-defense. Justice and reunion.",
                        "key_events": [
                            "Lydia confesses — it was self-defense (Ch 39)",
                            "Claire presents evidence clearing Lydia (Ch 41)",
                            "Trial verdict (Ch 43)",
                            "Sisters' reunion — complicated but hopeful (Ch 45)",
                        ],
                    },
                },
                "timeline": [
                    {"day": 1, "event": "Kane's body discovered. Claire assigned to case.", "chapter_range": [1, 2]},
                    {"day": 5, "event": "First session with Lydia.", "chapter_range": [3, 4]},
                    {"day": 15, "event": "Claire finds childhood photo connection.", "chapter_range": [11, 12]},
                    {"day": 30, "event": "Background check contradictions emerge.", "chapter_range": [14, 15]},
                    {"day": 52, "event": "Claire discovers adoption records.", "chapter_range": [27, 28]},
                    {"day": 71, "event": "Trial begins.", "chapter_range": [38, 39]},
                    {"day": 78, "event": "Verdict and reunion.", "chapter_range": [43, 45]},
                ],
                "clues_tracker": [
                    {
                        "clue_id": "clue_001",
                        "description": "Lydia touches her left ear when saying she doesn't remember",
                        "planted_in_chapter": 3,
                        "revealed_in_chapter": 39,
                        "is_red_herring": False,
                        "connected_to": ["clue_004"],
                    },
                    {
                        "clue_id": "clue_002",
                        "description": "Kane's gallery had a hidden room — red herring suggesting criminal enterprise",
                        "planted_in_chapter": 8,
                        "revealed_in_chapter": 35,
                        "is_red_herring": True,
                        "connected_to": [],
                    },
                    {
                        "clue_id": "clue_003",
                        "description": "Lydia knows Claire's childhood nickname 'Cricket'",
                        "planted_in_chapter": 24,
                        "revealed_in_chapter": 39,
                        "is_red_herring": False,
                        "connected_to": ["clue_005"],
                    },
                ],
                "themes": ["Identity and selfhood", "Family secrets", "The price of silence", "Trauma and memory", "Justice vs. truth"],
                "tone": "Dark, tense, psychologically layered",
                "pov": "First Person",
                "tense": "Past",
                "summary_for_ai": (
                    "The Silent Witness follows forensic psychologist Claire Meadows (42, Boston, guarded but empathetic) "
                    "who discovers her evaluation subject, witness Lydia Haines, is her long-lost twin sister. "
                    "Protagonist wound: lost a patient to suicide 8 years ago. Core conflict: expose Lydia's identity "
                    "and destroy her safety, or suppress the truth. Antagonist: not truly villainous — Lydia killed "
                    "Kane in self-defense after 20 years of hiding from an abusive partner. Setting: Boston legal world, "
                    "autumn aesthetic, claustrophobic tension. Key clues: ear-touching tell, childhood nickname, photo. "
                    "Resolution: Claire presents self-defense evidence; twins reunite carefully."
                ),
            },
            "Murder at the Maple Syrup Festival": {
                "characters": {
                    "protagonist": {
                        "name": "Millicent 'Millie' Hart",
                        "age": 38,
                        "occupation": "Bakery owner (Hart's Sweet Shop)",
                        "personality": "Warm, curious, overly helpful. Chatty in a way that makes people confide. Struggles to say no.",
                        "wound": "Moved to Maple Creek after a painful divorce in Boston. Still rebuilding her confidence.",
                        "goal": "Clear the name of her friend Earl, who's been wrongly arrested.",
                        "arc": "Grows from someone who hides in her bakery to someone who takes up space in her community.",
                    },
                    "antagonist": {
                        "name": "Gordon Pruitt",
                        "age": 55,
                        "occupation": "Festival Organizer (Chair of Maple Creek Tourism Committee)",
                        "motivation": "Has been embezzling festival funds for 12 years. His wife Harriet discovered the accounts and threatened to expose him.",
                        "method": "Made the crime look like a random act during the chaos of the festival.",
                    },
                    "supporting": [
                        {"name": "Sheriff Dale Whitmore", "role": "Competent but stubborn. Focused on Earl. Millie's reluctant ally by Act 3."},
                        {"name": "Lou from the hardware store", "role": "Comic relief. Knows every secret in Maple Creek but speaks in riddles."},
                        {"name": "Chef Annika Sorensen", "role": "Red herring suspect. Feuded with Harriet for years over a recipe dispute."},
                    ],
                },
                "world_rules": {
                    "setting": "Maple Creek, Vermont — population 4,200",
                    "time_period": "October, contemporary",
                    "key_locations": [
                        "Hart's Sweet Shop (Main Street)",
                        "Maple Creek Fairgrounds",
                        "The Sugar Shack (crime scene)",
                        "Town Hall (festival HQ)",
                        "Lou's Hardware (gossip central)",
                    ],
                    "atmosphere": "Cozy, warm, autumnal. Smell of maple syrup and fresh bread everywhere. Secrets hide behind friendly smiles.",
                    "important_rules": [
                        "Everyone in Maple Creek knows everyone — this cuts both ways",
                        "Festival runs Friday–Sunday: Millie has exactly 48 hours",
                        "Gordon never raises his voice — his control is what makes him dangerous",
                    ],
                },
                "four_act_outline": {
                    "act_1_setup": {
                        "chapters": [1, 6],
                        "summary": "Festival opens. Millie wins Best Scone. Harriet is found dead. Earl arrested.",
                        "key_events": ["Festival opening (Ch 1)", "Harriet-Millie argument about judging (Ch 3)", "Body discovered (Ch 4)", "Earl arrested (Ch 6)"],
                    },
                    "act_2_confrontation": {
                        "chapters": [7, 14],
                        "summary": "Millie investigates. Red herrings: Annika's feud, the sugar shack co-op dispute, an insurance policy.",
                        "key_events": ["Millie finds festival accounts (Ch 9)", "Annika red herring (Ch 12)", "Lou drops cryptic clue (Ch 14)"],
                    },
                    "act_3_complication": {
                        "chapters": [15, 21],
                        "summary": "Gordon tries to shut Millie out. She finds the embezzlement trail. Gordon confronts her.",
                        "key_events": ["Embezzlement discovered in receipts (Ch 16)", "Gordon's threats escalate (Ch 19)", "Millie nearly runs off the road (Ch 21)"],
                    },
                    "act_4_resolution": {
                        "chapters": [22, 25],
                        "summary": "Millie presents evidence to Sheriff. Gordon arrested at the closing ceremony. Earl freed. Community celebrates.",
                        "key_events": ["Evidence to Sheriff (Ch 22)", "Gordon's arrest (Ch 24)", "Festival closes, Earl freed, pie-eating contest (Ch 25)"],
                    },
                },
                "timeline": [
                    {"day": 1, "event": "Festival opens. Best Scone contest. Harriet found dead.", "chapter_range": [1, 4]},
                    {"day": 2, "event": "Investigation. Red herrings. Festival continues.", "chapter_range": [5, 14]},
                    {"day": 3, "event": "Millie finds evidence. Confrontation. Resolution.", "chapter_range": [15, 25]},
                ],
                "clues_tracker": [
                    {"clue_id": "clue_001", "description": "Festival accounts show transfers to personal account", "planted_in_chapter": 9, "revealed_in_chapter": 22, "is_red_herring": False, "connected_to": []},
                    {"clue_id": "clue_002", "description": "Annika's feud with Harriet — seems like motive", "planted_in_chapter": 3, "revealed_in_chapter": 15, "is_red_herring": True, "connected_to": []},
                    {"clue_id": "clue_003", "description": "Gordon's shoes have maple syrup on the sole", "planted_in_chapter": 7, "revealed_in_chapter": 22, "is_red_herring": False, "connected_to": ["clue_001"]},
                ],
                "themes": ["Community and belonging", "Secrets in plain sight", "Rebuilding after loss", "Small town loyalty"],
                "tone": "Warm, cozy, light mystery with gentle tension",
                "pov": "Third Person Limited",
                "tense": "Past",
                "summary_for_ai": (
                    "Murder at the Maple Syrup Festival follows Millie Hart (38, bakery owner, Maple Creek VT) "
                    "investigating the death of town gossip Harriet Pruitt during the annual festival. "
                    "Killer: Gordon Pruitt (Harriet's husband, embezzler). Setting: cozy Vermont autumn festival. "
                    "Millie's wound: recovering from painful divorce. Her superpower: people confide in her over scones. "
                    "Key clues: festival accounts, maple syrup on Gordon's shoes. Red herring: Chef Annika's feud. "
                    "48-hour deadline before festival ends. Warm, community-focused tone throughout."
                ),
            },
        }

        count = 0
        for book in books:
            if book.lifecycle_status not in eligible:
                continue
            if book.title not in bibles:
                continue

            data = bibles[book.title]
            StoryBible.objects.get_or_create(
                book=book,
                defaults={
                    "characters": data["characters"],
                    "world_rules": data["world_rules"],
                    "four_act_outline": data["four_act_outline"],
                    "timeline": data["timeline"],
                    "clues_tracker": data["clues_tracker"],
                    "themes": data["themes"],
                    "tone": data["tone"],
                    "pov": data["pov"],
                    "tense": data["tense"],
                    "summary_for_ai": data["summary_for_ai"],
                },
            )
            count += 1

        self.stdout.write(f"  ✓ Story bibles: {count}")

    # =========================================================================
    # CHAPTERS
    # =========================================================================

    def _seed_chapters(self, books, minimal=False):
        from novels.models import Chapter, ChapterStatus, BookLifecycleStatus

        needs_chapters = {
            BookLifecycleStatus.WRITING_IN_PROGRESS,
            BookLifecycleStatus.QA_REVIEW,
            BookLifecycleStatus.EXPORT_READY,
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL,
        }

        CHAPTER_CONFIGS = {
            "The Silent Witness": [
                ("The Last Session", ChapterStatus.PUBLISHED, True),
                ("A Familiar Stranger", ChapterStatus.PUBLISHED, True),
                ("What the Files Don't Say", ChapterStatus.PUBLISHED, True),
                ("The Photo", ChapterStatus.PUBLISHED, True),
                ("Dead Ends", ChapterStatus.PUBLISHED, True),
                ("The Adoption Notice", ChapterStatus.APPROVED, True),
                ("Lydia's Lie", ChapterStatus.APPROVED, False),
                ("The Earl of Evidence", ChapterStatus.APPROVED, False),
                ("Two Truths", ChapterStatus.PENDING_QA, False),
                ("The Ear Touch", ChapterStatus.PENDING_QA, False),
                ("Cricket", ChapterStatus.WRITTEN, False),
                ("What Sisters Know", ChapterStatus.WRITTEN, False),
            ],
            "Every Lie You Told": [
                ("Home Again", ChapterStatus.PUBLISHED, True),
                ("The Sale", ChapterStatus.PUBLISHED, True),
                ("Thirty Years", ChapterStatus.APPROVED, True),
                ("The Safe Deposit", ChapterStatus.APPROVED, False),
                ("Dad's Lawyer", ChapterStatus.PENDING_QA, False),
                ("Paper Trail", ChapterStatus.WRITTEN, False),
                ("What the Neighbours Saw", ChapterStatus.WRITTEN, False),
                ("Nora's Real Name", ChapterStatus.READY_TO_WRITE, False),
                ("The Biological Connection", ChapterStatus.READY_TO_WRITE, False),
                ("Confrontation", ChapterStatus.PENDING, False),
            ],
            "Murder at the Maple Syrup Festival": [
                ("Opening Day", ChapterStatus.PUBLISHED, True),
                ("The Best Scone in Vermont", ChapterStatus.PUBLISHED, True),
                ("Sweet and Sour", ChapterStatus.PUBLISHED, True),
                ("The Sugar Shack", ChapterStatus.PUBLISHED, True),
                ("Earl in Handcuffs", ChapterStatus.PUBLISHED, True),
                ("Gossip and Gravy", ChapterStatus.PUBLISHED, True),
                ("The Festival Accounts", ChapterStatus.PUBLISHED, False),
                ("Annika's Alibi", ChapterStatus.PUBLISHED, False),
                ("Syrup on the Shoes", ChapterStatus.PUBLISHED, False),
                ("Lou Knows", ChapterStatus.PUBLISHED, False),
                ("Gordon's Warning", ChapterStatus.PUBLISHED, False),
                ("The Empty Vat", ChapterStatus.PUBLISHED, False),
                ("Millie's List", ChapterStatus.PUBLISHED, False),
                ("Almost Run Off the Road", ChapterStatus.PUBLISHED, False),
                ("Sheriff Finally Listens", ChapterStatus.PUBLISHED, False),
                ("Gordon Pruitt's Accounting Error", ChapterStatus.PUBLISHED, False),
                ("The Longest Sunday", ChapterStatus.PUBLISHED, False),
                ("Closing Ceremony", ChapterStatus.PUBLISHED, False),
                ("Earl Eats His Weight in Pie", ChapterStatus.PUBLISHED, False),
                ("Next Year", ChapterStatus.PUBLISHED, False),
            ],
            "Death by Peach Cobbler": [
                ("The Critic Arrives", ChapterStatus.APPROVED, False),
                ("Five Stars or Zero", ChapterStatus.APPROVED, False),
                ("Peach Cobbler at Dawn", ChapterStatus.APPROVED, False),
                ("Dead Critic", ChapterStatus.APPROVED, False),
                ("The Coroner's Surprise", ChapterStatus.PENDING_QA, False),
                ("Pre-existing Conditions", ChapterStatus.PENDING_QA, False),
                ("Who Wanted Him Dead", ChapterStatus.WRITTEN, False),
                ("Health Inspector", ChapterStatus.WRITTEN, False),
                ("The Real Poison", ChapterStatus.REJECTED, False),
                ("Millie Digs Deeper", ChapterStatus.READY_TO_WRITE, False),
            ],
            "Reasonable Doubt": [
                ("Jack Takes the Case", ChapterStatus.PUBLISHED, True),
                ("The Confession Tape", ChapterStatus.PUBLISHED, True),
                ("Something Wrong", ChapterStatus.PUBLISHED, True),
                ("Old Records, New Questions", ChapterStatus.PUBLISHED, True),
                ("The Grandmother's Will", ChapterStatus.PUBLISHED, True),
                ("A Planted Weapon", ChapterStatus.PUBLISHED, True),
                ("Jack's Father", ChapterStatus.PUBLISHED, False),
                ("The FBI Connection", ChapterStatus.PUBLISHED, False),
                ("The Informant", ChapterStatus.PUBLISHED, False),
                ("What Really Happened", ChapterStatus.PUBLISHED, False),
                ("The Defense Rests", ChapterStatus.PUBLISHED, False),
                ("Verdict", ChapterStatus.PUBLISHED, False),
                ("Aftermath", ChapterStatus.PUBLISHED, False),
            ],
        }

        sample_content = {
            "opening": (
                "The call came at 7:14 on a Tuesday morning, which meant Claire was already on her second espresso "
                "and halfway through the Hendricks evaluation notes when Dr. Peterson's name lit up her phone. "
                "She almost didn't answer. Peterson only called when he needed something uncomfortable.\n\n"
                "\"There's a case,\" he said, before she could get through hello. \"Witness evaluation. "
                "Suffolk County. They need someone with your specific background.\"\n\n"
                "Claire set down the espresso. \"My background meaning trauma specialization, or my background meaning "
                "I'm the only person in Boston who owes you a favor?\"\n\n"
                "A pause that told her everything. \"Both,\" he said. \"Can you be downtown by nine?\""
            ),
            "middle": (
                "Lydia Haines sat with her hands folded in her lap in the precise way that Claire had seen a hundred "
                "times — the way people sat when they were performing calm. The session room smelled of lavender and "
                "stale coffee, which Claire had always found an honest combination.\n\n"
                "\"Let's talk about what you remember from that evening,\" Claire said.\n\n"
                "Lydia's left hand moved to her ear. A small gesture. Absent. Claire noted it without moving her pen.\n\n"
                "\"I don't remember much.\" The words came out smooth, rehearsed. \"It was dark. I was frightened.\"\n\n"
                "\"Of course.\" Claire kept her voice neutral. \"What specifically frightened you?\"\n\n"
                "The pause lasted half a breath too long. \"Everything,\" Lydia said finally. \"Everything frightened me.\"\n\n"
                "Claire wrote nothing on her notepad. She was watching the way Lydia's eyes tracked to the window "
                "whenever she wasn't quite telling the truth."
            ),
        }

        total = 0
        for book in books:
            if book.lifecycle_status not in needs_chapters:
                continue
            if book.title not in CHAPTER_CONFIGS:
                continue

            chapters = CHAPTER_CONFIGS[book.title]
            if minimal:
                chapters = chapters[:5]

            for i, (title, ch_status, is_published) in enumerate(chapters, 1):
                content = ""
                if ch_status in {ChapterStatus.WRITTEN, ChapterStatus.PENDING_QA,
                                  ChapterStatus.APPROVED, ChapterStatus.PUBLISHED, ChapterStatus.REJECTED}:
                    content = sample_content["opening"] if i == 1 else sample_content["middle"]

                brief = {
                    "opening_hook": f"Chapter {i} opens with a pivotal confrontation that raises the stakes.",
                    "key_events": [
                        f"Event A: protagonist discovers new information",
                        f"Event B: relationship dynamic shifts",
                        f"Event C: tension escalates toward next chapter",
                    ],
                    "ending_hook": "Ends on a revelation that recontextualises everything the reader knows.",
                    "mood": "Tense" if book.pen_name.niche_genre == "Psychological Thriller" else "Warm",
                    "pov_character": "Claire Meadows" if "Thriller" in book.pen_name.niche_genre else "Millie Hart",
                }

                chapter, _ = Chapter.objects.get_or_create(
                    book=book,
                    chapter_number=i,
                    defaults={
                        "title": title,
                        "status": ch_status,
                        "is_published": is_published,
                        "content": content,
                        "brief": brief,
                        "word_count": len(content.split()) if content else 0,
                        "generation_model": "llama3" if content else "",
                        "generation_cost_usd": round(random.uniform(0.001, 0.005), 4) if content else 0,
                        "generation_tokens_used": random.randint(800, 1200) if content else 0,
                        "qa_notes": "Pacing is too slow in the middle section. Strengthen the ending hook." if ch_status == ChapterStatus.REJECTED else "",
                    },
                )
                total += 1

        self.stdout.write(f"  ✓ Chapters: {total}")

    # =========================================================================
    # PRICING
    # =========================================================================

    def _seed_pricing(self, books):
        from novels.models import PricingStrategy, PricingPhase, BookLifecycleStatus

        eligible = {
            BookLifecycleStatus.PUBLISHED_KDP,
            BookLifecycleStatus.PUBLISHED_ALL,
            BookLifecycleStatus.QA_REVIEW,
            BookLifecycleStatus.EXPORT_READY,
        }

        pricing_map = {
            "The Silent Witness": {
                "current_phase": PricingPhase.MATURE,
                "current_price_usd": Decimal("3.99"),
                "price_history": [
                    {"date": (date.today() - timedelta(days=65)).isoformat(), "price": 0.99, "phase": "launch", "reason": "Launch pricing"},
                    {"date": (date.today() - timedelta(days=51)).isoformat(), "price": 2.99, "phase": "growth", "reason": "20 reviews reached"},
                    {"date": (date.today() - timedelta(days=30)).isoformat(), "price": 3.99, "phase": "mature", "reason": "Stable BSR < 5000"},
                ],
                "is_kdp_select": True,
                "last_promotion_date": date.today() - timedelta(days=30),
                "next_promotion_date": date.today() + timedelta(days=60),
            },
            "Murder at the Maple Syrup Festival": {
                "current_phase": PricingPhase.MATURE,
                "current_price_usd": Decimal("3.99"),
                "price_history": [
                    {"date": (date.today() - timedelta(days=120)).isoformat(), "price": 0.99, "phase": "launch", "reason": "Launch"},
                    {"date": (date.today() - timedelta(days=100)).isoformat(), "price": 2.99, "phase": "growth", "reason": "Review threshold"},
                    {"date": (date.today() - timedelta(days=75)).isoformat(), "price": 3.99, "phase": "mature", "reason": "BSR stabilized"},
                ],
                "is_kdp_select": True,
                "last_promotion_date": date.today() - timedelta(days=45),
                "next_promotion_date": date.today() + timedelta(days=45),
            },
            "Reasonable Doubt": {
                "current_phase": PricingPhase.GROWTH,
                "current_price_usd": Decimal("2.99"),
                "price_history": [
                    {"date": (date.today() - timedelta(days=45)).isoformat(), "price": 0.99, "phase": "launch", "reason": "Launch"},
                    {"date": (date.today() - timedelta(days=25)).isoformat(), "price": 2.99, "phase": "growth", "reason": "Review threshold"},
                ],
                "is_kdp_select": True,
                "last_promotion_date": None,
                "next_promotion_date": date.today() + timedelta(days=75),
            },
            "Death by Peach Cobbler": {
                "current_phase": PricingPhase.LAUNCH,
                "current_price_usd": Decimal("0.99"),
                "price_history": [],
                "is_kdp_select": True,
                "last_promotion_date": None,
                "next_promotion_date": None,
            },
        }

        count = 0
        for book in books:
            if book.lifecycle_status not in eligible:
                continue
            pdata = pricing_map.get(book.title)
            if not pdata:
                pdata = {
                    "current_phase": PricingPhase.LAUNCH,
                    "current_price_usd": Decimal("0.99"),
                    "price_history": [],
                    "is_kdp_select": True,
                    "last_promotion_date": None,
                    "next_promotion_date": None,
                }

            PricingStrategy.objects.get_or_create(
                book=book,
                defaults={
                    "current_phase": pdata["current_phase"],
                    "current_price_usd": pdata["current_price_usd"],
                    "price_history": pdata["price_history"],
                    "is_kdp_select": pdata["is_kdp_select"],
                    "last_promotion_date": pdata["last_promotion_date"],
                    "next_promotion_date": pdata["next_promotion_date"],
                    "days_between_promotions": 90,
                    "auto_price_enabled": True,
                    "reviews_threshold_for_growth": 20,
                    "days_in_launch_phase": 7,
                },
            )
            count += 1

        self.stdout.write(f"  ✓ Pricing strategies: {count}")

    # =========================================================================
    # ADS PERFORMANCE
    # =========================================================================

    def _seed_ads(self, books):
        from novels.models import AdsPerformance, BookLifecycleStatus

        eligible = {BookLifecycleStatus.PUBLISHED_KDP, BookLifecycleStatus.PUBLISHED_ALL}
        count = 0

        genre_kw_map = {
            "Psychological Thriller": ["psychological thriller", "domestic thriller", "gillian flynn fans", "dark suspense novels"],
            "Cozy Mystery": ["cozy mystery", "bakery mystery", "small town mystery", "joanne fluke fans"],
            "Legal Thriller": ["legal thriller", "courtroom drama", "john grisham fans", "lawyer mystery"],
        }

        for book in books:
            if book.lifecycle_status not in eligible:
                continue

            kws = genre_kw_map.get(book.pen_name.niche_genre, ["thriller books"])
            days = 30 if book.lifecycle_status == BookLifecycleStatus.PUBLISHED_ALL else 14

            for d in range(days, 0, -1):
                report_date = date.today() - timedelta(days=d)
                impressions = random.randint(2000, 8000)
                clicks = int(impressions * random.uniform(0.003, 0.015))
                spend = round(clicks * random.uniform(0.18, 0.55), 2)
                sales = round(spend / random.uniform(0.2, 0.6), 2)
                acos = round((spend / sales * 100) if sales > 0 else 0, 1)
                ctr = round((clicks / impressions * 100), 3)

                top_kws = [
                    {
                        "keyword": kws[i % len(kws)],
                        "impressions": random.randint(200, 1500),
                        "clicks": random.randint(2, 25),
                        "sales": round(random.uniform(0, 15), 2),
                        "acos": round(random.uniform(15, 65), 1),
                    }
                    for i in range(3)
                ]
                to_pause = [k for k in top_kws if k["acos"] > 65]

                AdsPerformance.objects.get_or_create(
                    book=book,
                    report_date=report_date,
                    defaults={
                        "impressions": impressions,
                        "clicks": clicks,
                        "spend_usd": Decimal(str(spend)),
                        "sales_usd": Decimal(str(sales)),
                        "acos": acos,
                        "ctr": ctr,
                        "cpc": Decimal(str(round(spend / clicks, 2))) if clicks > 0 else None,
                        "top_keywords": top_kws,
                        "keywords_to_pause": to_pause,
                    },
                )
                count += 1

        self.stdout.write(f"  ✓ Ads performance records: {count}")

    # =========================================================================
    # REVIEWS
    # =========================================================================

    def _seed_reviews(self, books):
        from novels.models import ReviewTracker, BookLifecycleStatus

        eligible = {BookLifecycleStatus.PUBLISHED_KDP, BookLifecycleStatus.PUBLISHED_ALL}

        # ReviewTracker is OneToOneField — one aggregate record per book.
        genre_data = {
            "Psychological Thriller": {
                "total_reviews": 142,
                "avg_rating": 4.6,
                "reviews_week_1": 38,
                "reviews_week_2": 42,
                "reviews_week_3": 28,
                "reviews_week_4": 18,
                "positive_themes": ["gripping pace", "unexpected twist", "complex characters", "atmospheric writing", "unreliable narrator done well"],
                "negative_themes": ["slow middle section", "predictable twist for genre veterans"],
                "arc_emails_sent": 25,
                "arc_reviews_received": 18,
                "arc_conversion_rate": 72.0,
                "rating_distribution": {"5": 89, "4": 35, "3": 12, "2": 4, "1": 2},
                "last_scraped": timezone.now() - timedelta(days=1),
            },
            "Cozy Mystery": {
                "total_reviews": 218,
                "avg_rating": 4.7,
                "reviews_week_1": 52,
                "reviews_week_2": 61,
                "reviews_week_3": 48,
                "reviews_week_4": 35,
                "positive_themes": ["charming characters", "Vermont setting", "cozy atmosphere", "fun mystery", "great for book clubs"],
                "negative_themes": ["killer somewhat predictable", "pacing slow in act 2"],
                "arc_emails_sent": 30,
                "arc_reviews_received": 24,
                "arc_conversion_rate": 80.0,
                "rating_distribution": {"5": 145, "4": 52, "3": 14, "2": 5, "1": 2},
                "last_scraped": timezone.now() - timedelta(days=1),
            },
            "Legal Thriller": {
                "total_reviews": 87,
                "avg_rating": 4.4,
                "reviews_week_1": 28,
                "reviews_week_2": 31,
                "reviews_week_3": 18,
                "reviews_week_4": 10,
                "positive_themes": ["authentic legal detail", "great protagonist", "fast-paced", "unexpected ending"],
                "negative_themes": ["middle drags slightly", "some legal jargon heavy"],
                "arc_emails_sent": 20,
                "arc_reviews_received": 14,
                "arc_conversion_rate": 70.0,
                "rating_distribution": {"5": 48, "4": 27, "3": 8, "2": 3, "1": 1},
                "last_scraped": timezone.now() - timedelta(days=2),
            },
        }

        count = 0
        for book in books:
            if book.lifecycle_status not in eligible:
                continue
            genre = book.pen_name.niche_genre
            data = genre_data.get(genre, genre_data["Psychological Thriller"])

            ReviewTracker.objects.get_or_create(
                book=book,
                defaults=data,
            )
            count += 1

        self.stdout.write(f"  ✓ Review trackers: {count}")

    # =========================================================================
    # ARC READERS
    # =========================================================================

    def _seed_arc_readers(self, pen_names):
        from novels.models import ARCReader

        arc_data = [
            ("Elena Marchetti", "elena.marchetti@bookclub.com", "Psychological Thriller,Domestic Thriller", 4.8, 12, True),
            ("Sandra Beaumont", "sandra.b.reads@gmail.com", "Cozy Mystery,Culinary Mystery,Comfort Read", 4.6, 8, True),
            ("Donna Fitzgerald", "dfitz.reader@outlook.com", "Legal Thriller,Courtroom Drama", 4.9, 5, True),
            ("Rebecca Okonkwo", "becca.bookworm@gmail.com", "Psychological Thriller,Suspense,Literary Fiction", 4.7, 15, True),
            ("Linda Park", "lindapark.reads@yahoo.com", "Cozy Mystery,Romance,Light Mystery", 4.4, 21, True),
            ("Thomas Harker", "t.harker@readersgroup.org", "Legal Thriller,Crime,Thriller", 4.5, 9, True),
            ("Carla Winters", "c.winters.books@gmail.com", "Psychological Thriller,Dark Fiction", 4.2, 3, True),
            ("June Crawford", "jcrawford.arc@gmail.com", "Cozy Mystery,Historical Mystery", 3.9, 7, False),
        ]

        count = 0

        for name, email, genres, _reliability, reviews_given, is_reliable in arc_data:
            # genres is a comma-separated string — store as list
            genres_list = [g.strip() for g in genres.split(",")]
            unreliable_count = 2 if not is_reliable else 0
            ARCReader.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "genres_interested": genres_list,
                    "reviews_left_count": reviews_given,
                    "arc_copies_received": reviews_given + unreliable_count,
                    "avg_rating_given": round(random.uniform(3.8, 5.0), 1),
                    "is_reliable": is_reliable,
                    "unreliable_count": unreliable_count,
                    "notes": "Leaves detailed, helpful reviews consistently." if is_reliable else "Has missed review deadlines twice.",
                },
            )
            count += 1

        self.stdout.write(f"  ✓ ARC readers: {count}")

    # =========================================================================
    # COMPETITOR BOOKS
    # =========================================================================

    def _seed_competitor_books(self, books):
        from novels.models import CompetitorBook, BookLifecycleStatus

        eligible = {BookLifecycleStatus.PUBLISHED_KDP, BookLifecycleStatus.PUBLISHED_ALL}
        competitors_data = {
            "Psychological Thriller": [
                ("The Silent Patient", "Alex Michaelides", "B07S3ZHHHZ", 1, 89000, 4.5, 3.99),
                ("Gone Girl", "Gillian Flynn", "B0088ZB8NG", 3, 125000, 3.9, 7.99),
                ("Behind Closed Doors", "B. A. Paris", "B01GXXCIXO", 28, 45000, 3.7, 6.99),
                ("The Woman in the Window", "A.J. Finn", "B076CLHRGM", 45, 38000, 3.7, 6.99),
            ],
            "Cozy Mystery": [
                ("Chocolate Chip Cookie Murder", "Joanne Fluke", "B000FC2N30", 850, 12000, 4.4, 7.99),
                ("Double Fudge", "Joanne Fluke", "B000YDXXM2", 1200, 8000, 4.3, 7.99),
                ("If Looks Could Chill", "Diane Mott Davidson", "B003JBFVCK", 2100, 5500, 4.2, 6.99),
            ],
            "Legal Thriller": [
                ("The Firm", "John Grisham", "B000FCKIDM", 120, 95000, 4.4, 9.99),
                ("A Time to Kill", "John Grisham", "B000FCKK7C", 250, 75000, 4.5, 9.99),
                ("The Lincoln Lawyer", "Michael Connelly", "B000GCFEK0", 450, 55000, 4.4, 8.99),
            ],
        }

        count = 0
        seen_asins = set()
        for book in books:
            if book.lifecycle_status not in eligible:
                continue
            genre = book.pen_name.niche_genre
            for ctitle, cauthor, casin, cbsr, creviews, crating, cprice in competitors_data.get(genre, []):
                if casin in seen_asins:
                    continue
                seen_asins.add(casin)
                CompetitorBook.objects.get_or_create(
                    asin=casin,
                    defaults={
                        "title": ctitle,
                        "author": cauthor,
                        "bsr": cbsr,
                        "review_count": creviews,
                        "avg_rating": crating,
                        "price_usd": Decimal(str(cprice)),
                        "genre": genre,
                        "estimated_monthly_revenue": Decimal(str(round(cprice * min(creviews, 500) * 0.05, 2))),
                    },
                )
                count += 1

        self.stdout.write(f"  ✓ Competitor books: {count}")

    # =========================================================================
    # SUBSCRIPTIONS & PURCHASES
    # =========================================================================

    def _seed_subscriptions(self, users):
        from novels.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus, ChapterPurchase
        from novels.models import Chapter

        plans = [
            (SubscriptionPlan.MONTHLY, SubscriptionStatus.ACTIVE, "cus_test_001", "sub_test_001"),
            (SubscriptionPlan.ANNUAL, SubscriptionStatus.ACTIVE, "cus_test_002", "sub_test_002"),
            (SubscriptionPlan.FREE, SubscriptionStatus.ACTIVE, "", ""),
            (SubscriptionPlan.MONTHLY, SubscriptionStatus.CANCELED, "cus_test_004", "sub_test_004"),
        ]

        count = 0
        for i, user in enumerate(users):
            plan, status, cus_id, sub_id = plans[i % len(plans)]
            sub, created = Subscription.objects.get_or_create(
                user=user,
                defaults={
                    "plan": plan,
                    "status": status,
                    "stripe_customer_id": cus_id,
                    "stripe_subscription_id": sub_id,
                    "current_period_start": timezone.now() - timedelta(days=15),
                    "current_period_end": timezone.now() + timedelta(days=15),
                },
            )
            if created:
                count += 1

        # Seed chapter purchases for free users
        free_user = users[2] if len(users) > 2 else users[0]
        pub_chapters = Chapter.objects.filter(is_published=True).order_by("?")[:3]
        for ch in pub_chapters:
            ChapterPurchase.objects.get_or_create(
                user=free_user,
                chapter=ch,
                defaults={
                    "price_usd": Decimal("1.99"),
                    "stripe_payment_intent_id": f"pi_test_{ch.id:06d}",
                },
            )

        self.stdout.write(f"  ✓ Subscriptions: {count} created")

    # =========================================================================
    # DISTRIBUTION CHANNELS
    # =========================================================================

    def _seed_distribution(self, books):
        from novels.models import DistributionChannel, DistributionPlatform, BookLifecycleStatus

        eligible = {BookLifecycleStatus.PUBLISHED_KDP, BookLifecycleStatus.PUBLISHED_ALL}

        platforms = [
            (DistributionPlatform.KDP, 0.70),
            (DistributionPlatform.DRAFT2DIGITAL, 0.60),
            (DistributionPlatform.WEBSITE, 0.95),
        ]

        count = 0
        for book in books:
            if book.lifecycle_status not in eligible:
                continue
            for platform, royalty in platforms:
                units = random.randint(50, 500)
                revenue = round(units * float(book.current_price_usd or 3.99) * royalty, 2) if book.current_price_usd else 0
                DistributionChannel.objects.get_or_create(
                    book=book,
                    platform=platform,
                    defaults={
                        "royalty_rate": royalty,
                        "units_sold": units,
                        "revenue_usd": Decimal(str(revenue)),
                        "is_active": True,
                        "published_at": timezone.now() - timedelta(days=random.randint(5, 120)),
                    },
                )
                count += 1

        self.stdout.write(f"  ✓ Distribution channels: {count}")
