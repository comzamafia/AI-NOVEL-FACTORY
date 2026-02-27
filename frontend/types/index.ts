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
  book_count?: number;
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
  | 'bible_generation'
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

export interface ReviewTracker {
  book: number;
  total_reviews: number;
  avg_rating: number;
  reviews_week_1: number;
  reviews_week_2: number;
  reviews_week_3: number;
  reviews_week_4: number;
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
