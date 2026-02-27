import BookCard from '@/components/BookCard';
import { getBooks, getPenNames } from '@/lib/api';
import { BookOpen, Filter } from 'lucide-react';
import Link from 'next/link';

export const revalidate = 60;

export const metadata = {
  title: 'All Books — NovelFactory',
  description: 'Browse all AI-crafted novels available on NovelFactory.',
};

interface BooksPageProps {
  searchParams: { page?: string; pen_name?: string };
}

export default async function BooksPage({ searchParams }: BooksPageProps) {
  const page = parseInt(searchParams.page || '1', 10);
  const penNameFilter = searchParams.pen_name;

  const [data, penNamesData] = await Promise.all([
    getBooks({
      page,
      ordering: '-created_at',
      ...(penNameFilter ? { pen_name: Number(penNameFilter) } : {}),
    }).catch(() => ({ results: [], count: 0, next: null, previous: null })),
    getPenNames().catch(() => ({ results: [], count: 0 })),
  ]);

  const books = data.results;
  const authors = penNamesData.results;
  const totalPages = Math.ceil(data.count / 20);

  const buildPageUrl = (p: number) => {
    const params = new URLSearchParams();
    params.set('page', String(p));
    if (penNameFilter) params.set('pen_name', penNameFilter);
    return `/books?${params.toString()}`;
  };

  const buildFilterUrl = (id?: number) => {
    if (!id) return '/books';
    return `/books?pen_name=${id}`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-extrabold text-white mb-2">All Books</h1>
        <p className="text-slate-400">
          {data.count > 0
            ? `${data.count} book${data.count !== 1 ? 's' : ''} in the library`
            : 'Our growing library of AI-crafted novels'}
        </p>
      </div>

      {/* Genre / Author filter */}
      {authors.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-8">
          <span className="text-slate-500 text-sm flex items-center gap-1.5 mr-1">
            <Filter size={14} />
            Filter:
          </span>
          <Link
            href="/books"
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors border ${
              !penNameFilter
                ? 'bg-amber-500 text-slate-900 border-amber-500'
                : 'text-slate-400 border-slate-600 hover:border-slate-400 hover:text-slate-200'
            }`}
          >
            All genres
          </Link>
          {authors.map((a) => (
            <Link
              key={a.id}
              href={buildFilterUrl(a.id)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors border ${
                penNameFilter === String(a.id)
                  ? 'bg-amber-500 text-slate-900 border-amber-500'
                  : 'text-slate-400 border-slate-600 hover:border-slate-400 hover:text-slate-200'
              }`}
            >
              {a.niche_genre}
            </Link>
          ))}
        </div>
      )}

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
                <Link
                  href={buildPageUrl(page - 1)}
                  className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm"
                >
                  ← Previous
                </Link>
              )}
              <span className="text-slate-400 text-sm px-4">
                Page {page} of {totalPages}
              </span>
              {page < totalPages && (
                <Link
                  href={buildPageUrl(page + 1)}
                  className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm"
                >
                  Next →
                </Link>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-24 text-slate-500">
          <BookOpen size={56} className="mx-auto mb-4 opacity-40" />
          <p className="text-xl">No books found.</p>
          {penNameFilter && (
            <Link href="/books" className="mt-3 inline-block text-amber-400 hover:text-amber-300 text-sm">
              Clear filter
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
