import { notFound } from 'next/navigation';
import Link from 'next/link';
import { ChevronLeft, ChevronRight, BookOpen } from 'lucide-react';
import { getBook, getChapterByNumber, getChapters } from '@/lib/api';
import ChapterGate from '@/components/ChapterGate';
import UpsellBanner from '@/components/UpsellBanner';
import ReadingProgress from '@/components/ReadingProgress';

export const revalidate = 60;

interface ChapterPageProps {
  params: { id: string; num: string };
  searchParams: { unlocked?: string; subscribed?: string };
}

export async function generateMetadata({ params }: ChapterPageProps) {
  const book = await getBook(params.id).catch(() => null);
  if (!book) return { title: 'Chapter not found' };
  return {
    title: `Chapter ${params.num} — ${book.title} | NovelFactory`,
  };
}

export default async function ChapterPage({ params, searchParams }: ChapterPageProps) {
  const { id, num } = params;
  const chapterNum = parseInt(num, 10);

  if (isNaN(chapterNum)) notFound();

  const [book, chapter] = await Promise.all([
    getBook(id).catch(() => null),
    getChapterByNumber(id, chapterNum).catch(() => null),
  ]);

  if (!book || !chapter) notFound();

  const penName = typeof book.pen_name === 'object' ? book.pen_name : null;

  // Chapter is free if it's chapter 1 or explicitly marked free
  const isFree = chapter.is_free || chapterNum === 1;
  // Treat as unlocked if free, or if payment succeeded (query param)
  const isUnlocked = isFree || searchParams.unlocked === '1' || searchParams.subscribed === '1';

  // Get adjacent chapters for navigation
  const adjacentData = await getChapters({ book: id, is_published: true }).catch(() => ({ results: [] }));
  const publishedChapters = adjacentData.results;
  const currentIdx = publishedChapters.findIndex((c) => c.chapter_number === chapterNum);
  const prevChapter = currentIdx > 0 ? publishedChapters[currentIdx - 1] : null;
  const nextChapter = currentIdx < publishedChapters.length - 1 ? publishedChapters[currentIdx + 1] : null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <ReadingProgress />
      {/* Breadcrumb */}
      <nav className="text-sm text-slate-500 mb-8 flex items-center gap-2 flex-wrap">
        <Link href="/" className="hover:text-slate-300">Home</Link>
        <ChevronRight size={14} />
        <Link href="/books" className="hover:text-slate-300">Books</Link>
        <ChevronRight size={14} />
        <Link href={`/books/${id}`} className="hover:text-slate-300 truncate max-w-xs">{book.title}</Link>
        <ChevronRight size={14} />
        <span className="text-slate-300">Chapter {chapterNum}</span>
      </nav>

      {/* Chapter header */}
      <header className="mb-8">
        <p className="text-amber-400 text-sm font-medium mb-2">
          {penName?.name} · {book.title}
        </p>
        <h1 className="text-4xl font-extrabold text-white">
          {chapter.title || `Chapter ${chapterNum}`}
        </h1>
        {chapter.word_count && (
          <p className="text-slate-500 text-sm mt-2">{chapter.word_count.toLocaleString()} words</p>
        )}
      </header>

      {/* Chapter content */}
      {isUnlocked && chapter.content ? (
        <article id="chapter-content" className="prose prose-invert prose-slate max-w-none prose-lg text-slate-200 leading-relaxed prose-p:mb-5 prose-headings:text-white">
          {chapter.content.split('\n\n').map((para, i) => (
            <p key={i}>{para}</p>
          ))}
        </article>
      ) : isUnlocked && !chapter.content ? (
        <div className="text-center py-16 text-slate-500 bg-slate-800 rounded-2xl border border-slate-700">
          <BookOpen size={40} className="mx-auto mb-3 opacity-40" />
          <p>Chapter content is not available yet.</p>
        </div>
      ) : null}

      {/* Free preview — show part of chapter 1 or first paragraph as teaser */}
      {!isUnlocked && chapter.content && (
        <div className="relative overflow-hidden">
          <article className="prose prose-invert prose-slate max-w-none prose-lg text-slate-200 leading-relaxed prose-p:mb-5">
            {chapter.content
              .split('\n\n')
              .slice(0, 3)
              .map((para, i) => (
                <p key={i}>{para}</p>
              ))}
          </article>
          {/* Fade gradient */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none" />
        </div>
      )}

      {/* Paywall gate */}
      {!isUnlocked && (
        <ChapterGate
          chapterId={chapter.id}
          chapterNum={chapterNum}
          bookTitle={book.title}
        />
      )}

      {/* Upsell banner (shown after content or midway) */}
      {isUnlocked && (
        <>
          <UpsellBanner
            bookTitle={book.title}
            amazonUrl={book.amazon_url}
            price={book.current_price_usd || 3.99}
          />

          {/* Chapter navigation */}
          <nav className="flex justify-between items-center mt-8 pt-6 border-t border-slate-700">
            {prevChapter ? (
              <Link
                href={`/books/${id}/chapters/${prevChapter.chapter_number}`}
                className="flex items-center gap-2 text-slate-400 hover:text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <ChevronLeft size={18} />
                <span className="text-sm">
                  Chapter {prevChapter.chapter_number}
                  {prevChapter.title && <span className="hidden sm:inline"> · {prevChapter.title}</span>}
                </span>
              </Link>
            ) : (
              <div />
            )}

            <Link
              href={`/books/${id}`}
              className="text-slate-500 hover:text-slate-300 text-xs px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            >
              Table of Contents
            </Link>

            {nextChapter ? (
              <Link
                href={`/books/${id}/chapters/${nextChapter.chapter_number}`}
                className="flex items-center gap-2 text-amber-400 hover:text-amber-300 px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <span className="text-sm">
                  Chapter {nextChapter.chapter_number}
                  {nextChapter.title && <span className="hidden sm:inline"> · {nextChapter.title}</span>}
                </span>
                <ChevronRight size={18} />
              </Link>
            ) : (
              <div className="text-slate-500 text-sm text-right">
                <p>That&apos;s the latest chapter!</p>
                <p className="text-xs mt-0.5">Next chapter drops in 3 days 🔔</p>
              </div>
            )}
          </nav>
        </>
      )}
    </div>
  );
}
