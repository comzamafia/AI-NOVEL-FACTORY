'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Star, ArrowLeft, RefreshCw, Users, TrendingUp,
  MessageSquare, Loader2, ThumbsUp, ThumbsDown,
  Mail, CheckCircle, AlertTriangle, Clock,
} from 'lucide-react';
import { getBook, getReviewTracker } from '@/lib/api';
import type { Book, ReviewTracker } from '@/types';

// ── Rating distribution bar ───────────────────────────────────────
function RatingBar({ stars, count, total }: { stars: number; count: number; total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  const color =
    stars >= 4 ? 'bg-emerald-500' :
    stars === 3 ? 'bg-yellow-500' :
    'bg-red-500';
  return (
    <div className="flex items-center gap-3 py-1">
      <span className="text-sm text-slate-400 w-10 text-right shrink-0 font-mono">{stars}★</span>
      <div className="flex-1 bg-slate-800 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm text-slate-400 font-mono w-8 text-right shrink-0">{count}</span>
      <span className="text-xs text-slate-600 w-10 shrink-0">{pct.toFixed(0)}%</span>
    </div>
  );
}

// ── Velocity bar (weekly reviews) ─────────────────────────────────
function VelocityBar({ label, count, max }: { label: string; count: number; max: number }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-sm font-mono text-white">{count}</span>
      <div className="w-10 bg-slate-800 rounded-lg overflow-hidden" style={{ height: '80px' }}>
        <div
          className="w-full bg-gradient-to-t from-amber-600 to-amber-400 rounded-lg transition-all duration-700"
          style={{ height: `${pct}%`, marginTop: `${100 - pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-500">{label}</span>
    </div>
  );
}

// ── KPI Card ──────────────────────────────────────────────────────
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

// ── Theme chip ────────────────────────────────────────────────────
function ThemeChip({ label, positive }: { label: string; positive: boolean }) {
  return (
    <span className={`text-xs px-3 py-1.5 rounded-full font-medium border ${
      positive
        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
        : 'bg-red-500/10 text-red-400 border-red-500/30'
    }`}>
      {label}
    </span>
  );
}

// ── Star display ──────────────────────────────────────────────────
function StarDisplay({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map(n => (
        <Star
          key={n}
          size={20}
          className={n <= Math.round(rating) ? 'text-amber-400 fill-amber-400' : 'text-slate-700'}
        />
      ))}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function ReviewsPage() {
  const { id } = useParams<{ id: string }>();
  const bookId = id;

  const [book, setBook]     = useState<Book | null>(null);
  const [tracker, setTracker] = useState<ReviewTracker | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, t] = await Promise.all([
        getBook(bookId),
        getReviewTracker(bookId),
      ]);
      setBook(b);
      setTracker(t);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => { load(); }, [load]);

  // Derived values
  const dist = tracker?.rating_distribution ?? {};
  const totalFromDist = Object.values(dist).reduce((s: number, v) => s + (Number(v) || 0), 0);
  const totalReviews = tracker?.total_reviews ?? totalFromDist;

  const weeklyMax = Math.max(
    tracker?.reviews_week_1 ?? 0,
    tracker?.reviews_week_2 ?? 0,
    tracker?.reviews_week_3 ?? 0,
    tracker?.reviews_week_4 ?? 0,
    1,
  );

  const arcConvPct = tracker?.arc_conversion_rate != null
    ? `${(tracker.arc_conversion_rate * 100).toFixed(1)}%`
    : '—';

  const lowRating = tracker && tracker.avg_rating < 3.5;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link
              href={`/books/${bookId}`}
              className="text-slate-400 hover:text-white transition-colors shrink-0"
            >
              <ArrowLeft size={20} />
            </Link>
            <div className="min-w-0">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Reviews</p>
              <h1 className="text-lg font-bold text-white truncate">
                {book?.title ?? 'Loading…'}
              </h1>
            </div>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-2 rounded-lg transition-colors disabled:opacity-40 shrink-0"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-500">
            <Loader2 size={40} className="animate-spin" />
          </div>
        ) : !tracker ? (
          <div className="text-center py-24 text-slate-500">
            <MessageSquare size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400">No review data yet.</p>
            <p className="text-sm mt-2">Review data is synced daily from Amazon.</p>
          </div>
        ) : (
          <>
            {/* Low-rating alert */}
            {lowRating && (
              <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 rounded-2xl px-5 py-4">
                <AlertTriangle size={18} className="text-red-400 shrink-0" />
                <p className="text-sm text-red-300">
                  Average rating is <strong>{tracker.avg_rating.toFixed(1)}★</strong> — below the 3.5★
                  threshold. Review the AI sentiment report and consider publishing improvements.
                </p>
              </div>
            )}

            {/* KPI Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <KpiCard
                label="Total Reviews"
                value={String(totalReviews)}
                icon={<MessageSquare size={20} />}
                color="text-blue-400"
              />
              <KpiCard
                label="Avg Rating"
                value={tracker.avg_rating > 0 ? `${tracker.avg_rating.toFixed(2)}★` : '—'}
                sub={tracker.avg_rating >= 4 ? 'Excellent' : tracker.avg_rating >= 3.5 ? 'Good' : 'Needs attention'}
                icon={<Star size={20} />}
                color={tracker.avg_rating >= 4 ? 'text-emerald-400' : tracker.avg_rating >= 3.5 ? 'text-yellow-400' : 'text-red-400'}
              />
              <KpiCard
                label="ARC Sent"
                value={String(tracker.arc_emails_sent)}
                icon={<Mail size={20} />}
                color="text-purple-400"
              />
              <KpiCard
                label="ARC Conversion"
                value={arcConvPct}
                sub={`${tracker.arc_reviews_received} reviews received`}
                icon={<CheckCircle size={20} />}
                color={tracker.arc_conversion_rate >= 0.5 ? 'text-emerald-400' : 'text-amber-400'}
              />
            </div>

            {/* Two-column: rating dist + weekly velocity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Rating Distribution */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
                  <Star size={14} className="text-amber-400" />
                  Rating Distribution
                </h2>

                <div className="flex items-start gap-6 mb-6">
                  <div className="text-center">
                    <p className="text-5xl font-extrabold text-white">
                      {tracker.avg_rating > 0 ? tracker.avg_rating.toFixed(1) : '—'}
                    </p>
                    <StarDisplay rating={tracker.avg_rating} />
                    <p className="text-xs text-slate-500 mt-2">{totalReviews} reviews</p>
                  </div>
                  <div className="flex-1 space-y-1">
                    {[5, 4, 3, 2, 1].map(stars => (
                      <RatingBar
                        key={stars}
                        stars={stars}
                        count={Number(dist[String(stars)] || 0)}
                        total={totalReviews}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Weekly Velocity */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
                  <TrendingUp size={14} className="text-amber-400" />
                  Weekly Review Velocity
                </h2>
                <div className="flex items-end justify-around h-32">
                  <VelocityBar label="Week 1" count={tracker.reviews_week_1 ?? 0} max={weeklyMax} />
                  <VelocityBar label="Week 2" count={tracker.reviews_week_2 ?? 0} max={weeklyMax} />
                  <VelocityBar label="Week 3" count={tracker.reviews_week_3 ?? 0} max={weeklyMax} />
                  <VelocityBar label="Week 4" count={tracker.reviews_week_4 ?? 0} max={weeklyMax} />
                </div>
              </div>
            </div>

            {/* Themes */}
            {(tracker.positive_themes?.length > 0 || tracker.negative_themes?.length > 0) && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Positive themes */}
                {tracker.positive_themes?.length > 0 && (
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <ThumbsUp size={14} className="text-emerald-400" />
                      Positive Themes
                    </h2>
                    <div className="flex flex-wrap gap-2">
                      {tracker.positive_themes.map((theme, i) => (
                        <ThemeChip key={i} label={theme} positive />
                      ))}
                    </div>
                  </div>
                )}

                {/* Negative themes */}
                {tracker.negative_themes?.length > 0 && (
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <ThumbsDown size={14} className="text-red-400" />
                      Negative Themes
                    </h2>
                    <div className="flex flex-wrap gap-2">
                      {tracker.negative_themes.map((theme, i) => (
                        <ThemeChip key={i} label={theme} positive={false} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ARC Stats card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5 flex items-center gap-2">
                <Users size={14} className="text-purple-400" />
                ARC Reader Program
              </h2>
              <div className="grid grid-cols-3 gap-6 text-center">
                <div>
                  <p className="text-3xl font-bold text-purple-400">{tracker.arc_emails_sent}</p>
                  <p className="text-sm text-slate-400 mt-1">Emails Sent</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-white">{tracker.arc_reviews_received}</p>
                  <p className="text-sm text-slate-400 mt-1">Reviews Received</p>
                </div>
                <div>
                  <p className={`text-3xl font-bold ${
                    tracker.arc_conversion_rate >= 0.5 ? 'text-emerald-400' :
                    tracker.arc_conversion_rate >= 0.3 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {arcConvPct}
                  </p>
                  <p className="text-sm text-slate-400 mt-1">Conversion Rate</p>
                </div>
              </div>
              {tracker.arc_emails_sent > 0 && (
                <div className="mt-5">
                  <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                    <span>Conversion progress</span>
                    <span>{tracker.arc_reviews_received} / {tracker.arc_emails_sent}</span>
                  </div>
                  <div className="bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-600 to-purple-400 rounded-full transition-all duration-700"
                      style={{ width: `${Math.min((tracker.arc_reviews_received / tracker.arc_emails_sent) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Last scraped */}
            {tracker.last_scraped && (
              <p className="text-xs text-slate-600 text-center flex items-center justify-center gap-1.5 pb-4">
                <Clock size={11} />
                Last synced from Amazon: {new Date(tracker.last_scraped).toLocaleString()}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
