import Image from 'next/image';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ExternalLink, BookOpen, Lock, ChevronRight, ImageIcon } from 'lucide-react';
import { getBook, getChapters, getActiveDescription, buildCoverUrl } from '@/lib/api';
import StarRating from '@/components/StarRating';
import UpsellBanner from '@/components/UpsellBanner';
import type { Chapter } from '@/types';

export const revalidate = 120;

interface BookPageProps {
  params: { id: string };
}

export async function generateMetadata({ params }: BookPageProps) {
  const book = await getBook(params.id).catch(() => null);
  if (!book) return { title: 'Book not found' };
  return {
    title: `${book.title} — NovelFactory`,
    description: book.synopsis || `Read ${book.title} on NovelFactory.`,
  };
}

export default async function BookPage({ params }: BookPageProps) {
  const book = await getBook(params.id).catch(() => null);
  if (!book) notFound();

  const penName = typeof book.pen_name === 'object' ? book.pen_name : null;

  // Fetch description and chapters in parallel
  const [description, chaptersData] = await Promise.allSettled([
    getActiveDescription(params.id),
    getChapters({ book: params.id, is_published: true }),
  ]);

  const activeDesc = description.status === 'fulfilled' ? description.value : null;
  const chapters: Chapter[] =
    chaptersData.status === 'fulfilled' ? chaptersData.value.results : [];

  const coverUrl = buildCoverUrl(book);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Breadcrumb */}
      <nav className="text-sm text-slate-500 mb-8 flex items-center gap-2">
        <Link href="/" className="hover:text-slate-300">Home</Link>
        <ChevronRight size={14} />
        <Link href="/books" className="hover:text-slate-300">Books</Link>
        <ChevronRight size={14} />
        <span className="text-slate-300 truncate max-w-xs">{book.title}</span>
      </nav>

      {/* Main layout */}
      <div className="flex flex-col lg:flex-row gap-10">
        {/* Left: Cover */}
        <div className="flex-shrink-0 flex flex-col items-center lg:items-start gap-4">
          <Image
            src={coverUrl}
            alt={book.title}
            width={280}
            height={420}
            className="rounded-2xl shadow-2xl object-cover border border-slate-700"
            unoptimized
          />

          {/* Buy on Amazon */}
          {book.amazon_url && (
            <a
              href={book.amazon_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 w-full justify-center bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold py-3 px-6 rounded-xl transition-colors"
            >
              <ExternalLink size={16} />
              Buy on Amazon{book.current_price_usd ? ` $${parseFloat(String(book.current_price_usd)).toFixed(2)}` : ''}
            </a>
          )}

          {/* Covers link */}
          <Link
            href={`/books/${params.id}/covers`}
            className="flex items-center gap-2 w-full justify-center bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-sm font-medium py-2.5 px-4 rounded-xl border border-slate-700 transition-colors"
          >
            <ImageIcon size={15} />
            Manage KDP Covers
          </Link>

          {/* Stats */}
          <div className="w-full grid grid-cols-2 gap-2 text-center">
            {book.published_chapter_count !== undefined && (
              <div className="bg-slate-800 rounded-xl p-3 border border-slate-700">
                <p className="text-amber-400 text-xl font-bold">{book.published_chapter_count}</p>
                <p className="text-slate-400 text-xs">Chapters</p>
              </div>
            )}
            {book.asin && (
              <div className="bg-slate-800 rounded-xl p-3 border border-slate-700">
                <p className="text-amber-400 text-xs font-mono break-all">{book.asin}</p>
                <p className="text-slate-400 text-xs">ASIN</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: Details */}
        <div className="flex-1 min-w-0">
          {/* Author */}
          {penName && (
            <Link
              href={`/authors/${penName.id}`}
              className="inline-flex items-center gap-2 text-amber-400 hover:text-amber-300 text-sm font-medium mb-3"
            >
              {penName.name} · {penName.niche_genre}
            </Link>
          )}

          <h1 className="text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-3">
            {book.title}
          </h1>

          {/* Rating */}
          {book.avg_rating !== undefined && book.avg_rating !== null && (
            <div className="mb-4">
              <StarRating rating={book.avg_rating} count={book.review_count} />
            </div>
          )}

          {/* Synopsis */}
          {book.synopsis && (
            <p className="text-slate-300 text-lg leading-relaxed mb-6">{book.synopsis}</p>
          )}

          {/* Rich description from BookDescription model */}
          {activeDesc?.description_html && (
            <div
              className="prose prose-invert prose-slate max-w-none text-slate-300 leading-relaxed mb-6 [&_b]:text-white [&_em]:text-amber-300"
              dangerouslySetInnerHTML={{ __html: activeDesc.description_html }}
            />
          )}

          {/* Upsell banner */}
          <UpsellBanner
            bookTitle={book.title}
            amazonUrl={book.amazon_url}
            price={book.current_price_usd || 3.99}
          />

          {/* Chapter list */}
          <div className="mt-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <BookOpen size={20} className="text-amber-400" />
              Chapters
            </h2>

            {chapters.length > 0 ? (
              <div className="flex flex-col gap-2">
                {chapters.map((ch) => {
                  const isFree = ch.is_free || ch.chapter_number === 1;
                  return (
                    <Link
                      key={ch.id}
                      href={`/books/${book.id}/chapters/${ch.chapter_number}`}
                      className="flex items-center justify-between p-4 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-amber-500/50 transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-slate-500 text-sm w-8 text-right font-mono">
                          {ch.chapter_number}
                        </span>
                        <span className="text-white group-hover:text-amber-300 transition-colors">
                          {ch.title || `Chapter ${ch.chapter_number}`}
                        </span>
                        {isFree && (
                          <span className="text-xs bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-0.5 rounded-full">
                            FREE
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-slate-500 text-sm">
                        {ch.word_count && <span>{ch.word_count.toLocaleString()} words</span>}
                        {!isFree && <Lock size={13} className="text-slate-500" />}
                        <ChevronRight size={14} className="group-hover:text-amber-400 group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </Link>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-10 text-slate-500 bg-slate-800 rounded-2xl border border-slate-700">
                <p>No published chapters yet.</p>
                <p className="text-sm mt-1">New chapters drop every 3 days!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
