'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, BookPlus, Loader2, BookOpen, Users } from 'lucide-react';
import { createBook, getPenNames } from '@/lib/api';
import type { BookCreatePayload } from '@/lib/api';
import type { PenName } from '@/types';

const GENRE_OPTIONS = [
  'Thriller', 'Mystery', 'Suspense', 'Horror', 'Crime', 'Psychological Thriller',
  'Legal Thriller', 'Medical Thriller', 'Action & Adventure', 'Spy Thriller',
  'Fantasy', 'Science Fiction', 'Romance', 'Historical Fiction', 'Literary Fiction', 'Other',
];

export default function NewBookPage() {
  const router = useRouter();

  const [penNames, setPenNames]   = useState<PenName[]>([]);
  const [loadingPN, setLoadingPN] = useState(true);

  const [form, setForm] = useState<{
    title: string;
    subtitle: string;
    synopsis: string;
    pen_name: string;
    genre: string;
    target_chapter_count: string;
    target_word_count: string;
  }>({
    title: '',
    subtitle: '',
    synopsis: '',
    pen_name: '',
    genre: '',
    target_chapter_count: '40',
    target_word_count: '80000',
  });

  const [errors, setErrors]   = useState<Partial<typeof form>>({});
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError]     = useState('');

  useEffect(() => {
    getPenNames({ page: 1 })
      .then(res => {
        setPenNames(res.results);
        if (res.results.length > 0 && !form.pen_name) {
          setForm(f => ({ ...f, pen_name: String(res.results[0].id) }));
        }
      })
      .catch(() => {})
      .finally(() => setLoadingPN(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function validate() {
    const errs: Partial<typeof form> = {};
    if (!form.title.trim()) errs.title = 'Title is required';
    if (!form.pen_name)     errs.pen_name = 'Select a pen name';
    const chapters = Number(form.target_chapter_count);
    const words    = Number(form.target_word_count);
    if (isNaN(chapters) || chapters < 1 || chapters > 500) errs.target_chapter_count = '1–500';
    if (isNaN(words)    || words    < 1000)                 errs.target_word_count    = 'Min 1,000';
    return errs;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setSubmitting(true);
    setApiError('');
    try {
      const payload: BookCreatePayload = {
        title:                form.title.trim(),
        subtitle:             form.subtitle.trim() || undefined,
        synopsis:             form.synopsis.trim() || undefined,
        pen_name:             Number(form.pen_name),
        genre:                form.genre || undefined,
        target_chapter_count: Number(form.target_chapter_count),
        target_word_count:    Number(form.target_word_count),
      };
      const book = await createBook(payload);
      router.push(`/books/${book.id}/workflow`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: Record<string, string[]> }; message?: string };
      if (e.response?.data) {
        const msgs = Object.entries(e.response.data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
          .join('; ');
        setApiError(msgs);
      } else {
        setApiError(e.message ?? 'Something went wrong');
      }
    } finally {
      setSubmitting(false);
    }
  }

  function field(key: keyof typeof form, value: string) {
    setForm(f => ({ ...f, [key]: value }));
    setErrors(e => ({ ...e, [key]: undefined }));
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center gap-4">
          <Link href="/dashboard" className="text-slate-400 hover:text-white transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider">Books</p>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <BookPlus size={20} className="text-amber-400" />
              Create New Book
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Info banner */}
        <div className="flex items-start gap-3 bg-blue-900/20 border border-blue-700/40 rounded-xl p-4 mb-8 text-sm text-blue-300">
          <BookOpen size={16} className="shrink-0 mt-0.5 text-blue-400" />
          <p>
            After creating the book it will start in <strong>draft</strong> status. Use the{' '}
            <strong>Workflow</strong> panel to kick off keyword research and writing.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Pen Name */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              <Users size={14} className="inline mr-1.5 text-amber-400" />
              Pen Name <span className="text-red-400">*</span>
            </label>
            {loadingPN ? (
              <div className="flex items-center gap-2 text-slate-500 text-sm py-2">
                <Loader2 size={14} className="animate-spin" /> Loading pen names…
              </div>
            ) : penNames.length === 0 ? (
              <div className="text-sm text-red-400 flex items-center gap-2 py-2">
                No pen names found.{' '}
                <Link href="/pen-names" className="underline hover:text-red-300">Create one first</Link>
              </div>
            ) : (
              <select
                value={form.pen_name}
                onChange={e => field('pen_name', e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none"
              >
                <option value="">— Select pen name —</option>
                {penNames.map(pn => (
                  <option key={pn.id} value={String(pn.id)}>
                    {pn.name}{pn.niche_genre ? ` · ${pn.niche_genre}` : ''}
                  </option>
                ))}
              </select>
            )}
            {errors.pen_name && <p className="text-red-400 text-xs mt-1">{errors.pen_name}</p>}
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={form.title}
              onChange={e => field('title', e.target.value)}
              placeholder="The Missing Hour"
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm placeholder-slate-600 focus:outline-none"
            />
            {errors.title && <p className="text-red-400 text-xs mt-1">{errors.title}</p>}
          </div>

          {/* Subtitle */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Subtitle <span className="text-slate-500">(optional)</span>
            </label>
            <input
              type="text"
              value={form.subtitle}
              onChange={e => field('subtitle', e.target.value)}
              placeholder="A Detective Morgan Thriller"
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm placeholder-slate-600 focus:outline-none"
            />
          </div>

          {/* Genre */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Genre <span className="text-slate-500">(optional)</span>
            </label>
            <select
              value={form.genre}
              onChange={e => field('genre', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none"
            >
              <option value="">— Select genre —</option>
              {GENRE_OPTIONS.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          {/* Synopsis */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Synopsis <span className="text-slate-500">(optional — AI will generate if blank)</span>
            </label>
            <textarea
              rows={5}
              value={form.synopsis}
              onChange={e => field('synopsis', e.target.value)}
              placeholder="A high-stakes thriller set in a city where every minute counts…"
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm placeholder-slate-600 resize-none focus:outline-none"
            />
          </div>

          {/* Target Chapter Count & Word Count */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Target Chapters
              </label>
              <input
                type="number"
                min={1}
                max={500}
                value={form.target_chapter_count}
                onChange={e => field('target_chapter_count', e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none"
              />
              {errors.target_chapter_count && (
                <p className="text-red-400 text-xs mt-1">{errors.target_chapter_count}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Target Words
              </label>
              <input
                type="number"
                min={1000}
                step={1000}
                value={form.target_word_count}
                onChange={e => field('target_word_count', e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none"
              />
              {errors.target_word_count && (
                <p className="text-red-400 text-xs mt-1">{errors.target_word_count}</p>
              )}
            </div>
          </div>

          {/* API error */}
          {apiError && (
            <div className="bg-red-900/30 border border-red-700/50 rounded-lg px-4 py-3 text-red-300 text-sm">
              {apiError}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-4 pt-2">
            <button
              type="submit"
              disabled={submitting || penNames.length === 0}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed text-slate-900 font-bold px-8 py-3 rounded-xl transition-colors shadow-lg shadow-amber-500/20"
            >
              {submitting ? <Loader2 size={16} className="animate-spin" /> : <BookPlus size={16} />}
              Create Book
            </button>
            <Link href="/dashboard" className="text-slate-400 hover:text-white text-sm transition-colors">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
