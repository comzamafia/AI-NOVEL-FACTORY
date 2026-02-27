import { Suspense } from 'react';
import Link from 'next/link';
import { Search, BookOpen, Users } from 'lucide-react';
import BookCard from '@/components/BookCard';
import AuthorCard from '@/components/AuthorCard';
import SearchInput from '@/components/SearchInput';
import { searchBooks, searchPenNames } from '@/lib/api';

export const dynamic = 'force-dynamic';

export function generateMetadata({ searchParams }: { searchParams: { q?: string } }) {
  const q = searchParams.q || '';
  return {
    title: q ? `"${q}" — Search | NovelFactory` : 'Search — NovelFactory',
  };
}

async function SearchResults({ q }: { q: string }) {
  if (!q.trim()) {
    return (
      <div className="text-center py-24 text-slate-500">
        <Search size={56} className="mx-auto mb-4 opacity-30" />
        <p className="text-xl">Start typing to search books and authors.</p>
      </div>
    );
  }

  const [booksData, authorsData] = await Promise.allSettled([
    searchBooks(q),
    searchPenNames(q),
  ]);

  const books = booksData.status === 'fulfilled' ? booksData.value.results : [];
  const authors = authorsData.status === 'fulfilled' ? authorsData.value.results : [];
  const total = books.length + authors.length;

  if (total === 0) {
    return (
      <div className="text-center py-24 text-slate-500">
        <Search size={56} className="mx-auto mb-4 opacity-30" />
        <p className="text-xl font-semibold text-slate-400">No results for &ldquo;{q}&rdquo;</p>
        <p className="text-sm mt-2">Try a different title, author, or genre.</p>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      {/* Authors */}
      {authors.length > 0 && (
        <section>
          <h2 className="text-xl font-bold text-white mb-5 flex items-center gap-2">
            <Users size={18} className="text-amber-400" />
            Authors
            <span className="text-slate-500 text-sm font-normal ml-1">({authors.length})</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {authors.map((a) => (
              <AuthorCard key={a.id} author={a} />
            ))}
          </div>
        </section>
      )}

      {/* Books */}
      {books.length > 0 && (
        <section>
          <h2 className="text-xl font-bold text-white mb-5 flex items-center gap-2">
            <BookOpen size={18} className="text-amber-400" />
            Books
            <span className="text-slate-500 text-sm font-normal ml-1">({books.length})</span>
          </h2>
          <div className="flex flex-wrap gap-5">
            {books.map((book) => (
              <BookCard key={book.id} book={book} size="md" />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default function SearchPage({ searchParams }: { searchParams: { q?: string } }) {
  const q = searchParams.q || '';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-4xl font-extrabold text-white mb-6 flex items-center gap-3">
          <Search className="text-amber-400" size={32} />
          Search
        </h1>
        <SearchInput defaultValue={q} />
      </div>

      {q && (
        <p className="text-slate-400 text-sm mb-8">
          Results for <span className="text-white font-semibold">&ldquo;{q}&rdquo;</span>
        </p>
      )}

      <Suspense
        fallback={
          <div className="text-center py-16 text-slate-500">
            <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            Searching...
          </div>
        }
      >
        <SearchResults q={q} />
      </Suspense>
    </div>
  );
}
