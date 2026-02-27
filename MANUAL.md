# AI Novel Factory — คู่มือการใช้งานระบบ (System Manual)

> **เวอร์ชัน:** 1.0 · **อัปเดต:** กุมภาพันธ์ 2026  
> **Stack:** Django 5 · Next.js 14 · PostgreSQL · Redis · Celery · Gemini AI

---

## สารบัญ (Table of Contents)

1. [ภาพรวมระบบ (System Overview)](#1-ภาพรวมระบบ)
2. [สถาปัตยกรรม (Architecture)](#2-สถาปัตยกรรม)
3. [การติดตั้งและตั้งค่า (Installation & Setup)](#3-การติดตั้งและตั้งค่า)
4. [หน้าจอระบบ Frontend](#4-หน้าจอระบบ-frontend)
   - 4.1 [Dashboard — ภาพรวมการผลิต](#41-dashboard--ภาพรวมการผลิต)
   - 4.2 [Books — รายการหนังสือ](#42-books--รายการหนังสือ)
   - 4.3 [Book Detail — รายละเอียดหนังสือ](#43-book-detail--รายละเอียดหนังสือ)
   - 4.4 [Lifecycle Workflow — การเปลี่ยนสถานะ](#44-lifecycle-workflow--การเปลี่ยนสถานะ)
   - 4.5 [Chapter Manager — จัดการบท](#45-chapter-manager--จัดการบท)
   - 4.6 [KDP Covers — จัดการปก](#46-kdp-covers--จัดการปก)
   - 4.7 [Keyword Research — วิจัยคีย์เวิร์ด](#47-keyword-research--วิจัยคีย์เวิร์ด)
   - 4.8 [Story Bible — คู่มือเรื่อง](#48-story-bible--คู่มือเรื่อง)
   - 4.9 [Analytics — วิเคราะห์รายได้และโฆษณา](#49-analytics--วิเคราะห์รายได้และโฆษณา)
   - 4.10 [Pen Names — จัดการนามปากกา](#410-pen-names--จัดการนามปากกา)
   - 4.11 [New Book — สร้างหนังสือใหม่](#411-new-book--สร้างหนังสือใหม่)
5. [วงจรชีวิตหนังสือ (Book Lifecycle)](#5-วงจรชีวิตหนังสือ)
6. [Backend API Reference](#6-backend-api-reference)
7. [Celery Background Tasks](#7-celery-background-tasks)
8. [การตั้งค่า Production](#8-การตั้งค่า-production)
9. [Docker & Deployment](#9-docker--deployment)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. ภาพรวมระบบ

**AI Novel Factory** คือระบบจัดการการผลิตนิยาย AI แบบครบวงจร ตั้งแต่การวิจัยคีย์เวิร์ด ไปจนถึงการเผยแพร่บน Amazon KDP และการวิเคราะห์รายได้และโฆษณา

### ฟีเจอร์หลัก

| โมดูล | คำอธิบาย |
|---|---|
| **Book Lifecycle FSM** | ระบบสถานะหนังสือแบบ Finite State Machine รองรับ 13 สถานะ |
| **AI Content Generation** | สร้างเนื้อหา ตัวละคร คำอธิบาย และบทต่าง ๆ ด้วย AI (Gemini / Ollama) |
| **KDP Cover Manager** | อัปโหลดและคำนวณขนาดปกอีบุ๊กและปกกระดาษ (Paperback) ตามมาตรฐาน KDP |
| **Keyword Research** | วิจัยคีย์เวิร์ด KDP Backend ดู ASIN คู่แข่ง อนุมัติ/รัน webhook |
| **Story Bible** | จัดการเอกสารอ้างอิงเรื่อง (ตัวละคร โลก ไทม์ไลน์ โครงเรื่อง) |
| **Analytics Dashboard** | ติดตามรายได้ ACOS โฆษณา และรีวิว |
| **Chapter Management** | QA review อนุมัติ/ปฏิเสธ ตีพิมพ์บท |
| **Stripe Payments** | ระบบสมัครสมาชิกและซื้อบทรายบท |
| **Pen Name CRUD** | จัดการนามปากกาหลายชื่อ |

---

## 2. สถาปัตยกรรม

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                  │
│  :3001  ·  TypeScript  ·  Tailwind CSS  ·  Lucide Icons  │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API (JSON)
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (Django 5 + DRF)                    │
│  :8000  ·  PostgreSQL  ·  django-fsm  ·  Throttling      │
└───────────────┬──────────────────────┬──────────────────┘
                │                      │
                ▼                      ▼
┌──────────────────┐        ┌──────────────────────────┐
│  Celery Workers  │        │   External APIs          │
│  Redis broker    │        │  Gemini · Stripe         │
│  Scheduled tasks │        │  Amazon Ads · Sentry      │
└──────────────────┘        └──────────────────────────┘
```

### โครงสร้างไดเรกทอรี

```
AI-Novel-Factory/
├── config/                  # Django settings & URLs
│   ├── settings.py          # Main Django configuration
│   └── urls.py              # Root URL routing
├── novels/                  # Main Django app
│   ├── api/                 # DRF ViewSets, Serializers, URLs
│   │   ├── views.py         # 9 ViewSets (Book, Chapter, Cover, ...)
│   │   ├── serializers.py   # 15+ serializers
│   │   └── urls.py          # API router registration
│   ├── models/              # Django models (Book, Chapter, Cover, ...)
│   ├── tasks/               # Celery async tasks
│   │   ├── content.py       # AI content generation
│   │   ├── keywords.py      # Keyword research
│   │   ├── ads.py           # Amazon Ads sync
│   │   ├── reviews.py       # Review scraping
│   │   └── pricing.py       # Auto pricing transitions
│   ├── services/            # Business logic layer
│   └── utils/               # KDP calculator, helpers
├── frontend/                # Next.js 14 application
│   ├── app/                 # App Router pages
│   │   ├── analytics/       # Analytics dashboard
│   │   ├── books/
│   │   │   ├── [id]/        # Book detail
│   │   │   │   ├── workflow/    # Lifecycle FSM control
│   │   │   │   ├── chapters/    # Chapter management
│   │   │   │   ├── covers/      # KDP cover manager
│   │   │   │   ├── keywords/    # Keyword research
│   │   │   │   └── bible/       # Story bible editor
│   │   │   └── new/         # Create book form
│   │   ├── dashboard/       # Production pipeline overview
│   │   └── pen-names/       # Author management
│   ├── components/          # Reusable UI components
│   ├── lib/                 # API client (axios)
│   └── types/               # TypeScript interfaces
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── MANUAL.md                # This file
```

---

## 3. การติดตั้งและตั้งค่า

### ความต้องการของระบบ (Prerequisites)

| ซอฟต์แวร์ | เวอร์ชันขั้นต่ำ |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| Redis | 7+ |
| Docker (optional) | 24+ |

### 3.1 ติดตั้ง Backend

```bash
# Clone project
git clone <repo-url>
cd AI-Novel-Factory

# สร้าง virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# ติดตั้ง dependencies
pip install -r requirements.txt

# ตั้งค่า environment variables
copy .env.example .env
# แก้ไขค่าใน .env ตามสภาพแวดล้อมของคุณ

# รัน migrations
python manage.py migrate

# สร้าง superuser
python manage.py createsuperuser

# (Optional) โหลดข้อมูลตัวอย่าง
python manage.py seed_data

# รัน development server
python manage.py runserver 0:8000
```

### 3.2 ติดตั้ง Frontend

```bash
cd frontend

# ติดตั้ง dependencies
npm install

# ตั้งค่า environment
copy .env.local.example .env.local
# แก้ไข NEXT_PUBLIC_API_URL ให้ตรงกับ backend

# รัน development server
npm run dev        # :3001
```

### 3.3 รัน Celery Workers

```bash
# Terminal 1: Worker
celery -A config worker -l INFO -Q default,ai_generation

# Terminal 2: Beat Scheduler (cron tasks)
celery -A config beat -l INFO

# Terminal 3: Flower (monitoring)
celery -A config flower --port=5555
```

### 3.4 Environment Variables ที่สำคัญ

#### Backend (`.env`)

| ตัวแปร | คำอธิบาย | ค่าเริ่มต้น |
|---|---|---|
| `SECRET_KEY` | Django secret key — **must change in production** | insecure default |
| `DEBUG` | True/False | True |
| `DB_ENGINE` | `postgresql` หรือ `sqlite` | sqlite |
| `REDIS_URL` | URL ของ Redis | redis://localhost:6379/0 |
| `LLM_PROVIDER` | `gemini` หรือ `ollama` | ollama |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `CORS_ALLOWED_ORIGINS` | Origins ที่อนุญาต (คั่นด้วย comma) | localhost:3000,localhost:3001 |
| `STRIPE_SECRET_KEY` | Stripe secret key | — |
| `SENTRY_DSN` | Sentry error tracking DSN | — |

#### Frontend (`.env.local`)

| ตัวแปร | คำอธิบาย |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL ของ Django API เช่น `http://localhost:8000/api` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key |
| `NEXT_PUBLIC_MEDIA_HOST` | Hostname สำหรับรูปภาพ media (production) |

---

## 4. หน้าจอระบบ Frontend

### 4.1 Dashboard — ภาพรวมการผลิต

**URL:** `/dashboard`

แสดงภาพรวมสถานะการผลิตของหนังสือทั้งหมด

#### ส่วนประกอบ

| ส่วน | คำอธิบาย |
|---|---|
| **KPI Cards** | จำนวนหนังสือทั้งหมด, หนังสือที่ตีพิมพ์แล้ว, รายได้รวม, จำนวนคำทั้งหมด |
| **AI Quality Scores** | AI Detection Score และ Plagiarism Score เฉลี่ย |
| **Chapter Stats** | จำนวนบท: ทั้งหมด / อนุมัติ / ตีพิมพ์ / รอ QA |
| **Status Pipeline** | แถบแสดงจำนวนหนังสือในแต่ละสถานะ |
| **Recent Books** | 5 หนังสือล่าสุดที่มีการอัปเดต + progress bar |

#### ข้อมูล API

```
GET /api/books/pipeline_stats/
```

---

### 4.2 Books — รายการหนังสือ

**URL:** `/books`

แสดงรายการหนังสือทั้งหมดพร้อมกรองและค้นหา

#### ฟีเจอร์

- **ค้นหา** ตามชื่อหนังสือ, ผู้แต่ง (นามปากกา), เนื้อเรื่องย่อ
- **กรอง** ตามสถานะ lifecycle
- **เรียงลำดับ** ตามวันที่สร้าง, วันที่ตีพิมพ์, BSR
- **Book Card** แสดง: ปก, ชื่อ, ผู้แต่ง, สถานะ, progress bar, ราคา, รีวิว, ASIN

---

### 4.3 Book Detail — รายละเอียดหนังสือ

**URL:** `/books/[id]`

หน้ารายละเอียดหนังสือสำหรับผู้อ่าน — แสดงปก ชื่อ เรื่องย่อ บทต่าง ๆ

#### ปุ่ม Navigation (Sidebar ซ้าย)

| ปุ่ม | ปลายทาง |
|---|---|
| **Manage KDP Covers** | `/books/[id]/covers` |
| **Lifecycle Workflow** | `/books/[id]/workflow` |
| **Manage Chapters** | `/books/[id]/chapters` |
| **Keyword Research** | `/books/[id]/keywords` |
| **Story Bible** | `/books/[id]/bible` |

---

### 4.4 Lifecycle Workflow — การเปลี่ยนสถานะ

**URL:** `/books/[id]/workflow`

ควบคุมสถานะของหนังสือผ่าน Finite State Machine (FSM)

#### สถานะและปุ่มที่ใช้ได้

| สถานะปัจจุบัน | ปุ่มที่ใช้ได้ | สถานะถัดไป |
|---|---|---|
| `concept_pending` | Start Keyword Research | `keyword_research` |
| `keyword_research` | Approve Keywords | `keyword_approved` |
| `keyword_approved` | Generate Description | `description_generation` |
| `description_generation` | Approve Description | `description_approved` |
| `description_approved` | Generate Story Bible | `bible_generation` |
| `bible_generation` | Approve Bible | `bible_approved` |
| `bible_approved` | Start Writing | `writing_in_progress` |
| `writing_in_progress` | Submit for QA | `qa_review` |
| `qa_review` | Approve for Export | `export_ready` |
| `export_ready` | Publish to KDP | `published_kdp` |

> **หมายเหตุ:** ปุ่มที่ trigger AI generation (Generate Description, Generate Story Bible) มี throttle จำกัด 20 ครั้ง/ชั่วโมง

#### Export หนังสือ

- **DOCX** — ไฟล์ Word สำหรับส่ง KDP
- **EPUB** — ไฟล์ eBook สำหรับอีบุ๊ก

---

### 4.5 Chapter Manager — จัดการบท

**URL:** `/books/[id]/chapters`

จัดการสถานะบท QA อนุมัติ หรือปฏิเสธ

#### คอลัมน์ตาราง

| คอลัมน์ | คำอธิบาย |
|---|---|
| **บทที่** | Chapter number |
| **ชื่อบท** | Chapter title |
| **สถานะ** | pending / ready\_to\_write / written / qa\_review / approved / rejected |
| **จำนวนคำ** | Word count |
| **ตีพิมพ์** | Toggle บทที่แสดงต่อสาธารณะ |
| **ฟรี** | Toggle บทที่อ่านได้ฟรี |
| **AI Score** | AI Detection Score |
| **QA Notes** | บันทึก QA |

#### การดำเนินการ

- **Mark Ready** — เปลี่ยนสถานะเป็น `ready_to_write` ให้ AI เขียน
- **Approve** — อนุมัติบทผ่าน QA
- **Reject** — ปฏิเสธ (ต้องใส่ Notes) — trigger rewrite ผ่าน Celery

---

### 4.6 KDP Covers — จัดการปก

**URL:** `/books/[id]/covers`

อัปโหลดและจัดการปกหนังสือสำหรับ Amazon KDP

#### KDP Dimension Calculator (built-in)

| ประเภท | ค่า |
|---|---|
| **eBook** | 2,560 × 1,600 px (ratio 1.6:1) |
| **Paperback 6×9** | คำนวณอัตโนมัติตาม paper type และ page count |

#### การใช้งาน

1. เลือก **Cover Type**: eBook หรือ Paperback
2. (Paperback) เลือก **Trim Size**, **Paper Type**, ใส่ **Page Count**
3. ระบบจะแสดงขนาดที่ถูกต้องให้ทันที
4. คลิก **+ New Cover Version** เพื่อสร้างเวอร์ชันใหม่
5. อัปโหลดไฟล์ปก (Front / Full / Back)
6. คลิก **Set Active** เพื่อเลือกปกที่ใช้งาน

#### ประเภทปก

| ประเภท | Front Cover | Full Cover | Back Cover |
|---|---|---|---|
| **eBook** | ✅ required | — | — |
| **Paperback** | ✅ | ✅ full wrap | ✅ |

---

### 4.7 Keyword Research — วิจัยคีย์เวิร์ด

**URL:** `/books/[id]/keywords`

จัดการคีย์เวิร์ด KDP สำหรับการค้นพบหนังสือบน Amazon

#### ส่วนประกอบ

**AI Suggestions (อ่านอย่างเดียว)**
- ชื่อที่แนะนำ (Suggested Title)
- ชื่อรอง (Suggested Subtitle)
- ปุ่ม Copy ใช้งานทั้งสองรายการ

**KDP Backend Keywords (แก้ไขได้)**
- 7 ช่อง (Keyword 1–7)
- แต่ละช่องรองรับ 50 ตัวอักษร
- Counter แสดง X/50 พร้อมเตือนเมื่อเกิน

**Categories**
- KDP Category 1 และ Category 2
- ป้อนเส้นทางหมวดหมู่เต็ม เช่น `Kindle Store > Books > Literature`

**Primary Keywords (Tags)**
- เพิ่ม/ลบ keyword tags
- แสดง volume และ competition level

**Competitor ASINs (ตาราง)**
| คอลัมน์ | คำอธิบาย |
|---|---|
| ASIN | Amazon Standard Identification Number |
| Title | ชื่อหนังสือคู่แข่ง |
| BSR | Best Seller Rank |
| Reviews | จำนวนรีวิว |
| Rating | คะแนน (ดาว) |
| Price | ราคา |

#### ปุ่มดำเนินการ

| ปุ่ม | คำอธิบาย |
|---|---|
| **Validate** | ตรวจสอบ keyword ว่าถูกต้องตามข้อกำหนด KDP |
| **Re-run Research** | ส่ง task ให้ Celery รันการวิจัยใหม่ |
| **Save Changes** | บันทึกการแก้ไขทั้งหมด |
| **Approve** | อนุมัติผลการวิจัย (ล็อก timestamp) |

---

### 4.8 Story Bible — คู่มือเรื่อง

**URL:** `/books/[id]/bible`

เอกสารอ้างอิงสำหรับ AI ในการเขียนเนื้อหาอย่างสอดคล้องกัน

#### ส่วนประกอบ (Collapsible Sections)

| ส่วน | รูปแบบข้อมูล | คำอธิบาย |
|---|---|---|
| **Characters** | JSON Array | รายชื่อและประวัติตัวละคร |
| **World Rules** | JSON Array/Object | กฎโลกของเรื่อง (magic system, technology, etc.) |
| **Timeline** | JSON Array | ลำดับเหตุการณ์ตามเวลา |
| **4-Act Outline** | JSON Object | โครงเรื่อง (Act 1, 2A, 2B, 3) |
| **Clues Tracker** | JSON Array | เบาะแสและ foreshadowing |

#### Text Fields

| ฟิลด์ | คำอธิบาย |
|---|---|
| **Themes** | แก่นเรื่องหลัก |
| **Tone** | น้ำเสียงของเรื่อง (dark, hopeful, etc.) |
| **POV** | มุมมองการเล่าเรื่อง (First Person, Third Limited, etc.) |
| **Tense** | กาล (Past, Present) |

#### AI Summary

- แสดงสรุปเนื้อหาที่ AI ใช้ใน prompt
- ปุ่ม **Regenerate** — สร้างสรุปใหม่จาก Bible ปัจจุบัน

> **JSON Editor:** แต่ละ section มี JSON textarea ที่ตรวจสอบ format อัตโนมัติ เมื่อ blur จะแจ้งเตือนหากรูปแบบไม่ถูกต้อง

---

### 4.9 Analytics — วิเคราะห์รายได้และโฆษณา

**URL:** `/analytics`

แดชบอร์ดรายได้และโฆษณาสำหรับผู้ดูแลระบบ

#### KPI Cards (6 หน้าต่าง)

| KPI | คำอธิบาย |
|---|---|
| **Total Revenue** | รายได้รวมทุกเล่ม (USD) |
| **Total Books** | จำนวนหนังสือทั้งหมด |
| **Ads Spend (30d)** | ค่าโฆษณา 30 วันล่าสุด |
| **Ads Sales (30d)** | ยอดขายจากโฆษณา 30 วัน |
| **Overall ACOS** | Advertising Cost of Sale (%) |
| **Total Reviews** | รีวิวรวม + คะแนนเฉลี่ย |

#### ACOS Color Legend

| สี | ช่วง | ความหมาย |
|---|---|---|
| 🟢 Green | < 25% | ดีเยี่ยม — กำไรสูง |
| 🟡 Yellow | 25–50% | พอรับได้ |
| 🔴 Red | > 50% | ขาดทุนจากโฆษณา |

#### Revenue Bar Chart

แถบแสดงรายได้ของแต่ละหนังสือเปรียบเทียบกัน (เรียงจากมากไปน้อย)

#### ตาราง Book Performance

แสดงข้อมูลทุกเล่มในหน้าเดียว: ชื่อ, Pen Name, สถานะ, รายได้, ราคา, BSR, รีวิว, คะแนน, ค่าโฆษณา, ACOS

#### Tab Filter

- **All Books** — หนังสือทั้งหมด
- **Published** — เฉพาะที่ตีพิมพ์แล้ว (`published_kdp`, `published_all`)

---

### 4.10 Pen Names — จัดการนามปากกา

**URL:** `/pen-names`

CRUD นามปากกา (ผู้แต่ง)

#### ฟิลด์นามปากกา

| ฟิลด์ | จำเป็น | คำอธิบาย |
|---|---|---|
| **Name** | ✅ | ชื่อนามปากกา |
| **Niche/Genre** | ✅ | ประเภทหนังสือที่เชี่ยวชาญ |
| **Bio** | — | ประวัติผู้แต่ง |
| **Writing Style Prompt** | — | Prompt สไตล์การเขียนสำหรับ AI |
| **Website URL** | — | เว็บไซต์ผู้แต่ง |
| **Amazon Author URL** | — | หน้า Author Central |

#### Stats (คำนวณอัตโนมัติ)

- Total Books Published
- Total Revenue (USD)
- Book Count

---

### 4.11 New Book — สร้างหนังสือใหม่

**URL:** `/books/new`

ฟอร์มสร้างหนังสือเล่มใหม่

#### ฟิลด์ที่บังคับ

| ฟิลด์ | คำอธิบาย |
|---|---|
| **Title** | ชื่อหนังสือ |
| **Pen Name** | เลือกนามปากกาจากรายการ |

#### ฟิลด์ Optional

| ฟิลด์ | คำอธิบาย |
|---|---|
| **Subtitle** | ชื่อรอง |
| **Synopsis** | เรื่องย่อ |
| **Target Audience** | กลุ่มเป้าหมาย |
| **Hook** | ประโยคเปิดดึงดูด |
| **Core Twist** | จุดพลิกผันหลัก |
| **Target Chapters** | จำนวนบทเป้าหมาย (default: 25) |
| **Target Word Count** | จำนวนคำเป้าหมาย (default: 60,000) |

หลังจากสร้างสำเร็จ ระบบจะ redirect ไปหน้า Book Detail โดยอัตโนมัติ

---

## 5. วงจรชีวิตหนังสือ

### Lifecycle States (ทั้ง 13 สถานะ)

```
concept_pending
    │  [Start Keyword Research] → Celery: run_keyword_research
    ▼
keyword_research
    │  [Approve Keywords]
    ▼
keyword_approved
    │  [Generate Description] → Celery: generate_book_description
    ▼
description_generation
    │  [Approve Description]
    ▼
description_approved
    │  [Generate Story Bible] → Celery: generate_story_bible
    ▼
bible_generation
    │  [Approve Bible]
    ▼
bible_approved
    │  [Start Writing]
    ▼
writing_in_progress
    │  [Submit for QA]
    ▼
qa_review
    │  [Approve for Export]
    ▼
export_ready
    │  [Publish to KDP]
    ▼
published_kdp ──→ published_all
                        │
                        └──→ archived
```

### Chapter States

```
pending → ready_to_write → written → qa_review → approved → published
                                          │
                                          └──→ rejected → [rewrite] → written
```

---

## 6. Backend API Reference

### Base URL

```
Development: http://localhost:8000/api/
Production:  https://yourdomain.com/api/
```

### Authentication

- **Session Auth** — ล็อกอินจาก Django Admin หรือ /api/auth/
- **Token Auth** — ส่ง Header `Authorization: Token <token>`

### Endpoints

#### Books (`/api/books/`)

| Method | URL | คำอธิบาย | Auth |
|---|---|---|---|
| GET | `/api/books/` | รายการหนังสือ (filter: pen_name, lifecycle_status) | Public |
| POST | `/api/books/` | สร้างหนังสือใหม่ | Auth |
| GET | `/api/books/{id}/` | รายละเอียดหนังสือ | Public |
| PATCH | `/api/books/{id}/` | แก้ไขหนังสือ | Auth |
| DELETE | `/api/books/{id}/` | ลบหนังสือ (soft delete) | Auth |
| POST | `/api/books/{id}/start_keyword_research/` | เริ่มวิจัยคีย์เวิร์ด | Auth |
| POST | `/api/books/{id}/approve_keywords/` | อนุมัติคีย์เวิร์ด | Auth |
| POST | `/api/books/{id}/start_description_generation/` | สร้าง Description | Auth |
| POST | `/api/books/{id}/approve_description/` | อนุมัติ Description | Auth |
| POST | `/api/books/{id}/start_bible_generation/` | สร้าง Story Bible | Auth |
| POST | `/api/books/{id}/approve_bible/` | อนุมัติ Story Bible | Auth |
| POST | `/api/books/{id}/start_writing/` | เริ่มเขียนเนื้อหา | Auth |
| POST | `/api/books/{id}/submit_for_qa/` | ส่ง QA | Auth |
| POST | `/api/books/{id}/approve_for_export/` | อนุมัติ Export | Auth |
| POST | `/api/books/{id}/publish_to_kdp/` | เผยแพร่ KDP | Auth |
| POST | `/api/books/{id}/export/` | Export DOCX/EPUB | Auth |
| GET | `/api/books/pipeline_stats/` | สถิติ Dashboard | Auth |
| GET | `/api/books/analytics_summary/` | สรุป Analytics | Auth |

**Query Parameters (GET /api/books/):**
```
pen_name=<id>
lifecycle_status=published_kdp,published_all
search=<text>
ordering=-created_at
page=1
```

#### Chapters (`/api/chapters/`)

| Method | URL | คำอธิบาย |
|---|---|---|
| GET | `/api/chapters/` | รายการบท (filter: book, status, is_published) |
| PATCH | `/api/chapters/{id}/` | แก้ไขบท |
| POST | `/api/chapters/{id}/approve/` | อนุมัติบท |
| POST | `/api/chapters/{id}/reject/` | ปฏิเสธบท (ต้องส่ง `notes`) |
| POST | `/api/chapters/{id}/mark_ready_to_write/` | ทำเครื่องหมายพร้อมเขียน |

#### Covers (`/api/covers/`)

| Method | URL | คำอธิบาย |
|---|---|---|
| GET | `/api/covers/` | รายการปก |
| POST | `/api/covers/` | สร้างปกใหม่ (multipart/form-data) |
| PATCH | `/api/covers/{id}/` | อัปเดตปก |
| DELETE | `/api/covers/{id}/` | ลบปก |
| POST | `/api/covers/{id}/activate/` | เลือกเป็นปก active |
| GET | `/api/covers/calculate/` | คำนวณขนาด KDP |
| GET | `/api/covers/choices/` | ตัวเลือก trim/paper type |

#### Keyword Research (`/api/keyword-research/`)

| Method | URL | คำอธิบาย |
|---|---|---|
| GET | `/api/keyword-research/?book={id}` | ดูผลวิจัย |
| PATCH | `/api/keyword-research/{id}/` | แก้ไขคีย์เวิร์ด |
| POST | `/api/keyword-research/{id}/approve/` | อนุมัติ |
| POST | `/api/keyword-research/{id}/re_run/` | รันใหม่ |
| GET | `/api/keyword-research/{id}/validate/` | Validate |

#### Story Bible (`/api/story-bibles/`)

| Method | URL | คำอธิบาย |
|---|---|---|
| GET | `/api/story-bibles/?book={id}` | ดู Story Bible |
| PATCH | `/api/story-bibles/{id}/` | บันทึก Bible |
| POST | `/api/story-bibles/{id}/generate_summary/` | สร้าง AI Summary |

#### Analytics & Reviews

| Endpoint | คำอธิบาย |
|---|---|
| `GET /api/review-trackers/?book={id}` | ข้อมูลรีวิวหนังสือ |
| `GET /api/ads-performance/?book={id}` | ผลโฆษณารายวัน |

#### Pen Names (`/api/pen-names/`)

| Method | URL | คำอธิบาย |
|---|---|---|
| GET | `/api/pen-names/` | รายการนามปากกา |
| POST | `/api/pen-names/` | สร้างนามปากกา |
| PATCH | `/api/pen-names/{id}/` | แก้ไข |
| DELETE | `/api/pen-names/{id}/` | ลบ (soft delete) |
| POST | `/api/pen-names/{id}/update_stats/` | คำนวณ stats ใหม่ |

### Response Format

**Paginated List:**
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/books/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

**Error Response:**
```json
{
  "detail": "Not found.",
  "error": "Human-readable message"
}
```

### Rate Limiting (Throttling)

| Scope | Limit |
|---|---|
| Anonymous | 200/hour |
| User (general) | 2,000/hour |
| AI Generation | 20/hour |
| Chapter Write | 50/hour |
| Payment | 30/hour |

---

## 7. Celery Background Tasks

### Tasks ที่มีในระบบ

| Task | Module | ทริกเกอร์โดย |
|---|---|---|
| `run_keyword_research` | `tasks.keywords` | start_keyword_research lifecycle action |
| `generate_book_description` | `tasks.content` | start_description_generation |
| `generate_story_bible` | `tasks.content` | start_bible_generation |
| `rewrite_chapter` | `tasks.content` | chapter reject action |
| `run_daily_content_generation` | `tasks.content` | Cron: 06:00 daily |
| `sync_ads_performance` | `tasks.ads` | Cron: 08:00 daily |
| `optimize_ads_keywords` | `tasks.ads` | Cron: Mon 08:00 |
| `scrape_all_books_reviews` | `tasks.reviews` | Cron: 09:00 daily |
| `auto_transition_pricing` | `tasks.pricing` | Cron: 07:00 daily |
| `backup_database` | `tasks.maintenance` | Cron: 02:00 daily |
| `cleanup_old_backups` | `tasks.maintenance` | Cron: Mon 03:00 |

### ตรวจสอบ Task Status

```bash
# Flower Web UI
http://localhost:5555

# CLI
celery -A config inspect active
celery -A config inspect reserved
```

### Queue Configuration

| Queue | ใช้สำหรับ |
|---|---|
| `default` | งานทั่วไป (ads sync, reviews, maintenance) |
| `ai_generation` | งาน AI (content generation ใช้ GPU/API) |

---

## 8. การตั้งค่า Production

### 8.1 Security Checklist

```python
# settings.py / settings_production.py
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')  # ต้องเป็น random string ยาว ≥ 50 chars
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### 8.2 Database

ใน Production ต้องใช้ **PostgreSQL** เท่านั้น (ไม่ใช้ SQLite):

```bash
# .env
DB_ENGINE=postgresql
DB_NAME=ai_novel_factory
DB_USER=novel_user
DB_PASSWORD=<strong-password>
DB_HOST=db   # Docker service name
DB_PORT=5432
```

### 8.3 Static Files

```bash
# Run once after deployment
python manage.py collectstatic --noinput
```

### 8.4 CORS

```bash
# .env
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 8.5 AI Provider

```bash
# .env (Production: ใช้ Gemini)
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-2.0-flash
```

---

## 9. Docker & Deployment

### 9.1 Docker Compose (Development)

```bash
# สร้างและรัน services ทั้งหมด
docker-compose up --build

# Services ที่รัน
# - django   :8000
# - frontend :3001  
# - postgres :5432
# - redis    :6379
# - celery worker
# - celery beat
# - flower   :5555
```

### 9.2 Production Deployment

**ขั้นตอน:**

1. **สร้างไฟล์ `.env.production`** จาก `.env.production.example`

2. **Build images:**
```bash
docker-compose -f docker-compose.prod.yml build
```

3. **Run migrations:**
```bash
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py collectstatic --noinput
```

4. **สร้าง superuser (ครั้งแรกเท่านั้น):**
```bash
docker-compose exec django python manage.py createsuperuser
```

5. **ตรวจสอบ:**
```bash
docker-compose exec django python manage.py check --deploy
```

### 9.3 Environment Variables Production

ดูไฟล์ `.env.production.example` สำหรับตัวแปรทั้งหมดที่ต้องตั้งค่า

### 9.4 Frontend Build

```bash
cd frontend
npm run build    # สร้าง production build
npm start        # รัน production server

# หรือใช้ Docker
docker build -t novel-frontend ./frontend
docker run -p 3001:3001 -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api novel-frontend
```

---

## 10. Troubleshooting

### ปัญหาที่พบบ่อย

#### Backend

**Django check error: `System check identified issues`**
```bash
python manage.py check --deploy
# ตรวจสอบ settings ทั้งหมด
```

**Celery ไม่รับ task:**
```bash
# ตรวจสอบ Redis connection
redis-cli ping   # ควรได้ PONG

# ตรวจสอบ worker
celery -A config inspect active
```

**CORS error จาก Frontend:**
```bash
# ตรวจสอบ .env
CORS_ALLOWED_ORIGINS=http://localhost:3001

# หรือ production
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

**`ImproperlyConfigured`: SECRET_KEY ไม่ถูกต้อง**
```bash
# Generate new key
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Migration error:**
```bash
python manage.py showmigrations
python manage.py migrate --run-syncdb
```

#### Frontend

**ไม่เห็นข้อมูล (API returns 401):**
- ตรวจสอบว่าล็อกอินแล้วใน Django session หรือส่ง Token header

**`NetworkError` / `ERR_CONNECTION_REFUSED`:**
- ตรวจสอบ `NEXT_PUBLIC_API_URL` ใน `.env.local`
- ตรวจสอบว่า Django server กำลังทำงาน

**รูปปกไม่แสดง:**
- ตรวจสอบ `NEXT_PUBLIC_MEDIA_HOST` ใน production
- ตรวจสอบ `MEDIA_ROOT` ใน Django settings
- ตรวจสอบ `remotePatterns` ใน `next.config.mjs`

**Build error: TypeScript type error:**
```bash
cd frontend
npm run build 2>&1 | grep "Type error"
```

#### Database

**PostgreSQL connection refused:**
```bash
# ตรวจสอบ PostgreSQL
pg_isready -h localhost -p 5432

# docker
docker-compose ps db
docker-compose logs db
```

**SQLite ใน Production:**
- **ห้ามใช้ SQLite ใน Production** — ต้องตั้งค่า `DB_ENGINE=postgresql`

### Log Files

| ไฟล์ | ข้อมูลที่บันทึก |
|---|---|
| `logs/django.log` | Django request/response errors |
| `logs/celery.log` | Background task execution |

```bash
# ดู logs แบบ real-time
tail -f logs/django.log
tail -f logs/celery.log
```

### Django Admin

**URL:** `http://localhost:8000/admin/`

ใช้สำหรับจัดการข้อมูลโดยตรง รวมถึง:
- จัดการ Users และ Tokens
- ดู/แก้ไข Book, Chapter, KeywordResearch, etc.
- ตรวจสอบ Celery Beat schedules

---

## ผู้พัฒนา (Development Notes)

### Code Style

- **Python:** Black formatter, isort, flake8 (ดู `requirements.txt`)
- **TypeScript:** ESLint + Next.js default rules

```bash
# Format Python
black novels/ config/
isort novels/ config/

# Lint TypeScript
cd frontend && npm run lint
```

### Testing

```bash
# Backend tests
pytest

# Frontend type check
cd frontend && npm run build
```

### Git Workflow

```bash
# Feature branch
git checkout -b feat/your-feature

# Commit
git add -A
git commit -m "feat: description"

# Push
git push origin feat/your-feature
```

---

*เอกสารนี้อัปเดตล่าสุด: กุมภาพันธ์ 2026 | AI Novel Factory v1.0*
