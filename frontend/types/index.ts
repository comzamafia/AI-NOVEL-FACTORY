// ============================================================
// CORE API TYPES — mirrors Django DRF serializers
// ============================================================

export interface PenName {
  id: number;
  name: string;
  niche_genre: string;
  bio: string;
  writing_style_prompt?: string;
  profile_image?: string;
  website_url?: string;
  amazon_author_url?: string;
  total_books_published?: number;
  total_revenue_usd?: string | number;
  book_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Book {
  id: number;
  title: string;
  synopsis: string;
  bsr?: number;
  target_audience?: string;
  lifecycle_status: BookLifecycleStatus;
  pen_name: PenName | number;
  cover_image_url?: string;
  asin?: string;
  amazon_url?: string;
  published_at?: string;
  created_at: string;
  description?: BookDescription;
  active_description?: BookDescription;
  chapter_count?: number;
  published_chapter_count?: number;
  avg_rating?: number;
  review_count?: number;
  current_price_usd?: number;
}

export type BookLifecycleStatus =
  | 'concept_pending'
  | 'keyword_research'
  | 'keyword_approved'
  | 'description_generation'
  | 'description_approved'
  | 'bible_generation'
  | 'bible_approved'
  | 'writing_in_progress'
  | 'qa_review'
  | 'export_ready'
  | 'published_kdp'
  | 'published_all'
  | 'archived';

export interface BookDescription {
  id: number;
  book: number;
  description_html: string;
  description_plain: string;
  version: 'A' | 'B';
  hook_line?: string;
  setup_paragraph?: string;
  stakes_paragraph?: string;
  call_to_action?: string;
  comparable_authors?: string[];
  is_active: boolean;
}

export interface Chapter {
  id: number;
  book: number;
  chapter_number: number;
  title?: string;
  brief?: string;
  content?: string;
  status: ChapterStatus;
  is_published: boolean;
  published_at?: string;
  word_count?: number;
  is_free?: boolean;
}

export type ChapterStatus = 'pending' | 'ready_to_write' | 'written' | 'qa_review' | 'approved' | 'rejected';

export interface Subscription {
  id: number;
  user: number;
  stripe_subscription_id: string;
  status: SubscriptionStatus;
  current_period_end: string;
  plan: 'monthly' | 'annual';
}

export type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'trialing' | 'unpaid';

export interface ChapterPurchase {
  id: number;
  user: number;
  chapter: number;
  stripe_payment_intent_id: string;
  amount_paid_usd: number;
  purchased_at: string;
}

// ============================================================
// KDP COVER TYPES
// ============================================================
export type CoverType = 'ebook' | 'paperback';
export type PaperType = 'bw_white' | 'bw_cream' | 'color';

export interface BookCover {
  id: number;
  book: number;
  cover_type: CoverType;
  cover_type_display: string;
  version_number: number;
  version_note: string;
  is_active: boolean;
  // Paperback
  trim_size: string;
  trim_size_display: string;
  paper_type: PaperType | '';
  paper_type_display: string;
  page_count: number | null;
  // Calculated dims
  ebook_width_px: number | null;
  ebook_height_px: number | null;
  spine_width_in: string | null;
  total_width_in: string | null;
  total_height_in: string | null;
  total_width_px: number | null;
  total_height_px: number | null;
  // Files
  front_cover: string | null;
  front_cover_url: string | null;
  full_cover: string | null;
  full_cover_url: string | null;
  back_cover: string | null;
  back_cover_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface KDPEbookDimensions {
  cover_type: 'ebook';
  width_px: number;
  height_px: number;
  aspect_ratio: number;
  file_size_kb_approx: number;
  notes: string[];
}

export interface KDPPaperbackDimensions {
  cover_type: 'paperback';
  trim_size: string;
  paper_type: string;
  page_count: number;
  dpi: number;
  bleed_in: number;
  trim_width_in: number;
  trim_height_in: number;
  spine_width_in: number;
  total_width_in: number;
  total_height_in: number;
  total_width_px: number;
  total_height_px: number;
  notes: string[];
}

export type KDPDimensions = KDPEbookDimensions | KDPPaperbackDimensions;

export interface CoverChoice {
  value: string;
  label: string;
}

export interface CoverChoices {
  trim_sizes: CoverChoice[];
  paper_types: CoverChoice[];
  cover_types: CoverChoice[];
}

// ============================================================
// PIPELINE / DASHBOARD TYPES
// ============================================================
export interface PipelineStats {
  status_counts: Record<string, number>;
  totals: {
    books: number;
    published: number;
    revenue_usd: number;
    words: number;
    avg_ai_detection: number;
    avg_plagiarism: number;
  };
  chapters: {
    total: number;
    approved: number;
    published: number;
    in_review: number;
  };
  recent_books: {
    id: number;
    title: string;
    pen_name: string;
    lifecycle_status: string;
    progress: number;
    current_word_count: number;
    updated_at: string;
  }[];
}

// ============================================================
// KEYWORD RESEARCH
// ============================================================
export interface KeywordPrimary {
  keyword: string;
  volume?: number;
  competition?: string;
}

export interface CompetitorAsin {
  asin: string;
  title?: string;
  bsr?: number;
  reviews?: number;
  rating?: number;
  price?: number;
}

export interface KeywordResearch {
  id: number;
  book: number;
  primary_keywords: KeywordPrimary[];
  kdp_backend_keywords: string[];
  kdp_category_1: string;
  kdp_category_2: string;
  suggested_title: string;
  suggested_subtitle: string;
  competitor_asins: CompetitorAsin[];
  avg_competitor_reviews: number;
  keyword_search_volume: Record<string, number>;
  is_approved: boolean;
  approved_at: string | null;
  last_research_at: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// STORY BIBLE
// ============================================================
export interface StoryBible {
  id: number;
  book: number;
  characters: Record<string, unknown> | unknown[];
  world_rules: Record<string, unknown> | unknown[];
  timeline: Record<string, unknown> | unknown[];
  four_act_outline: Record<string, unknown> | unknown[];
  clues_tracker: Record<string, unknown> | unknown[];
  themes: string;
  tone: string;
  pov: string;
  tense: string;
  summary_for_ai: string;
  created_at: string;
  updated_at: string;
}

// ============================================================
// REVIEW TRACKER
// ============================================================
export interface ReviewTracker {
  id: number;
  book: number;
  total_reviews: number;
  avg_rating: number;
  reviews_week_1: number;
  reviews_week_2: number;
  reviews_week_3: number;
  reviews_week_4: number;
  positive_themes: string[];
  negative_themes: string[];
  arc_emails_sent: number;
  arc_reviews_received: number;
  arc_conversion_rate: number;
  rating_distribution: Record<string, number>;
  last_scraped: string | null;
}

// ============================================================
// ADS PERFORMANCE
// ============================================================
export interface AdsPerformance {
  id: number;
  book: number;
  report_date: string;
  impressions: number;
  clicks: number;
  spend_usd: string | number;
  sales_usd: string | number;
  acos: number | null;
  ctr: number | null;
  cpc: string | number | null;
  orders: number;
  units_sold: number;
}

// ============================================================
// ANALYTICS SUMMARY
// ============================================================
export interface AnalyticsBook {
  id: number;
  title: string;
  pen_name: string;
  lifecycle_status: string;
  asin: string | null;
  bsr: number | null;
  total_revenue_usd: number;
  current_price_usd: number;
  reviews: {
    total_reviews: number;
    avg_rating: number;
    arc_reviews_received: number;
  };
  ads_30d: {
    spend: number;
    sales: number;
    clicks: number;
    impressions: number;
    orders: number;
    acos: number | null;
  };
}

export interface AnalyticsSummary {
  books: AnalyticsBook[];
  totals: {
    revenue_usd: number;
    ads_spend_30d: number;
    ads_sales_30d: number;
    overall_acos: number | null;
    total_books: number;
  };
}

// ============================================================
// API PAGINATED RESPONSE
// ============================================================
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ============================================================
// STRIPE TYPES
// ============================================================
export interface StripeCheckoutSession {
  sessionId: string;
  url: string;
}

export interface CreateCheckoutParams {
  type: 'chapter' | 'subscription';
  chapterId?: number;
  plan?: 'monthly' | 'annual';
  successUrl: string;
  cancelUrl: string;
}
