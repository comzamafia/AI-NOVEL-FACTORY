import Image from 'next/image';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ChevronRight, BookOpen } from 'lucide-react';
import { getPenName, getBooksByAuthor, buildAvatarUrl } from '@/lib/api';
import BookCard from '@/components/BookCard';

export const revalidate = 120;

interface AuthorPageProps {
  params: { id: string };
}

export async function generateMetadata({ params }: AuthorPageProps) {
  const author = await getPenName(params.id).catch(() => null);
  if (!author) return { title: 'Author not found' };
  return {
    title: `${author.name} — NovelFactory`,
    description: author.bio || `Books by ${author.name} on NovelFactory.`,
  };
}

export default async function AuthorPage({ params }: AuthorPageProps) {
  const author = await getPenName(params.id).catch(() => null);
  if (!author) notFound();

  const booksData = await getBooksByAuthor(params.id).catch(() => ({ results: [], count: 0 }));
  const books = booksData.results;

  const avatarUrl = buildAvatarUrl(author);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Breadcrumb */}
      <nav className="text-sm text-slate-500 mb-8 flex items-center gap-2">
        <Link href="/" className="hover:text-slate-300">Home</Link>
        <ChevronRight size={14} />
        <Link href="/authors" className="hover:text-slate-300">Authors</Link>
        <ChevronRight size={14} />
        <span className="text-slate-300">{author.name}</span>
      </nav>

      {/* Author header */}
      <div className="flex flex-col sm:flex-row gap-8 items-center sm:items-start mb-12 p-8 rounded-3xl bg-slate-800 border border-slate-700">
        <Image
          src={avatarUrl}
          alt={author.name}
          width={140}
          height={140}
          className="rounded-full object-cover border-4 border-slate-600 flex-shrink-0"
          unoptimized
        />

        <div className="flex-1 text-center sm:text-left">
          <div className="flex flex-wrap items-center gap-3 mb-2 justify-center sm:justify-start">
            <h1 className="text-4xl font-extrabold text-white">{author.name}</h1>
            {author.niche_genre && (
              <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-sm px-3 py-0.5 rounded-full">
                {author.niche_genre}
              </span>
            )}
          </div>

          {author.bio && (
            <p className="text-slate-300 text-lg leading-relaxed mt-3 max-w-2xl">{author.bio}</p>
          )}

          <div className="flex items-center gap-2 mt-4 text-slate-400 text-sm justify-center sm:justify-start">
            <BookOpen size={15} className="text-amber-400" />
            <span>{booksData.count} book{booksData.count !== 1 ? 's' : ''} published</span>
          </div>
        </div>
      </div>

      {/* Books by author */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-6">Books by {author.name}</h2>

        {books.length > 0 ? (
          <div className="flex flex-wrap gap-5">
            {books.map((book) => (
              <BookCard key={book.id} book={book} size="md" />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-slate-500 bg-slate-800 rounded-2xl border border-slate-700">
            <BookOpen size={40} className="mx-auto mb-3 opacity-40" />
            <p>No books published yet. Stay tuned!</p>
          </div>
        )}
      </div>
    </div>
  );
}
