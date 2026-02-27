'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Plus, BookOpen, ArrowLeft, RefreshCw } from 'lucide-react';
import { getBook, getCovers } from '@/lib/api';
import type { Book, BookCover } from '@/types';
import CoverCard from '@/components/CoverCard';
import KDPCalculator from '@/components/KDPCalculator';
import CoverUploadModal from '@/components/CoverUploadModal';

export default function CoversPage() {
  const { id } = useParams<{ id: string }>();
  const bookId = Number(id);

  const [book, setBook] = useState<Book | null>(null);
  const [covers, setCovers] = useState<BookCover[]>([]);
  const [filter, setFilter] = useState<'all' | 'ebook' | 'paperback'>('all');
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [bookData, coversData] = await Promise.all([
        getBook(bookId),
        getCovers({ book: bookId }),
      ]);
      setBook(bookData);
      setCovers(coversData.results);
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => { load(); }, [load]);

  function handleActivate(updated: BookCover) {
    setCovers((prev) =>
      prev.map((c) =>
        c.cover_type === updated.cover_type
          ? { ...c, is_active: c.id === updated.id }
          : c
      )
    );
  }

  function handleDelete(deletedId: number) {
    setCovers((prev) => prev.filter((c) => c.id !== deletedId));
  }

  function handleCreated(cover: BookCover) {
    setCovers((prev) => [cover, ...prev]);
  }

  const filtered = filter === 'all' ? covers : covers.filter((c) => c.cover_type === filter);
  const ebookActive = covers.find((c) => c.cover_type === 'ebook' && c.is_active);
  const paperbackActive = covers.find((c) => c.cover_type === 'paperback' && c.is_active);

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm">
          <Link href="/books" className="text-slate-400 hover:text-white transition-colors flex items-center gap-1">
            <BookOpen size={14} /> Books
          </Link>
          <span className="text-slate-600">/</span>
          {book && (
            <>
              <Link href={`/books/${bookId}`} className="text-slate-400 hover:text-white transition-colors line-clamp-1 max-w-xs">
                {book.title}
              </Link>
              <span className="text-slate-600">/</span>
            </>
          )}
          <span className="text-white">Covers</span>
        </div>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <Link
              href={`/books/${bookId}`}
              className="text-slate-400 hover:text-white text-sm flex items-center gap-1 mb-2 transition-colors"
            >
              <ArrowLeft size={14} /> Back to book
            </Link>
            <h1 className="text-2xl font-bold text-white">KDP Cover Manager</h1>
            {book && <p className="text-slate-400 mt-1 line-clamp-1">{book.title}</p>}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={load}
              disabled={loading}
              className="p-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              <Plus size={16} /> Add Cover
            </button>
          </div>
        </div>

        {/* Active cover summary */}
        {(ebookActive || paperbackActive) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {ebookActive && (
              <ActiveBadge label="eBook" version={ebookActive.version_number} />
            )}
            {paperbackActive && (
              <ActiveBadge label="Paperback" version={paperbackActive.version_number} />
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: cover grid */}
          <div className="lg:col-span-2 space-y-4">
            {/* Filter tabs */}
            <div className="flex gap-2">
              {(['all', 'ebook', 'paperback'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium capitalize transition-colors ${
                    filter === f
                      ? 'bg-amber-500 text-slate-900'
                      : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'
                  }`}
                >
                  {f === 'all' ? `All (${covers.length})` : `${f} (${covers.filter((c) => c.cover_type === f).length})`}
                </button>
              ))}
            </div>

            {/* Cover grid */}
            {loading ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-slate-800 rounded-2xl animate-pulse" style={{ aspectRatio: '3/5' }} />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-20 space-y-3">
                <BookOpen size={40} className="mx-auto text-slate-700" />
                <p className="text-slate-500">No cover versions yet.</p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="text-amber-400 hover:text-amber-300 text-sm underline"
                >
                  Upload the first cover
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {filtered.map((cover) => (
                  <CoverCard
                    key={cover.id}
                    cover={cover}
                    onActivate={handleActivate}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Right: KDP Calculator */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <KDPCalculator />

              {/* Quick links */}
              <div className="mt-4 bg-slate-800 border border-slate-700 rounded-2xl p-4 space-y-2">
                <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">KDP Resources</p>
                <a
                  href="https://kdp.amazon.com/en_US/cover-calculator"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm text-amber-400 hover:text-amber-300 transition-colors"
                >
                  ↗ KDP Cover Calculator (official)
                </a>
                <a
                  href="https://kdp.amazon.com/en_US/help/topic/G200645690"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm text-amber-400 hover:text-amber-300 transition-colors"
                >
                  ↗ Cover Submission Guidelines
                </a>
                <a
                  href="https://kdp.amazon.com/en_US/help/topic/G201834500"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm text-amber-400 hover:text-amber-300 transition-colors"
                >
                  ↗ eBook Cover Requirements
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showUpload && (
        <CoverUploadModal
          bookId={bookId}
          onCreated={handleCreated}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  );
}

function ActiveBadge({ label, version }: { label: string; version: number }) {
  return (
    <div className="flex items-center gap-3 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3">
      <div className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
      <div>
        <p className="text-xs text-slate-400">{label} — Active Cover</p>
        <p className="text-white text-sm font-semibold">Version {version}</p>
      </div>
    </div>
  );
}
