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
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

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