import Link from 'next/link';
import { BookOpen, Zap, Users, Star } from 'lucide-react';
import BookCard from '@/components/BookCard';
import AuthorCard from '@/components/AuthorCard';
import { getPublishedBooks, getPenNames } from '@/lib/api';

export const revalidate = 60;

export default async function HomePage() {
  const [booksData, authorsData] = await Promise.allSettled([
    getPublishedBooks(1),
    getPenNames({ page: 1 }),
  ]);

  const books = booksData.status === 'fulfilled' ? booksData.value.results.slice(0, 8) : [];
  const authors = authorsData.status === 'fulfilled' ? authorsData.value.results.slice(0, 4) : [];

  return (
    <div>
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-40 -left-40 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28 text-center">
          <div className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm px-4 py-1.5 rounded-full mb-6">
            <Zap size={14} className="fill-amber-400 text-amber-400" />
            New chapters every 3 days
          </div>
          <h1 className="text-5xl lg:text-7xl font-extrabold text-white leading-tight mb-6">
            Stories Crafted by{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
              AI. Loved by Humans.
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-8">
            Dive into page-turning thrillers, mysteries, and suspense novels — published chapter by chapter.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link href="/books" className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-8 py-3.5 rounded-full text-lg transition-colors shadow-lg shadow-amber-500/25">
              Browse All Books
            </Link>
            <Link href="/subscribe" className="bg-slate-700 hover:bg-slate-600 text-white font-semibold px-8 py-3.5 rounded-full text-lg border border-slate-600 transition-colors">
              Subscribe .99/mo
            </Link>
          </div>
          <div className="flex items-center justify-center gap-6 mt-10 text-sm text-slate-500 flex-wrap">
            <span className="flex items-center gap-1.5"><BookOpen size={14} className="text-amber-400" />Growing library</span>
            <span className="flex items-center gap-1.5"><Users size={14} className="text-amber-400" />Multiple pen names</span>
            <span className="flex items-center gap-1.5"><Star size={14} className="text-amber-400 fill-amber-400" />New chapters 3x/week</span>
          </div>
        </div>
      </section>

      {/* Featured Books */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex items-end justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white">Featured Books</h2>
            <p className="text-slate-400 mt-1">Latest releases from our AI authors</p>
          </div>
          <Link href="/books" className="text-amber-400 hover:text-amber-300 text-sm font-medium">View all →</Link>
        </div>
        {books.length > 0 ? (
          <div className="flex flex-wrap gap-5">
            {books.map((book) => (
              <BookCard key={book.id} book={book} size="md" />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-slate-500">
            <BookOpen size={48} className="mx-auto mb-4 opacity-40" />
            <p>No published books yet. Check back soon!</p>
          </div>
        )}
      </section>

      {/* How it works */}
      <section className="bg-slate-800/50 border-y border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <h2 className="text-3xl font-bold text-white text-center mb-10">How it Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: '📖', title: 'Browse & Preview', desc: 'Every book has free preview chapters. No sign-up needed to start reading.' },
              { icon: '🔓', title: 'Unlock Chapters', desc: 'Buy individual chapters for .99 each, or subscribe for unlimited access.' },
              { icon: '🛒', title: 'Own the Full Book', desc: 'Grab the complete book on Amazon Kindle for .99 and read at your own pace.' },
            ].map((item) => (
              <div key={item.title} className="text-center p-6 rounded-2xl bg-slate-800 border border-slate-700">
                <div className="text-4xl mb-4">{item.icon}</div>
                <h3 className="text-white font-bold text-lg mb-2">{item.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Authors */}
      {authors.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex items-end justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-white">Meet the Authors</h2>
              <p className="text-slate-400 mt-1">AI pen names with their own unique voice</p>
            </div>
            <Link href="/authors" className="text-amber-400 hover:text-amber-300 text-sm font-medium">All authors →</Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {authors.map((author) => (
              <AuthorCard key={author.id} author={author} />
            ))}
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-16">
        <div className="rounded-3xl bg-gradient-to-r from-amber-500 to-amber-600 p-10 text-center">
          <h2 className="text-3xl font-extrabold text-slate-900 mb-3">Unlimited Reading for .99/month</h2>
          <p className="text-slate-800 text-lg mb-6">Access every book, every chapter — including new releases the moment they drop.</p>
          <Link href="/subscribe" className="bg-slate-900 hover:bg-slate-800 text-white font-bold px-10 py-3.5 rounded-full text-lg transition-colors inline-block">
            Start Your Subscription
          </Link>
        </div>
      </section>
    </div>
  );
}
