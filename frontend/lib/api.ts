import axios from 'axios';
import type {
  Book,
  PenName,
  Chapter,
  BookDescription,
  BookCover,
  KDPDimensions,
  CoverChoices,
  PipelineStats,
  PaginatedResponse,
  KeywordResearch,
  StoryBible,
  AnalyticsSummary,
  ReviewTracker,
  AdsPerformance,
  PricingStrategy,
  DistributionChannel,
  CompetitorBook,
  ARCReader,
  StyleFingerprint,
  BookDescriptionFull,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Normalise error responses so callers always receive a plain Error with a
// human-readable message rather than raw Axios errors.
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (axios.isAxiosError(error)) {
      const detail =
        error.response?.data?.detail ??
        error.response?.data?.error ??
        error.response?.data?.message ??
        error.message;
      return Promise.reject(new Error(String(detail)));
    }
    return Promise.reject(error);
  },
);

// ----------------------------------------------------------------
// Books
// ----------------------------------------------------------------
export async function getBooks(params?: {
  page?: number;
  pen_name?: number;
  lifecycle_status?: string;
  ordering?: string;
}): Promise<PaginatedResponse<Book>> {
  const { data } = await apiClient.get<PaginatedResponse<Book>>('/books/', { params });
  return data;
}

export async function getPublishedBooks(page = 1): Promise<PaginatedResponse<Book>> {
  return getBooks({ page, lifecycle_status: 'published_kdp,published_all', ordering: '-created_at' });
}

export async function getBook(id: number | string): Promise<Book> {
  const { data } = await apiClient.get<Book>(`/books/${id}/`);
  return data;
}

// ----------------------------------------------------------------
// Pen Names (Authors)
// ----------------------------------------------------------------
export async function getPenNames(params?: { page?: number }): Promise<PaginatedResponse<PenName>> {
  const { data } = await apiClient.get<PaginatedResponse<PenName>>('/pen-names/', { params });
  return data;
}

export async function getPenName(id: number | string): Promise<PenName> {
  const { data } = await apiClient.get<PenName>(`/pen-names/${id}/`);
  return data;
}

export async function getBooksByAuthor(penNameId: number | string, page = 1): Promise<PaginatedResponse<Book>> {
  return getBooks({ pen_name: Number(penNameId), page });
}

// ----------------------------------------------------------------
// Search
// ----------------------------------------------------------------
export async function searchBooks(q: string, page = 1): Promise<PaginatedResponse<Book>> {
  const { data } = await apiClient.get<PaginatedResponse<Book>>('/books/', {
    params: { search: q, page, ordering: '-created_at' },
  });
  return data;
}

export async function searchPenNames(q: string): Promise<PaginatedResponse<PenName>> {
  const { data } = await apiClient.get<PaginatedResponse<PenName>>('/pen-names/', {
    params: { search: q },
  });
  return data;
}

// ----------------------------------------------------------------
// Chapters
// ----------------------------------------------------------------
export async function getChapters(params: {
  book?: number | string;
  is_published?: boolean;
  page?: number;
}): Promise<PaginatedResponse<Chapter>> {
  const { data } = await apiClient.get<PaginatedResponse<Chapter>>('/chapters/', { params });
  return data;
}

export async function getChapter(id: number | string): Promise<Chapter> {
  const { data } = await apiClient.get<Chapter>(`/chapters/${id}/`);
  return data;
}

export async function getChapterByNumber(bookId: number | string, chapterNum: number | string): Promise<Chapter> {
  const { data } = await apiClient.get<PaginatedResponse<Chapter>>('/chapters/', {
    params: { book: bookId, chapter_number: chapterNum },
  });
  if (data.results.length === 0) throw new Error('Chapter not found');
  return data.results[0];
}

// ----------------------------------------------------------------
// Book Descriptions
// ----------------------------------------------------------------
export async function getActiveDescription(bookId: number | string): Promise<BookDescription | null> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<BookDescription>>('/book-descriptions/', {
      params: { book: bookId, is_active: true },
    });
    return data.results[0] || null;
  } catch {
    return null;
  }
}

// ----------------------------------------------------------------
// Book Covers (KDP)
// ----------------------------------------------------------------
export async function getCovers(params?: {
  book?: number | string;
  cover_type?: string;
  is_active?: boolean;
}): Promise<PaginatedResponse<BookCover>> {
  const { data } = await apiClient.get<PaginatedResponse<BookCover>>('/covers/', { params });
  return data;
}

export async function getCover(id: number | string): Promise<BookCover> {
  const { data } = await apiClient.get<BookCover>(`/covers/${id}/`);
  return data;
}

export async function createCover(formData: FormData): Promise<BookCover> {
  const { data } = await apiClient.post<BookCover>('/covers/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function updateCover(id: number | string, formData: FormData): Promise<BookCover> {
  const { data } = await apiClient.patch<BookCover>(`/covers/${id}/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function activateCover(id: number | string): Promise<BookCover> {
  const { data } = await apiClient.post<BookCover>(`/covers/${id}/activate/`);
  return data;
}

export async function deleteCover(id: number | string): Promise<void> {
  await apiClient.delete(`/covers/${id}/`);
}

export async function calculateKDPDimensions(params: {
  cover_type: string;
  trim_size?: string;
  paper_type?: string;
  page_count?: number;
}): Promise<KDPDimensions> {
  const { data } = await apiClient.get<KDPDimensions>('/covers/calculate/', { params });
  return data;
}

export async function getCoverChoices(): Promise<CoverChoices> {
  const { data } = await apiClient.get<CoverChoices>('/covers/choices/');
  return data;
}

// ----------------------------------------------------------------
// Pipeline / Dashboard
// ----------------------------------------------------------------
export async function getPipelineStats(): Promise<PipelineStats> {
  const { data } = await apiClient.get<PipelineStats>('/books/pipeline_stats/');
  return data;
}

// ----------------------------------------------------------------
// Lifecycle Actions (FSM transitions)
// ----------------------------------------------------------------
export type LifecycleAction =
  | 'start_keyword_research'
  | 'approve_keywords'
  | 'start_description_generation'
  | 'approve_description'
  | 'start_bible_generation'
  | 'approve_bible'
  | 'start_writing'
  | 'submit_for_qa'
  | 'approve_for_export'
  | 'publish_to_kdp';

export async function triggerLifecycleAction(bookId: number | string, action: LifecycleAction): Promise<{ lifecycle_status: string; message: string }> {
  const { data } = await apiClient.post(`/books/${bookId}/${action}/`);
  return data;
}

// ----------------------------------------------------------------
// Export
// ----------------------------------------------------------------
export async function exportBook(bookId: number | string, format: 'docx' | 'epub'): Promise<void> {
  const response = await apiClient.post(
    `/books/${bookId}/export/`,
    { format },
    { responseType: 'blob' },
  );
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const a = document.createElement('a');
  a.href = url;
  const disposition = response.headers['content-disposition'] || '';
  const filename = disposition.match(/filename="?([^"]+)"?/)?.[1] || `book-${bookId}.${format}`;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}

// ----------------------------------------------------------------
// Chapter Actions
// ----------------------------------------------------------------
export async function approveChapter(chapterId: number | string): Promise<{ chapter_status: string; message: string }> {
  const { data } = await apiClient.post(`/chapters/${chapterId}/approve/`);
  return data;
}

export async function rejectChapter(chapterId: number | string, notes: string): Promise<{ chapter_status: string; message: string }> {
  const { data } = await apiClient.post(`/chapters/${chapterId}/reject/`, { notes });
  return data;
}

export async function markChapterReady(chapterId: number | string): Promise<{ chapter_status: string; message: string }> {
  const { data } = await apiClient.post(`/chapters/${chapterId}/mark_ready_to_write/`);
  return data;
}

export async function updateChapter(
  chapterId: number | string,
  payload: { is_published?: boolean; is_free?: boolean; title?: string }
): Promise<Chapter> {
  const { data } = await apiClient.patch<Chapter>(`/chapters/${chapterId}/`, payload);
  return data;
}

// ----------------------------------------------------------------
// Book Create / Edit / Delete (admin actions)
// ----------------------------------------------------------------
export interface BookCreatePayload {
  title: string;
  subtitle?: string;
  synopsis?: string;
  pen_name: number;
  target_chapter_count?: number;
  target_word_count?: number;
  genre?: string;
}

export async function createBook(payload: BookCreatePayload): Promise<Book> {
  const { data } = await apiClient.post<Book>('/books/', payload);
  return data;
}

export async function updateBook(id: number | string, payload: Partial<BookCreatePayload>): Promise<Book> {
  const { data } = await apiClient.patch<Book>(`/books/${id}/`, payload);
  return data;
}

export async function deleteBook(id: number | string): Promise<void> {
  await apiClient.delete(`/books/${id}/`);
}

// ----------------------------------------------------------------
// Pen Name Create / Edit / Delete (admin actions)
// ----------------------------------------------------------------
export interface PenNamePayload {
  name: string;
  niche_genre?: string;
  bio?: string;
  writing_style_prompt?: string;
  website_url?: string;
  amazon_author_url?: string;
}

export async function createPenName(payload: PenNamePayload): Promise<PenName> {
  const { data } = await apiClient.post<PenName>('/pen-names/', payload);
  return data;
}

export async function updatePenName(id: number | string, payload: Partial<PenNamePayload>): Promise<PenName> {
  const { data } = await apiClient.patch<PenName>(`/pen-names/${id}/`, payload);
  return data;
}

export async function deletePenName(id: number | string): Promise<void> {
  await apiClient.delete(`/pen-names/${id}/`);
}

// ----------------------------------------------------------------
// Keyword Research
// ----------------------------------------------------------------
export async function getKeywordResearch(bookId: number | string): Promise<KeywordResearch | null> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<KeywordResearch>>('/keyword-research/', {
      params: { book: bookId },
    });
    return data.results[0] || null;
  } catch {
    return null;
  }
}

export async function updateKeywordResearch(
  id: number | string,
  payload: Partial<KeywordResearch>
): Promise<KeywordResearch> {
  const { data } = await apiClient.patch<KeywordResearch>(`/keyword-research/${id}/`, payload);
  return data;
}

export async function approveKeywordResearch(id: number | string): Promise<{ status: string; message: string }> {
  const { data } = await apiClient.post(`/keyword-research/${id}/approve/`);
  return data;
}

export async function rerunKeywordResearch(id: number | string): Promise<{ status: string; message: string }> {
  const { data } = await apiClient.post(`/keyword-research/${id}/re_run/`);
  return data;
}

export async function validateKeywords(id: number | string): Promise<{ valid: boolean; errors: string[]; keyword_count: number }> {
  const { data } = await apiClient.get(`/keyword-research/${id}/validate/`);
  return data;
}

// ----------------------------------------------------------------
// Story Bible
// ----------------------------------------------------------------
export async function getStoryBible(bookId: number | string): Promise<StoryBible | null> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<StoryBible>>('/story-bibles/', {
      params: { book: bookId },
    });
    return data.results[0] || null;
  } catch {
    return null;
  }
}

export async function updateStoryBible(
  id: number | string,
  payload: Partial<StoryBible>
): Promise<StoryBible> {
  const { data } = await apiClient.patch<StoryBible>(`/story-bibles/${id}/`, payload);
  return data;
}

export async function generateBibleSummary(id: number | string): Promise<{ summary: string; message: string }> {
  const { data } = await apiClient.post(`/story-bibles/${id}/generate_summary/`);
  return data;
}

// ----------------------------------------------------------------
// Analytics
// ----------------------------------------------------------------
export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const { data } = await apiClient.get<AnalyticsSummary>('/books/analytics_summary/');
  return data;
}

// ----------------------------------------------------------------
// Review Tracker
// ----------------------------------------------------------------
export async function getReviewTracker(bookId: number | string): Promise<ReviewTracker | null> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<ReviewTracker>>('/review-trackers/', {
      params: { book: bookId },
    });
    return data.results[0] || null;
  } catch {
    return null;
  }
}

// ----------------------------------------------------------------
// Ads Performance
// ----------------------------------------------------------------
export async function getAdsPerformanceHistory(bookId: number | string): Promise<AdsPerformance[]> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<AdsPerformance>>('/ads-performance/', {
      params: { book: bookId, ordering: '-report_date' },
    });
    return data.results;
  } catch {
    return [];
  }
}

// ----------------------------------------------------------------
// Pricing Strategy
// ----------------------------------------------------------------
export async function getPricingStrategy(bookId: number | string): Promise<PricingStrategy | null> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<PricingStrategy>>('/pricing-strategies/', {
      params: { book: bookId },
    });
    return data.results[0] || null;
  } catch {
    return null;
  }
}

export async function updatePricingStrategy(
  id: number | string,
  payload: Partial<PricingStrategy>,
): Promise<PricingStrategy> {
  const { data } = await apiClient.patch<PricingStrategy>(`/pricing-strategies/${id}/`, payload);
  return data;
}

export async function logPriceChange(
  id: number | string,
  price: number,
  phase: string,
  reason: string,
): Promise<PricingStrategy> {
  const { data } = await apiClient.post<PricingStrategy>(`/pricing-strategies/${id}/log_change/`, {
    price, phase, reason,
  });
  return data;
}

// ----------------------------------------------------------------
// Distribution Channels
// ----------------------------------------------------------------
export async function getDistributionChannels(bookId: number | string): Promise<DistributionChannel[]> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<DistributionChannel>>('/distribution-channels/', {
      params: { book: bookId, ordering: 'platform' },
    });
    return data.results;
  } catch {
    return [];
  }
}

export async function createDistributionChannel(
  payload: Partial<DistributionChannel>,
): Promise<DistributionChannel> {
  const { data } = await apiClient.post<DistributionChannel>('/distribution-channels/', payload);
  return data;
}

export async function updateDistributionChannel(
  id: number | string,
  payload: Partial<DistributionChannel>,
): Promise<DistributionChannel> {
  const { data } = await apiClient.patch<DistributionChannel>(`/distribution-channels/${id}/`, payload);
  return data;
}

export async function deleteDistributionChannel(id: number | string): Promise<void> {
  await apiClient.delete(`/distribution-channels/${id}/`);
}

export async function getPlatformChoices(): Promise<{ value: string; label: string }[]> {
  try {
    const { data } = await apiClient.get<{ choices: { value: string; label: string }[] }>(
      '/distribution-channels/platform_choices/',
    );
    return data.choices;
  } catch {
    return [];
  }
}

// ----------------------------------------------------------------
// Utility helpers
// ----------------------------------------------------------------
export function buildCoverUrl(book: Book): string {
  if (book.cover_image_url) {
    if (book.cover_image_url.startsWith('http')) return book.cover_image_url;
    return `${API_BASE.replace('/api', '')}${book.cover_image_url}`;
  }
  return `https://placehold.co/400x600/1e293b/94a3b8?text=${encodeURIComponent(book.title)}`;
}

export function buildAvatarUrl(penName: PenName): string {
  if (penName.profile_image) {
    if (penName.profile_image.startsWith('http')) return penName.profile_image;
    return `${API_BASE.replace('/api', '')}${penName.profile_image}`;
  }
  return `https://placehold.co/200x200/0f172a/94a3b8?text=${encodeURIComponent(penName.name.charAt(0))}`;
}

// ----------------------------------------------------------------
// Competitor Books
// ----------------------------------------------------------------
export async function getCompetitorBooks(params?: { genre?: string; search?: string; ordering?: string }): Promise<CompetitorBook[]> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<CompetitorBook>>('/competitor-books/', { params });
    return data.results;
  } catch {
    return [];
  }
}

export async function createCompetitorBook(payload: Partial<CompetitorBook>): Promise<CompetitorBook> {
  const { data } = await apiClient.post<CompetitorBook>('/competitor-books/', payload);
  return data;
}

export async function updateCompetitorBook(id: number | string, payload: Partial<CompetitorBook>): Promise<CompetitorBook> {
  const { data } = await apiClient.patch<CompetitorBook>(`/competitor-books/${id}/`, payload);
  return data;
}

export async function deleteCompetitorBook(id: number | string): Promise<void> {
  await apiClient.delete(`/competitor-books/${id}/`);
}

export async function estimateCompetitorRevenue(id: number | string): Promise<CompetitorBook> {
  const { data } = await apiClient.post<CompetitorBook>(`/competitor-books/${id}/estimate_revenue/`);
  return data;
}

export async function getCompetitorGenres(): Promise<string[]> {
  try {
    const { data } = await apiClient.get<{ genres: string[] }>('/competitor-books/genre_choices/');
    return data.genres;
  } catch {
    return [];
  }
}

// ----------------------------------------------------------------
// ARC Readers
// ----------------------------------------------------------------
export async function getARCReaders(params?: { is_reliable?: boolean; search?: string }): Promise<ARCReader[]> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<ARCReader>>('/arc-readers/', { params });
    return data.results;
  } catch {
    return [];
  }
}

export async function createARCReader(payload: Partial<ARCReader>): Promise<ARCReader> {
  const { data } = await apiClient.post<ARCReader>('/arc-readers/', payload);
  return data;
}

export async function updateARCReader(id: number | string, payload: Partial<ARCReader>): Promise<ARCReader> {
  const { data } = await apiClient.patch<ARCReader>(`/arc-readers/${id}/`, payload);
  return data;
}

export async function deleteARCReader(id: number | string): Promise<void> {
  await apiClient.delete(`/arc-readers/${id}/`);
}

export async function markARCSent(id: number | string): Promise<ARCReader> {
  const { data } = await apiClient.post<ARCReader>(`/arc-readers/${id}/mark_sent/`);
  return data;
}

export async function markARCReviewed(id: number | string, rating?: number): Promise<ARCReader> {
  const { data } = await apiClient.post<ARCReader>(`/arc-readers/${id}/mark_reviewed/`, rating ? { rating } : {});
  return data;
}

// ----------------------------------------------------------------
// Style Fingerprint
// ----------------------------------------------------------------
export async function getStyleFingerprint(penNameId: number | string): Promise<StyleFingerprint | null> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<StyleFingerprint>>('/style-fingerprints/', {
      params: { pen_name: penNameId },
    });
    return data.results[0] ?? null;
  } catch {
    return null;
  }
}

export async function updateStyleFingerprint(id: number | string, payload: Partial<StyleFingerprint>): Promise<StyleFingerprint> {
  const { data } = await apiClient.patch<StyleFingerprint>(`/style-fingerprints/${id}/`, payload);
  return data;
}

export async function generateStylePrompt(id: number | string): Promise<{ style_system_prompt: string; fingerprint: StyleFingerprint }> {
  const { data } = await apiClient.post<{ style_system_prompt: string; fingerprint: StyleFingerprint }>(`/style-fingerprints/${id}/generate_prompt/`);
  return data;
}

export async function createStyleFingerprint(payload: Partial<StyleFingerprint>): Promise<StyleFingerprint> {
  const { data } = await apiClient.post<StyleFingerprint>('/style-fingerprints/', payload);
  return data;
}

// ----------------------------------------------------------------
// Book Descriptions (Full — A/B)
// ----------------------------------------------------------------
export async function getBookDescriptionsFull(bookId: number | string): Promise<BookDescriptionFull[]> {
  try {
    const { data } = await apiClient.get<PaginatedResponse<BookDescriptionFull>>('/book-descriptions-full/', {
      params: { book: bookId, ordering: 'version' },
    });
    return data.results;
  } catch {
    return [];
  }
}

export async function updateBookDescriptionFull(id: number | string, payload: Partial<BookDescriptionFull>): Promise<BookDescriptionFull> {
  const { data } = await apiClient.patch<BookDescriptionFull>(`/book-descriptions-full/${id}/`, payload);
  return data;
}

export async function setActiveDescription(id: number | string): Promise<BookDescriptionFull> {
  const { data } = await apiClient.post<BookDescriptionFull>(`/book-descriptions-full/${id}/set_active/`);
  return data;
}

export async function approveDescription(id: number | string): Promise<BookDescriptionFull> {
  const { data } = await apiClient.post<BookDescriptionFull>(`/book-descriptions-full/${id}/approve/`);
  return data;
}