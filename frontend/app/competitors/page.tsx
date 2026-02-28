'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  TrendingUp, ArrowLeft, RefreshCw, Loader2, Plus, Pencil,
  Trash2, X, Save, CheckCircle, AlertCircle, ExternalLink,
  BarChart2, Star, DollarSign, BookOpen,
} from 'lucide-react';
import {
  getCompetitorBooks,
  createCompetitorBook,
  updateCompetitorBook,
  deleteCompetitorBook,
  estimateCompetitorRevenue,
  getCompetitorGenres,
} from '@/lib/api';
import type { CompetitorBook } from '@/types';

// ── BSR Color ─────────────────────────────────────────────────
function bsrColor(bsr: number | null) {
  if (!bsr) return 'text-slate-500';
  if (bsr <= 1_000)  return 'text-emerald-400';
  if (bsr <= 10_000) return 'text-amber-400';
  if (bsr <= 50_000) return 'text-orange-400';
  return 'text-red-400';
}

function bsrLabel(bsr: number | null) {
  if (!bsr) return '—';
  if (bsr <= 1_000)  return 'Hot';
  if (bsr <= 10_000) return 'Good';
  if (bsr <= 50_000) return 'OK';
  return 'Low';
}

// ── Stars ─────────────────────────────────────────────────────
function StarRow({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map(s => (
        <Star
          key={s}
          size={11}
          className={s <= Math.round(rating) ? 'text-amber-400 fill-amber-400' : 'text-slate-700'}
        />
      ))}
      <span className="text-xs text-slate-400 ml-1">{rating.toFixed(1)}</span>
    </div>
  );
}

// ── BSR Mini Chart ────────────────────────────────────────────
function BsrChart({ history }: { history: { date: string; bsr: number }[] }) {
  if (!history.length) return <p className="text-xs text-slate-600">No history</p>;
  const last12 = history.slice(-12);
  const max = Math.max(...last12.map(h => h.bsr));
  const min = Math.min(...last12.map(h => h.bsr));
  const range = max - min || 1;

  return (
    <div className="flex items-end gap-0.5 h-8">
      {last12.map((h, i) => {
        const pct = ((max - h.bsr) / range) * 100;
        return (
          <div
            key={i}
            title={`${new Date(h.date).toLocaleDateString()}: BSR ${h.bsr.toLocaleString()}`}
            className="flex-1 bg-amber-500/60 rounded-sm min-w-[3px] transition-all"
            style={{ height: `${Math.max(pct, 8)}%` }}
          />
        );
      })}
    </div>
  );
}

// ── Add/Edit Modal ────────────────────────────────────────────
interface CompForm {
  asin: string; title: string; author: string;
  genre: string; subgenre: string;
  bsr: string; review_count: string; avg_rating: string; price_usd: string;
  cover_style: string; description_hooks: string; themes: string;
  tracking_start_date: string;
}

const EMPTY_FORM: CompForm = {
  asin: '', title: '', author: '',
  genre: '', subgenre: '',
  bsr: '', review_count: '0', avg_rating: '0', price_usd: '',
  cover_style: '', description_hooks: '', themes: '',
  tracking_start_date: '',
};

function CompModal({
  initial, onClose, onSaved,
}: {
  initial: CompetitorBook | null;
  onClose: () => void;
  onSaved: (c: CompetitorBook) => void;
}) {
  const isEdit = !!initial;
  const [form, setForm] = useState<CompForm>(
    initial ? {
      asin: initial.asin,
      title: initial.title,
      author: initial.author,
      genre: initial.genre,
      subgenre: initial.subgenre,
      bsr: initial.bsr != null ? String(initial.bsr) : '',
      review_count: String(initial.review_count),
      avg_rating: String(initial.avg_rating),
      price_usd: initial.price_usd != null ? String(initial.price_usd) : '',
      cover_style: initial.cover_style,
      description_hooks: initial.description_hooks.join(', '),
      themes: initial.themes.join(', '),
      tracking_start_date: initial.tracking_start_date ?? '',
    } : { ...EMPTY_FORM }
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  function f(key: keyof CompForm) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value }));
  }

  async function submit() {
    if (!form.asin.trim() || !form.title.trim()) {
      setErr('ASIN and Title are required');
      return;
    }
    setBusy(true);
    try {
      const payload: Partial<CompetitorBook> = {
        asin: form.asin.trim(),
        title: form.title.trim(),
        author: form.author.trim(),
        genre: form.genre.trim(),
        subgenre: form.subgenre.trim(),
        bsr: form.bsr ? parseInt(form.bsr) : null,
        review_count: parseInt(form.review_count) || 0,
        avg_rating: parseFloat(form.avg_rating) || 0,
        price_usd: form.price_usd ? form.price_usd : null,
        cover_style: form.cover_style.trim(),
        description_hooks: form.description_hooks.split(',').map(s => s.trim()).filter(Boolean),
        themes: form.themes.split(',').map(s => s.trim()).filter(Boolean),
        tracking_start_date: form.tracking_start_date || null,
      };
      const saved = isEdit
        ? await updateCompetitorBook(initial!.id, payload)
        : await createCompetitorBook(payload);
      onSaved(saved);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 overflow-y-auto">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-xl p-6 shadow-2xl my-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <TrendingUp size={18} className="text-amber-400" />
            {isEdit ? 'Edit Competitor' : 'Track New Competitor'}
          </h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">ASIN *</label>
              <input type="text" value={form.asin} onChange={f('asin')} placeholder="B0XXXXXXXXX"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Price (USD)</label>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm">$</span>
                <input type="number" min="0" step="0.01" value={form.price_usd} onChange={f('price_usd')}
                  className="w-full pl-6 pr-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono" />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Title *</label>
            <input type="text" value={form.title} onChange={f('title')} placeholder="Book title"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Author</label>
              <input type="text" value={form.author} onChange={f('author')}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">BSR</label>
              <input type="number" min="1" value={form.bsr} onChange={f('bsr')} placeholder="e.g. 5000"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Genre</label>
              <input type="text" value={form.genre} onChange={f('genre')} placeholder="e.g. Thriller"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Subgenre</label>
              <input type="text" value={form.subgenre} onChange={f('subgenre')} placeholder="e.g. Psychological"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Reviews</label>
              <input type="number" min="0" value={form.review_count} onChange={f('review_count')}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Avg Rating</label>
              <input type="number" min="0" max="5" step="0.1" value={form.avg_rating} onChange={f('avg_rating')}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono" />
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Cover Style</label>
            <input type="text" value={form.cover_style} onChange={f('cover_style')} placeholder="e.g. Dark silhouette, moody lighting"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Themes (comma-separated)</label>
            <input type="text" value={form.themes} onChange={f('themes')} placeholder="betrayal, redemption, survival"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Description Hooks (comma-separated)</label>
            <input type="text" value={form.description_hooks} onChange={f('description_hooks')} placeholder="What if...?, Secret she can't escape..."
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
          </div>

          {err && <p className="text-red-400 text-xs">{err}</p>}
          <div className="flex gap-3 pt-1">
            <button onClick={submit} disabled={busy}
              className="flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold py-2.5 rounded-xl transition-colors disabled:opacity-50">
              {busy ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              {busy ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Competitor'}
            </button>
            <button onClick={onClose} className="px-5 py-2.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function CompetitorsPage() {
  const [books,   setBooks]   = useState<CompetitorBook[]>([]);
  const [genres,  setGenres]  = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [genre,   setGenre]   = useState('');
  const [search,  setSearch]  = useState('');
  const [modal,   setModal]   = useState<{ open: boolean; editing: CompetitorBook | null }>({ open: false, editing: null });
  const [del,     setDel]     = useState<number | null>(null);
  const [toast,   setToast]   = useState<{ msg: string; ok: boolean } | null>(null);
  const [sort,    setSort]    = useState<string>('bsr');

  function showToast(msg: string, ok = true) {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, g] = await Promise.all([
        getCompetitorBooks({ genre: genre || undefined, search: search || undefined, ordering: sort }),
        getCompetitorGenres(),
      ]);
      setBooks(b);
      setGenres(g);
    } finally {
      setLoading(false);
    }
  }, [genre, search, sort]);

  useEffect(() => { load(); }, [load]);

  async function handleDelete(b: CompetitorBook) {
    if (!confirm(`Remove "${b.title}" from tracking?`)) return;
    setDel(b.id);
    try {
      await deleteCompetitorBook(b.id);
      setBooks(p => p.filter(c => c.id !== b.id));
      showToast('Removed from tracking');
    } catch { showToast('Failed to remove', false); }
    finally { setDel(null); }
  }

  async function handleEstimate(b: CompetitorBook) {
    try {
      const updated = await estimateCompetitorRevenue(b.id);
      setBooks(p => p.map(c => c.id === updated.id ? updated : c));
      showToast('Revenue estimate updated');
    } catch { showToast('Failed to estimate', false); }
  }

  function handleSaved(saved: CompetitorBook) {
    setBooks(p => {
      const idx = p.findIndex(c => c.id === saved.id);
      if (idx >= 0) { const n = [...p]; n[idx] = saved; return n; }
      return [...p, saved];
    });
    setModal({ open: false, editing: null });
    showToast(modal.editing ? 'Updated' : 'Competitor added');
  }

  // Aggregates
  const avgBsr = books.filter(b => b.bsr).reduce((s, b, _i, a) => s + (b.bsr! / a.filter(x => x.bsr).length), 0);
  const avgRevenue = books.reduce((s, b) => s + parseFloat(String(b.estimated_monthly_revenue)), 0) / (books.length || 1);
  const avgRating  = books.reduce((s, b) => s + b.avg_rating, 0) / (books.length || 1);

  const SORT_OPTIONS = [
    { label: 'BSR (best)', value: 'bsr' },
    { label: 'BSR (worst)', value: '-bsr' },
    { label: 'Rating', value: '-avg_rating' },
    { label: 'Reviews', value: '-review_count' },
    { label: 'Revenue', value: '-estimated_monthly_revenue' },
    { label: 'Price', value: 'price_usd' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl text-sm font-medium ${toast.ok ? 'bg-emerald-600' : 'bg-red-600'}`}>
          {toast.ok ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {toast.msg}
        </div>
      )}

      {modal.open && (
        <CompModal
          initial={modal.editing}
          onClose={() => setModal({ open: false, editing: null })}
          onSaved={handleSaved}
        />
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </Link>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Market Intelligence</p>
              <h1 className="text-xl font-bold">Competitor Books</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setModal({ open: true, editing: null })}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold text-sm px-4 py-2 rounded-xl transition-colors">
              <Plus size={14} /> Track Competitor
            </button>
            <button onClick={load} disabled={loading}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-2 rounded-lg transition-colors disabled:opacity-40">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* KPI Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-amber-400"><TrendingUp size={20} /></div>
            <p className="text-2xl font-bold">{books.length}</p>
            <p className="text-sm text-slate-400 mt-0.5">Tracked Competitors</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-blue-400"><BarChart2 size={20} /></div>
            <p className={`text-2xl font-bold ${bsrColor(Math.round(avgBsr))}`}>{Math.round(avgBsr).toLocaleString()}</p>
            <p className="text-sm text-slate-400 mt-0.5">Avg BSR</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-emerald-400"><DollarSign size={20} /></div>
            <p className="text-2xl font-bold text-emerald-400">${Math.round(avgRevenue).toLocaleString()}</p>
            <p className="text-sm text-slate-400 mt-0.5">Avg Monthly Revenue</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-amber-400"><Star size={20} /></div>
            <p className="text-2xl font-bold text-amber-400">{avgRating.toFixed(2)}★</p>
            <p className="text-sm text-slate-400 mt-0.5">Avg Rating</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <input
            type="text"
            placeholder="Search title, author, ASIN…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 min-w-[200px] max-w-sm px-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500"
          />
          <select value={genre} onChange={e => setGenre(e.target.value)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500">
            <option value="">All Genres</option>
            {genres.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
          <select value={sort} onChange={e => setSort(e.target.value)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500">
            {SORT_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-500">
            <Loader2 size={36} className="animate-spin" />
          </div>
        ) : books.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <TrendingUp size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400">No competitors tracked yet.</p>
            <button onClick={() => setModal({ open: true, editing: null })}
              className="mt-4 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-6 py-3 rounded-xl transition-colors mx-auto">
              <Plus size={16} /> Track First Competitor
            </button>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
                    <th className="text-left px-5 py-3">Title / Author</th>
                    <th className="text-center px-4 py-3">BSR</th>
                    <th className="text-center px-4 py-3">Price</th>
                    <th className="text-center px-4 py-3">Rating</th>
                    <th className="text-center px-4 py-3">Reviews</th>
                    <th className="text-right px-4 py-3">Est. Revenue/mo</th>
                    <th className="text-left px-4 py-3">BSR Trend</th>
                    <th className="text-center px-4 py-3">Genre</th>
                    <th className="py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {books.map((b, i) => (
                    <tr key={b.id} className={`border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${i % 2 === 0 ? '' : 'bg-slate-900/50'}`}>
                      <td className="px-5 py-4">
                        <p className="font-medium text-white truncate max-w-[200px]">{b.title}</p>
                        <p className="text-slate-500 text-xs mt-0.5">{b.author}</p>
                        <p className="text-slate-600 text-xs font-mono">{b.asin}</p>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <p className={`font-mono font-bold text-sm ${bsrColor(b.bsr)}`}>
                          {b.bsr ? `#${b.bsr.toLocaleString()}` : '—'}
                        </p>
                        <span className={`text-xs ${bsrColor(b.bsr)}`}>{bsrLabel(b.bsr)}</span>
                      </td>
                      <td className="px-4 py-4 text-center text-white font-mono">
                        {b.price_usd ? `$${parseFloat(String(b.price_usd)).toFixed(2)}` : '—'}
                      </td>
                      <td className="px-4 py-4">
                        <StarRow rating={b.avg_rating} />
                      </td>
                      <td className="px-4 py-4 text-center text-slate-300 font-mono">
                        {b.review_count.toLocaleString()}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <p className="text-emerald-400 font-mono font-semibold">
                          ${Math.round(parseFloat(String(b.estimated_monthly_revenue))).toLocaleString()}
                        </p>
                        <p className="text-slate-600 text-xs">{b.estimated_monthly_units} units</p>
                      </td>
                      <td className="px-4 py-4 w-24">
                        <BsrChart history={b.bsr_history} />
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded-full">
                          {b.genre || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-1">
                          <a
                            href={`https://amazon.com/dp/${b.asin}`}
                            target="_blank" rel="noopener noreferrer"
                            className="text-slate-500 hover:text-amber-400 transition-colors p-1"
                            title="View on Amazon"
                          >
                            <ExternalLink size={13} />
                          </a>
                          <button onClick={() => handleEstimate(b)}
                            className="text-slate-500 hover:text-emerald-400 transition-colors p-1" title="Recalculate revenue">
                            <TrendingUp size={13} />
                          </button>
                          <button onClick={() => setModal({ open: true, editing: b })}
                            className="text-slate-500 hover:text-amber-400 transition-colors p-1" title="Edit">
                            <Pencil size={13} />
                          </button>
                          <button onClick={() => handleDelete(b)} disabled={del === b.id}
                            className="text-slate-500 hover:text-red-400 transition-colors p-1 disabled:opacity-40" title="Remove">
                            {del === b.id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Themes Cloud */}
        {books.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BookOpen size={14} className="text-amber-400" />
              Trending Themes Across Competitors
            </h2>
            <div className="flex flex-wrap gap-2">
              {Array.from(
                books.flatMap(b => b.themes)
                  .reduce((acc, t) => { acc.set(t, (acc.get(t) ?? 0) + 1); return acc; }, new Map<string, number>())
              )
                .sort((a, b) => b[1] - a[1])
                .map(([theme, count]) => (
                  <span key={theme} className="text-xs px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    {theme} <span className="opacity-60">×{count}</span>
                  </span>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
