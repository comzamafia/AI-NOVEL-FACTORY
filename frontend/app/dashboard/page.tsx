'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  BarChart3, BookOpen, FileText, Globe, TrendingUp,
  CheckCircle, RefreshCw, AlertCircle, DollarSign, UserCog, BookPlus,
} from 'lucide-react';
import { getPipelineStats } from '@/lib/api';
import type { PipelineStats } from '@/types';
import LifecycleBadge from '@/components/LifecycleBadge';

// Lifecycle pipeline order (for the kanban bar)
const PIPELINE_ORDER = [
  'concept_pending',
  'keyword_research',
  'keyword_approved',
  'description_generation',
  'description_approved',
  'bible_generation',
  'bible_approved',
  'writing_in_progress',
  'qa_review',
  'export_ready',
  'published_kdp',
  'published_all',
  'archived',
];

export default function DashboardPage() {
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setStats(await getPipelineStats());
    } catch {
      setError('Could not load dashboard data. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingState />;
  if (error)   return <ErrorState msg={error} onRetry={load} />;
  if (!stats)  return null;

  const { totals, status_counts, chapters, recent_books } = stats;

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
              <BarChart3 className="text-amber-400" size={28} />
              Production Dashboard
            </h1>
            <p className="text-slate-400 mt-1">Real-time overview of the AI Novel Factory pipeline</p>
          </div>
          <button
            onClick={load}
            className="flex items-center gap-2 bg-slate-800 border border-slate-700 text-slate-300 hover:text-white px-4 py-2 rounded-xl text-sm transition-colors"
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <KPICard icon={<BookOpen size={18} />}   label="Total Books"      value={totals.books}                          color="text-white" />
          <KPICard icon={<Globe size={18} />}       label="Published"        value={totals.published}                      color="text-emerald-400" />
          <KPICard icon={<DollarSign size={18} />}  label="Revenue"          value={`$${totals.revenue_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} color="text-amber-400" />
          <KPICard icon={<FileText size={18} />}    label="Words Written"    value={totals.words.toLocaleString()}         color="text-blue-400" />
          <KPICard icon={<AlertCircle size={18} />} label="Avg AI Detection" value={`${totals.avg_ai_detection}%`}        color={totals.avg_ai_detection > 25 ? 'text-red-400' : 'text-green-400'} />
          <KPICard icon={<TrendingUp size={18} />}  label="Avg Plagiarism"   value={`${totals.avg_plagiarism}%`}          color={totals.avg_plagiarism > 5 ? 'text-red-400' : 'text-green-400'} />
        </div>

        {/* Chapter Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Total Chapters',     val: chapters.total,     icon: <FileText size={16} />,     color: 'text-slate-300' },
            { label: 'Approved',           val: chapters.approved,  icon: <CheckCircle size={16} />,  color: 'text-emerald-400' },
            { label: 'Published',          val: chapters.published, icon: <Globe size={16} />,        color: 'text-blue-400' },
            { label: 'In QA Review',       val: chapters.in_review, icon: <AlertCircle size={16} />,  color: 'text-orange-400' },
          ].map(({ label, val, icon, color }) => (
            <div key={label} className="bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3 flex items-center gap-3">
              <span className={color}>{icon}</span>
              <div>
                <p className={`text-xl font-bold ${color}`}>{val}</p>
                <p className="text-slate-500 text-xs">{label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Pipeline Stage Distribution */}
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5">
          <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
            <BarChart3 size={16} className="text-amber-400" />
            Pipeline Distribution
          </h2>
          <div className="space-y-2">
            {PIPELINE_ORDER.map((s) => {
              const count = status_counts[s] ?? 0;
              const max = Math.max(...Object.values(status_counts), 1);
              const pct = Math.round((count / max) * 100);
              return (
                <div key={s} className="flex items-center gap-3">
                  <div className="w-40 shrink-0">
                    <LifecycleBadge status={s} size="xs" />
                  </div>
                  <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full transition-all duration-700"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-slate-400 text-xs w-4 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-semibold flex items-center gap-2">
              <RefreshCw size={16} className="text-amber-400" />
              Recently Updated Books
            </h2>
            <Link href="/books" className="text-amber-400 hover:text-amber-300 text-sm transition-colors">
              View all →
            </Link>
          </div>
          <div className="space-y-3">
            {recent_books.length === 0 && (
              <p className="text-slate-500 text-sm text-center py-6">No books yet.</p>
            )}
            {recent_books.map((b) => (
              <div key={b.id} className="flex items-center gap-4 p-3 bg-slate-900/50 rounded-xl group hover:bg-slate-900 transition-colors">
                {/* Progress ring */}
                <div className="relative w-10 h-10 shrink-0">
                  <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="15" fill="none" stroke="#334155" strokeWidth="3" />
                    <circle
                      cx="18" cy="18" r="15" fill="none"
                      stroke="#f59e0b" strokeWidth="3"
                      strokeDasharray={`${(b.progress / 100) * 94.2} 94.2`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-[9px] text-amber-400 font-bold">
                    {b.progress}%
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/books/${b.id}/workflow`}
                    className="text-white text-sm font-medium hover:text-amber-400 transition-colors line-clamp-1 group-hover:underline"
                  >
                    {b.title}
                  </Link>
                  <p className="text-slate-500 text-xs">{b.pen_name} · {b.current_word_count.toLocaleString()} words</p>
                </div>
                <div className="shrink-0 hidden sm:block">
                  <LifecycleBadge status={b.lifecycle_status} size="xs" />
                </div>
                <Link
                  href={`/books/${b.id}/workflow`}
                  className="shrink-0 text-slate-600 hover:text-amber-400 transition-colors text-xs"
                >
                  →
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { href: '/books/new', icon: <BookPlus size={18} />,  label: 'New Book',        sub: 'Create a book' },
            { href: '/pen-names', icon: <UserCog size={18} />,   label: 'Pen Names',       sub: 'Manage authors' },
            { href: '/books',     icon: <BookOpen size={18} />,  label: 'Browse Books',    sub: 'Storefront view' },
            { href: '/authors',   icon: <Globe size={18} />,     label: 'Authors',         sub: 'Public view' },
            { href: '/search',    icon: <FileText size={18} />,  label: 'Search',          sub: 'Find anything' },
          ].map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="bg-slate-800 border border-slate-700 rounded-2xl p-4 hover:border-amber-500/50 transition-colors group"
            >
              <div className="text-amber-400 mb-2">{l.icon}</div>
              <p className="text-white text-sm font-medium">{l.label}</p>
              <p className="text-slate-500 text-xs">{l.sub}</p>
            </Link>
          ))}
          <a
            href="http://localhost:8000/admin/"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-slate-800 border border-slate-700 rounded-2xl p-4 hover:border-amber-500/50 transition-colors group"
          >
            <div className="text-amber-400 mb-2"><BarChart3 size={18} /></div>
            <p className="text-white text-sm font-medium">Django Admin</p>
            <p className="text-slate-500 text-xs">Full backend control</p>
          </a>
        </div>

      </div>
    </div>
  );
}

function KPICard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string | number; color: string }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-4">
      <div className={`mb-2 ${color}`}>{icon}</div>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-slate-500 text-xs mt-0.5">{label}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center space-y-3">
        <RefreshCw size={32} className="animate-spin text-amber-400 mx-auto" />
        <p className="text-slate-400">Loading dashboard…</p>
      </div>
    </div>
  );
}

function ErrorState({ msg, onRetry }: { msg: string; onRetry: () => void }) {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="text-center max-w-md space-y-4">
        <AlertCircle size={40} className="text-red-400 mx-auto" />
        <p className="text-white font-semibold">Dashboard Unavailable</p>
        <p className="text-slate-400 text-sm">{msg}</p>
        <button onClick={onRetry} className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-6 py-2 rounded-full text-sm">
          Try Again
        </button>
      </div>
    </div>
  );
}
