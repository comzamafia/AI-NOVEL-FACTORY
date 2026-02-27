'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  BarChart3, DollarSign, TrendingUp, TrendingDown,
  Star, Megaphone, RefreshCw, BookOpen, Loader2,
  ArrowUpRight, Target,
} from 'lucide-react';
import { getAnalyticsSummary } from '@/lib/api';
import type { AnalyticsSummary, AnalyticsBook } from '@/types';
import LifecycleBadge from '@/components/LifecycleBadge';

// ── KPI Card ─────────────────────────────────────────────────────
function KpiCard({
  label, value, sub, icon, color = 'text-amber-400',
}: {
  label: string; value: string; sub?: string; icon: React.ReactNode; color?: string;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <div className={`mb-3 ${color}`}>{icon}</div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-slate-400 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
    </div>
  );
}

// ── Revenue Bar ───────────────────────────────────────────────────
function RevenueBar({ book, max }: { book: AnalyticsBook; max: number }) {
  const pct = max > 0 ? (book.total_revenue_usd / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3 py-1">
      <Link href={`/books/${book.id}`} className="text-sm text-slate-300 hover:text-amber-400 transition-colors truncate w-40 shrink-0">
        {book.title}
      </Link>
      <div className="flex-1 bg-slate-800 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-mono text-emerald-400 w-20 text-right shrink-0">
        ${book.total_revenue_usd.toFixed(2)}
      </span>
    </div>
  );
}

// ── ACOS badge ────────────────────────────────────────────────────
function AcosBadge({ acos }: { acos: number | null }) {
  if (acos === null) return <span className="text-slate-600">—</span>;
  const color = acos < 25 ? 'text-emerald-400' : acos < 50 ? 'text-yellow-400' : 'text-red-400';
  return <span className={`font-mono ${color}`}>{acos.toFixed(1)}%</span>;
}

// ── Star Rating ───────────────────────────────────────────────────
function Stars({ rating }: { rating: number }) {
  if (!rating) return <span className="text-slate-600">—</span>;
  return (
    <span className="text-amber-400 font-mono">
      {rating.toFixed(1)}★
    </span>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function AnalyticsPage() {
  const [data, setData]       = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab]         = useState<'all' | 'published'>('all');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const summary = await getAnalyticsSummary();
      setData(summary);
    } catch {
      // silently fail — show empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const books: AnalyticsBook[] = data?.books || [];
  const filtered = tab === 'published'
    ? books.filter(b => b.lifecycle_status === 'published_kdp' || b.lifecycle_status === 'published_all')
    : books;

  const maxRevenue = Math.max(...filtered.map(b => b.total_revenue_usd), 1);

  const totals = data?.totals;

  // Aggregate review stats
  const totalReviews  = filtered.reduce((s, b) => s + (b.reviews.total_reviews || 0), 0);
  const avgRating     = filtered.length
    ? filtered.reduce((s, b) => s + (b.reviews.avg_rating || 0), 0) / filtered.filter(b => b.reviews.avg_rating > 0).length || 0
    : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider">Admin</p>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <BarChart3 size={20} className="text-amber-400" />
              Analytics
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-2 rounded-lg transition-colors">
              ← Dashboard
            </Link>
            <button
              onClick={load}
              disabled={loading}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-2 rounded-lg transition-colors disabled:opacity-40"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-500">
            <Loader2 size={40} className="animate-spin" />
          </div>
        ) : (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <KpiCard
                label="Total Revenue"
                value={`$${(totals?.revenue_usd || 0).toFixed(2)}`}
                icon={<DollarSign size={20} />}
                color="text-emerald-400"
              />
              <KpiCard
                label="Total Books"
                value={String(totals?.total_books || 0)}
                icon={<BookOpen size={20} />}
                color="text-blue-400"
              />
              <KpiCard
                label="Ads Spend (30d)"
                value={`$${(totals?.ads_spend_30d || 0).toFixed(2)}`}
                icon={<Megaphone size={20} />}
                color="text-orange-400"
              />
              <KpiCard
                label="Ads Sales (30d)"
                value={`$${(totals?.ads_sales_30d || 0).toFixed(2)}`}
                icon={<TrendingUp size={20} />}
                color="text-amber-400"
              />
              <KpiCard
                label="Overall ACOS"
                value={totals?.overall_acos != null ? `${totals.overall_acos.toFixed(1)}%` : '—'}
                sub="< 25% = great"
                icon={<Target size={20} />}
                color={totals?.overall_acos != null && totals.overall_acos < 25 ? 'text-emerald-400' : 'text-red-400'}
              />
              <KpiCard
                label="Total Reviews"
                value={String(totalReviews)}
                sub={avgRating > 0 ? `avg ${avgRating.toFixed(1)}★` : undefined}
                icon={<Star size={20} />}
                color="text-yellow-400"
              />
            </div>

            {/* Filter tabs */}
            <div className="flex items-center gap-2">
              {(['all', 'published'] as const).map(t => (
                <button key={t} onClick={() => setTab(t)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    tab === t ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  {t === 'all' ? `All Books (${books.length})` : `Published (${books.filter(b => b.lifecycle_status === 'published_kdp' || b.lifecycle_status === 'published_all').length})`}
                </button>
              ))}
            </div>

            {filtered.length === 0 ? (
              <div className="text-center py-16 text-slate-600">
                <BarChart3 size={48} className="mx-auto mb-4 opacity-30" />
                <p>No books found for this filter.</p>
              </div>
            ) : (
              <>
                {/* Revenue bar chart */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5 flex items-center gap-2">
                    <DollarSign size={14} /> Revenue by Book
                  </h2>
                  <div className="space-y-2">
                    {filtered.slice(0, 15).map(b => (
                      <RevenueBar key={b.id} book={b} max={maxRevenue} />
                    ))}
                    {filtered.length > 15 && (
                      <p className="text-xs text-slate-600 text-center pt-2">+{filtered.length - 15} more books</p>
                    )}
                  </div>
                </div>

                {/* Per-book table */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-800">
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                      <BarChart3 size={14} /> Book Performance
                    </h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-slate-500 text-xs uppercase tracking-wider border-b border-slate-800">
                          <th className="text-left px-4 py-3">Book</th>
                          <th className="text-left px-4 py-3">Pen Name</th>
                          <th className="text-left px-4 py-3">Status</th>
                          <th className="text-right px-4 py-3">Revenue</th>
                          <th className="text-right px-4 py-3">Price</th>
                          <th className="text-right px-4 py-3">BSR</th>
                          <th className="text-right px-4 py-3">Reviews</th>
                          <th className="text-right px-4 py-3">Rating</th>
                          <th className="text-right px-4 py-3">Ads Spend</th>
                          <th className="text-right px-4 py-3">Ads Sales</th>
                          <th className="text-right px-4 py-3">ACOS</th>
                          <th className="text-right px-4 py-3">View</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {filtered.map(b => (
                          <tr key={b.id} className="hover:bg-slate-800/40 transition-colors">
                            <td className="px-4 py-3">
                              <Link href={`/books/${b.id}`} className="text-white hover:text-amber-400 font-medium transition-colors line-clamp-1 max-w-xs">
                                {b.title}
                              </Link>
                              {b.asin && <p className="text-xs text-slate-600 font-mono">{b.asin}</p>}
                            </td>
                            <td className="px-4 py-3 text-slate-400">{b.pen_name}</td>
                            <td className="px-4 py-3">
                              <LifecycleBadge status={b.lifecycle_status} />
                            </td>
                            <td className="px-4 py-3 text-right text-emerald-400 font-mono">
                              ${b.total_revenue_usd.toFixed(2)}
                            </td>
                            <td className="px-4 py-3 text-right text-slate-400 font-mono">
                              ${b.current_price_usd.toFixed(2)}
                            </td>
                            <td className="px-4 py-3 text-right text-slate-400 font-mono">
                              {b.bsr?.toLocaleString() ?? '—'}
                            </td>
                            <td className="px-4 py-3 text-right text-slate-300">
                              {b.reviews.total_reviews || '—'}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <Stars rating={b.reviews.avg_rating} />
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-orange-400">
                              ${b.ads_30d.spend.toFixed(2)}
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-blue-400">
                              ${b.ads_30d.sales.toFixed(2)}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <AcosBadge acos={b.ads_30d.acos} />
                            </td>
                            <td className="px-4 py-3 text-right">
                              <Link href={`/books/${b.id}`} className="text-slate-500 hover:text-amber-400 transition-colors">
                                <ArrowUpRight size={14} />
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* ACOS legend */}
                <div className="flex items-center gap-6 text-xs text-slate-600 justify-center pb-4">
                  <span className="flex items-center gap-1.5"><TrendingUp size={12} className="text-emerald-400" />ACOS &lt; 25% — Excellent</span>
                  <span className="flex items-center gap-1.5"><Target size={12} className="text-yellow-400" />25–50% — Acceptable</span>
                  <span className="flex items-center gap-1.5"><TrendingDown size={12} className="text-red-400" />&gt; 50% — Unprofitable</span>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
