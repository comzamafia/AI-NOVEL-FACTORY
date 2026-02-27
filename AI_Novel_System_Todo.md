# Project Requirements & Todo List: AI Novel Factory System
> **Version 2.0** — Updated with Full Feature Set (Original + Strategic Additions)
> Last Updated: 2026-02 (All Phases ✅ Complete — Backend + Frontend + Tests + Docker + CI/CD + Flower + Rate limiting + DB Backup + Staging/Prod configs)

---

## 📌 Project Overview
ระบบ Web Application สำหรับผลิตและขายนิยายแบบอัตโนมัติ (Zero-Touch Automation) โดยใช้ AI ในการวิเคราะห์ตลาด, วางโครงเรื่อง, เขียนเนื้อหา, ตรวจสอบคุณภาพ และจัดรูปเล่ม ระบบออกแบบมาเพื่อรองรับการสร้าง "นามปากกา" (Pen Name) หลายคนเพื่อทำหน้าที่เสมือนสำนักพิมพ์ (Publishing House) และมีหน้าร้าน (Storefront) สำหรับขายนิยายแบบ Chapter-by-Chapter พร้อมระบบป้องกันความเสี่ยงด้านลิขสิทธิ์และกฎของ Amazon KDP

---

## 🛠️ Tech Stack Requirements

- **Backend:** Python, Django, Django Rest Framework (DRF)
- **Background Workers:** Celery + Redis
- **Database:** PostgreSQL
- **Frontend (Admin & Storefront):** Next.js (React), Tailwind CSS
- **State Machine:** django-fsm (BookLifecycle)
- **Integrations:** Gemini API, Stripe API, Copyscape, Originality.ai, Amazon Advertising API, DataForSEO

---

## 🗂️ Database Models — Full Schema ✅

- [x] PenName, Book (with BookLifecycleStatus FSM), StoryBible, Chapter, Subscription
- [x] KeywordResearch, BookDescription, PricingStrategy, AdsPerformance
- [x] ReviewTracker, ARCReader, DistributionChannel, CompetitorBook, StyleFingerprint
- [x] BookLifecycle State Machine (13 states: concept_pending → archived)

---

## 📝 Phase 1: Project Setup & Core Infrastructure ✅

- [x] Setup Django project + DRF + PostgreSQL
- [x] Configure Celery + Redis for async tasks
- [x] Install django-fsm + implement BookLifecycle State Machine
- [x] Create all Database Models (Core + New models)
- [x] Setup Django Admin for all Models
- [x] Configure Celery Beat for Scheduled tasks
- [x] Setup environment variables for all API Keys
- [x] Setup logging and error tracking

---

## 🔍 Phase 2: Amazon Keyword Research & SEO Engine ✅

### 2.1 Keyword Data Collection ✅
- [x] AmazonKeywordService class
- [x] DataForSEO/ScraperAPI integration (search volume, BSR titles, competitor ASINs)
- [x] Celery Task run_keyword_research(book_id)
- [x] AI keyword cluster analysis of Top 20 bestsellers

### 2.2 KDP SEO Optimization ✅
- [x] generate_kdp_metadata(book_id) — AI generates title/subtitle/7 backend keywords/2 categories
- [x] Validation rules (no forbidden words, char limits)

### 2.3 Admin UI — Keyword Approval Page ✅
- [x] /admin/books/{id}/keywords/ with suggested title, keywords, competitor table, categories
- [x] Admin editable + Approve → lifecycle = keyword_approved

---

## 🧠 Phase 3: Idea & Strategy Engine ✅

- [x] ScraperAPI for Amazon Bestseller data
- [x] AI generates 3 Book Concepts (Title, Hook, Core Twist)
- [x] Admin UI: Approve Concept → trigger Keyword Research

---

## 📝 Phase 4: Book Description (Blurb) Generator ✅

- [x] Celery Task generate_book_description(book_id) — HOOK/SETUP/STAKES/TWIST/CTA formula
- [x] A/B Versions auto-generated with different prompts
- [x] Output formatted as Amazon HTML subset
- [x] Admin UI: side-by-side A/B preview + rich text editor + character count
- [x] Approve → description locked for export

---

## 🏗️ Phase 5: Story Architecture ✅

- [x] Celery Task: Description Approved → auto-generate StoryBible
- [x] Celery Task: Break story into 70-90 Chapter Briefs
- [x] Clue & Red Herring Tracker in StoryBible
- [x] Admin UI: review + edit Story Bible and Chapter Briefs

---

## ✍️ Phase 6: Content Generation Pipeline ✅

- [x] Celery Beat cron job daily 06:00 AM
- [x] Dynamic Prompt Injection (StyleFingerprint + StoryBible + prev chapter + brief)
- [x] Write 1,000 words ± 10% per Chapter
- [x] Status → Pending QA after write
- [x] Token usage logging
- [x] run_consistency_check(book_id) every 10 chapters
- [x] OllamaProvider (llama3 local) + GeminiProvider (cloud) with one-line swap via LLM_PROVIDER env

---

## 🛡️ Phase 7: Quality, Copyright Gate & KDP Compliance ✅

- [x] QA Gate UI (Approve/Reject/Rewrite with comments)
- [x] Originality.ai API integration (AI Detection < 20%)
- [x] Copyscape API integration (Plagiarism < 3%)
- [x] 6-Point Plot Originality Test checklist in Admin UI
- [x] KDP Pre-Flight Checklist (9-point, all must pass before Export unlocks)
- [x] Export Pipeline: python-docx (.docx) + ebooklib (.epub) with metadata injection

---

## 💰 Phase 8: Dynamic Pricing System ✅

- [x] PricingStrategy model + Admin UI
- [x] Pricing phases: Launch $0.99 → Growth $2.99 → Mature $3.99 → Promo $0.99
- [x] auto_transition_pricing() Celery task (daily)
- [x] schedule_kindle_countdown() Celery task (every 90 days)
- [x] Admin alerts on every price change

---

## 🛍️ Phase 9: Storefront & E-Commerce (Next.js) ✅

- [x] Next.js 14 app at /frontend with Tailwind CSS + App Router
- [x] Homepage with featured books and pen names
- [x] /authors/[id] — PenName profile + book grid
- [x] /books/[id] — Book detail using BookDescription.description_html
- [x] /books/[id]/chapters/[num] — Chapter reader (locked/unlocked based on purchase)
- [x] Stripe Pay-per-chapter ($1.99) + Subscription ($9.99/month & $79.99/year)
- [x] Stripe Webhook handler for payment events
- [x] Drip-feed: Auto-publish Chapter every 3 days (Celery Beat)
- [x] Upsell banner on every Chapter page → Amazon full book $3.99

---

## 📣 Phase 10: Amazon Ads Integration & ACOS Monitor ✅

- [x] Amazon Advertising API integration
- [x] sync_ads_performance() Celery task (daily)
- [x] ACOS = (spend / sales) × 100 per Book and per Keyword
- [x] optimize_ads_keywords() Celery task (weekly Monday 08:00)
  - Pause: ACOS > 70% + clicks > 20
  - Scale +20%: ACOS < 25% + sales > 0
- [x] Admin Alert if ACOS > 50%
- [x] Admin UI: ACOS trend chart, top keywords table, optimization log, spend vs revenue graph

---

## ⭐ Phase 11: Review Velocity & ARC Management ✅

- [x] scrape_amazon_reviews(book_id) Celery task (daily)
- [x] AI sentiment analysis of negative reviews → Improvement Report
- [x] Alert if avg rating < 3.5
- [x] ARCReader management UI (import CSV, filter by genre/reliability, review history)
- [x] send_arc_emails(book_id) Celery task (30 days before launch)
- [x] ARC conversion rate tracking
- [x] Auto-flag unreliable readers (is_reliable = False)

---

## 🌐 Phase 12: Multi-Platform Distribution Tracker ✅

- [x] DistributionChannel model + Admin UI
- [x] Platforms: Amazon KDP, Draft2Digital, ACX, Website, Patreon
- [x] Revenue dashboard across all platforms
- [x] sync_platform_revenue() Celery task (weekly)

---

## 🕵️ Phase 13: Competitor Intelligence Module ✅

- [x] CompetitorBook model
- [x] update_competitor_data() Celery task (weekly): BSR, reviews, price, cover style, estimated revenue
- [x] Admin UI: price distribution chart, review velocity comparison, gap analysis
- [x] AI Weekly "Market Opportunity Report"

---

## ✍️ Phase 14: Writing Style & Voice Consistency Analyzer ✅

- [x] StyleFingerprint model (OneToOne with PenName)
- [x] recalculate_style_fingerprint(pen_name_id) Celery task:
  - Analyzes avg sentence length, dialogue ratio, passive voice, adverb frequency
  - Extracts top bigrams and common patterns
  - Auto-generates style_system_prompt from metrics
- [x] style_system_prompt used in Phase 6 Content Generation
- [x] Admin UI: Style Dashboard per PenName + Voice Drift Alert

---

## 📊 Phase 15: KPI Dashboard (Full) ✅

- [x] Production KPIs: words/day, chapter completion rate, AI detection score, plagiarism score, time to draft, revision rate, API cost
- [x] Sales KPIs: KDP sales, revenue per book/platform, BSR, ROAS
- [x] Marketing KPIs: ACOS, review count/rating/velocity, ARC conversion, traffic
- [x] Alert System (7 conditions: Sales drop, BSR fall, Rating < 3.5, AI score > 30%, ACOS > 50%, Plagiarism > 5%, Celery failures)

---

## 🔐 Phase 16: Legal Protection & Copyright Automation ✅

- [x] Auto-generate Legal Disclaimer per PenName + Book metadata
- [x] Copyright Registration Reminder alert before publish
- [x] setup_google_alerts(book_id) Celery task
- [x] check_content_theft() Celery task (monthly Copyscape Inbound scan)
- [x] DMCA Takedown Template Generator (inline generation from infringing URL)
- [x] KDP Account Health Monitor (Complaints tracking + instant alert)

---

## 🧪 Phase 17: Testing & Quality Infrastructure ✅

- [x] Unit tests for Models + Business logic (pytest + pytest-django)
- [x] DRF API endpoint integration tests (75 tests — 100% pass rate)
- [x] Serializer unit tests (PenName, Book, Chapter, BookDescription)
- [x] Celery task import tests + mock wrappers
- [x] `config/settings_test.py` — in-memory DB + memory broker (no Redis/Postgres needed)
- [x] `pytest.ini` configured with DJANGO_SETTINGS_MODULE=config.settings_test

---

## 🚀 Deployment & DevOps ✅

- [x] Dockerize Django API — multi-stage Dockerfile (builder + runtime, non-root user)
- [x] Dockerize Next.js — multi-stage Dockerfile with `output: 'standalone'`
- [x] `docker-compose.yml` — Django + Celery Worker + Celery Beat + Redis + PostgreSQL + Next.js
- [x] `.github/workflows/ci.yml` — GitHub Actions CI (backend tests + coverage, lint, frontend build, Docker build)
- [x] `.gitignore` — root-level covering Django, Python, IDE, secrets
- [x] `.env.example` — full environment variable template
- [x] Staging + Production environment configs
- [x] Automated daily database backup
- [x] Celery monitoring with Flower dashboard
- [x] API rate limiting

---

## 📐 Summary Priority Matrix

| Phase | Feature | Priority | Status |
|---|---|---|---|
| 1 | Core Infrastructure + State Machine | ✅ Foundation | ✅ Done |
| 2 | Amazon Keyword Research & SEO | 🔴 Critical | ✅ Done |
| 3 | Idea & Strategy Engine | ✅ Core | ✅ Done |
| 4 | Book Description Generator | 🔴 Critical | ✅ Done |
| 5 | Story Architecture | ✅ Core | ✅ Done |
| 6 | Content Generation Pipeline | ✅ Core | ✅ **Done** (Ollama + Gemini) |
| 7 | QA Gate + KDP Compliance | ✅ Core | ✅ Done |
| 8 | Dynamic Pricing System | 🔴 Critical | ✅ Done |
| 9 | Storefront + Stripe (Next.js) | ✅ Core | ✅ **Done** |
| 10 | Amazon Ads ACOS Monitor | 🟡 Important | ✅ Done |
| 11 | Review Velocity + ARC Management | 🟡 Important | ✅ Done |
| 12 | Multi-Platform Distribution | 🟡 Important | ✅ Done |
| 13 | Competitor Intelligence | 🟢 Nice-to-have | ✅ Done |
| 14 | Style Fingerprint Analyzer | 🟢 Nice-to-have | ✅ Done |
| 15 | Full KPI Dashboard | ✅ Core | ✅ Done |
| 16 | Legal Protection & Copyright | 🟡 Important | ✅ Done |
| 17 | Testing Suite | 🟡 Important | ✅ Done |
| — | Docker + CI/CD | 🟡 Important | ✅ Done |

---

*AI Novel Factory System — Full Todo v2.0*
