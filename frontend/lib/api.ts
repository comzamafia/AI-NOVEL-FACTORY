import axios from 'axios';
import type {
  Book,
  PenName,
  Chapter,
  BookDescription,
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
