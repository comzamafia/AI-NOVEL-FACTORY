import BookCard from '@/components/BookCard';
import { getBooks } from '@/lib/api';
import { BookOpen } from 'lucide-react';

export const revalidate = 60;

export const metadata = {
  title: 'All Books — NovelFactory',
  description: 'Browse all AI-crafted novels available on NovelFactory.',
};

interface BooksPageProps {
  searchParams: { page?: string; q?: string };
}

export default async function BooksPage({ searchParams }: BooksPageProps) {
  const page = parseInt(searchParams.page || '1', 10);

  const data = await getBooks({
    page,
    ordering: '-created_at',
  }).catch(() => ({ results: [], count: 0, next: null, previous: null }));

  const books = data.results;
  const totalPages = Math.ceil(data.count / 20);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-4xl font-extrabold text-white mb-2">All Books</h1>
        <p className="text-slate-400">
          {data.count > 0
            ? `${data.count} book${data.count !== 1 ? 's' : ''} in the library`
            : 'Our growing library of AI-crafted novels'}
        </p>
      </div>

      {/* Books grid */}
      {books.length > 0 ? (
        <>
          <div className="flex flex-wrap gap-5">
            {books.map((book) => (
              <BookCard key={book.id} book={book} size="md" />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-12">
              {page > 1 && (
                <a
                  href={`/books?page=${page - 1}`}
                  className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm"
                >
                  ← Previous
                </a>
              )}
              <span className="text-slate-400 text-sm px-4">
                Page {page} of {totalPages}
              </span>
              {page < totalPages && (
                <a
                  href={`/books?page=${page + 1}`}
                  className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm"
                >
                  Next →
                </a>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-24 text-slate-500">
          <BookOpen size={56} className="mx-auto mb-4 opacity-40" />
          <p className="text-xl">No books available yet.</p>
          <p className="text-sm mt-2">Check back soon — new titles drop regularly!</p>
        </div>
      )}
    </div>
  );
}
