'use client';

import { useState, useCallback, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, ChevronRight, Download, Loader2, CheckCircle,
  BookOpen, FileText, AlertCircle, ImageIcon, RefreshCw,
} from 'lucide-react';
import { getBook, getChapters, exportBook, triggerLifecycleAction } from '@/lib/api';
import type { LifecycleAction } from '@/lib/api';
import type { Book, Chapter } from '@/types';
import LifecycleBadge from '@/components/LifecycleBadge';

// ── FSM transition map ─────────────────────────────────────────────────────
// Maps current lifecycle_status → available action(s)
const TRANSITIONS: Record<string, { action: LifecycleAction; label: string; description: string }[]> = {
  concept_pending: [
    { action: 'start_keyword_research', label: 'Start Keyword Research', description: 'Begin KDP SEO keyword analysis' },
  ],
  keyword_research: [
    { action: 'approve_keywords', label: 'Approve Keywords', description: 'Lock keywords and proceed to description' },
  ],
  keyword_approved: [
    { action: 'start_description_generation', label: 'Generate Description', description: 'AI generates book blurb' },
    { action: 'start_writing', label: 'Skip to Writing', description: 'Jump directly to chapter generation' },
  ],
  description_generation: [
    { action: 'approve_description', label: 'Approve Description', description: 'Lock blurb and proceed' },
  ],
  description_approved: [
    { action: 'start_bible_generation', label: 'Generate Story Bible', description: 'AI builds story architecture' },
  ],
  bible_generation: [
    { action: 'approve_bible', label: 'Approve Bible', description: 'Lock story bible, start writing' },
    { action: 'start_writing', label: 'Start Writing Now', description: 'Begin chapter generation' },
  ],
  bible_approved: [
    { action: 'start_writing', label: 'Start Writing', description: 'Begin AI chapter generation pipeline' },
  ],
  writing_in_progress: [
    { action: 'submit_for_qa', label: 'Submit for QA', description: 'Send all chapters to quality review' },
  ],
  qa_review: [
    { action: 'approve_for_export', label: 'Approve for Export', description: 'Pass QA — unlock .docx/.epub export' },
  ],
  export_ready: [
    { action: 'publish_to_kdp', label: 'Mark as Published on KDP', description: 'Set status to published_kdp' },
  ],
};

// ── Chapter status colour map ──────────────────────────────────────────────
const CHAPTER_STATUS_COLOR: Record<string, string> = {
  pending:         'bg-slate-600',
  ready_to_write:  'bg-blue-500',
  written:         'bg-indigo-500',
  qa_review:       'bg-orange-500',
  approved:        'bg-emerald-500',
  rejected:        'bg-red-500',
};

export default function WorkflowPage() {
  const { id } = useParams<{ id: string }>();
  const bookId = Number(id);

  const [book, setBook]         = useState<Book | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading]   = useState(true);
  const [busy, setBusy]         = useState<string | null>(null);   // which action is in-progress
  const [exportBusy, setExportBusy] = useState<'docx' | 'epub' | null>(null);
  const [toast, setToast]       = useState<{ msg: string; ok: boolean } | null>(null);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [bookData, chapData] = await Promise.all([
        getBook(bookId),
        getChapters({ book: bookId }),
      ]);
      setBook(bookData);
      setChapters(chapData.results);
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => { load(); }, [load]);

  async function handleTransition(action: LifecycleAction) {
    if (!book) return;
    setBusy(action);
    try {
      const result = await triggerLifecycleAction(bookId, action);
      setBook((b) => b ? { ...b, lifecycle_status: result.lifecycle_status as Book['lifecycle_status'] } : b);
      showToast(result.message || 'Transition successful');
    } catch (err: unknown) {
      const anyErr = err as { response?: { data?: { error?: string } } };
      showToast(anyErr?.response?.data?.error || 'Action failed', false);
    } finally {
      setBusy(null);
    }
  }

  async function handleExport(format: 'docx' | 'epub') {
    setExportBusy(format);
    try {
      await exportBook(bookId, format);
      showToast(`${format.toUpperCase()} export downloaded`);
    } catch {
      showToast('Export failed. Check that all chapters are approved.', false);
    } finally {
      setExportBusy(null);
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <Loader2 className="animate-spin text-amber-400" size={32} />
    </div>
  );

  if (!book) return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center text-slate-400">
      Book not found.
    </div>
  );

  const available = TRANSITIONS[book.lifecycle_status] || [];
  const canExport = ['export_ready', 'published_kdp', 'published_all'].includes(book.lifecycle_status);

  // Chapter stats
  const statusGroups: Record<string, number> = {};
  chapters.forEach((c) => { statusGroups[c.status] = (statusGroups[c.status] || 0) + 1; });
  const approvedCount = statusGroups['approved'] || 0;
  const totalTarget   = (book as Book & { target_chapter_count?: number }).target_chapter_count ?? 80;
  const wordCount     = (book as Book & { current_word_count?: number }).current_word_count ?? 0;

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-20 right-4 z-[200] px-4 py-3 rounded-xl shadow-xl text-sm font-medium transition-all ${toast.ok ? 'bg-emerald-800 text-emerald-100' : 'bg-red-800 text-red-100'}`}>
          {toast.msg}
        </div>
      )}

      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Breadcrumb */}
        <nav className="text-sm text-slate-500 flex items-center gap-2 flex-wrap">
          <Link href="/dashboard" className="hover:text-slate-300 flex items-center gap-1">Dashboard</Link>
          <ChevronRight size={12} />
          <Link href="/books" className="hover:text-slate-300">Books</Link>
          <ChevronRight size={12} />
          <Link href={`/books/${bookId}`} className="hover:text-slate-300 max-w-xs truncate">{book.title}</Link>
          <ChevronRight size={12} />
          <span className="text-white">Workflow</span>
        </nav>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <Link href={`/books/${bookId}`} className="text-slate-400 hover:text-white text-sm flex items-center gap-1 mb-2 transition-colors">
              <ArrowLeft size={14} /> Back to book
            </Link>
            <h1 className="text-2xl font-bold text-white line-clamp-2">{book.title}</h1>
            <div className="flex items-center gap-2 mt-2">
              <LifecycleBadge status={book.lifecycle_status} size="sm" />
              {typeof (book.pen_name) === 'object' && (
                <span className="text-slate-500 text-sm">by {(book.pen_name as { name: string }).name}</span>
              )}
            </div>
          </div>
          <button onClick={load} className="shrink-0 p-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 hover:text-white transition-colors">
            <RefreshCw size={16} />
          </button>
        </div>

        {/* Progress bar */}
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-white font-semibold text-sm">Production Progress</p>
            <p className="text-amber-400 font-bold text-sm">{wordCount.toLocaleString()} words</p>
          </div>
          <ProgressBar
            label="Lifecycle"
            value={(book as Book & { progress?: number }).progress
              ?? progressForStatus(book.lifecycle_status)}
            max={100}
            color="bg-amber-500"
          />
          <ProgressBar
            label={`Chapters approved (${approvedCount} / ${totalTarget})`}
            value={approvedCount}
            max={totalTarget}
            color="bg-emerald-500"
          />
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatBox icon={<FileText size={16} />}    label="Total Chapters" val={chapters.length}   color="text-slate-300" />
          <StatBox icon={<CheckCircle size={16} />} label="Approved"       val={approvedCount}     color="text-emerald-400" />
          <StatBox icon={<AlertCircle size={16} />} label="QA Review"      val={statusGroups['qa_review'] || 0} color="text-orange-400" />
          <StatBox icon={<BookOpen size={16} />}    label="Published"      val={chapters.filter(c => c.is_published).length} color="text-blue-400" />
        </div>

        {/* FSM Transition Actions */}
        {available.length > 0 && (
          <div className="bg-slate-800 border border-amber-500/30 rounded-2xl p-5 space-y-3">
            <h2 className="text-white font-semibold flex items-center gap-2">
              <CheckCircle size={16} className="text-amber-400" />
              Available Actions
            </h2>
            <div className="space-y-2">
              {available.map((t) => (
                <div key={t.action} className="flex items-center justify-between gap-4 p-3 bg-slate-900/60 rounded-xl">
                  <div>
                    <p className="text-white text-sm font-medium">{t.label}</p>
                    <p className="text-slate-500 text-xs">{t.description}</p>
                  </div>
                  <button
                    onClick={() => handleTransition(t.action)}
                    disabled={!!busy}
                    className="shrink-0 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 text-sm font-semibold px-4 py-2 rounded-lg transition-colors disabled:opacity-60"
                  >
                    {busy === t.action ? <Loader2 size={14} className="animate-spin" /> : <ChevronRight size={14} />}
                    {busy === t.action ? 'Working…' : 'Run'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Export Panel */}
        <div className={`bg-slate-800 border rounded-2xl p-5 space-y-3 ${canExport ? 'border-emerald-500/40' : 'border-slate-700'}`}>
          <h2 className="text-white font-semibold flex items-center gap-2">
            <Download size={16} className={canExport ? 'text-emerald-400' : 'text-slate-500'} />
            Export Files
          </h2>
          {!canExport ? (
            <p className="text-slate-500 text-sm">
              Export unlocks after the book passes QA and reaches{' '}
              <LifecycleBadge status="export_ready" size="xs" /> status.
            </p>
          ) : (
            <div className="flex flex-wrap gap-3">
              {(['docx', 'epub'] as const).map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => handleExport(fmt)}
                  disabled={!!exportBusy}
                  className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 border border-slate-600 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors disabled:opacity-60"
                >
                  {exportBusy === fmt ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                  Download .{fmt.toUpperCase()}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-3 gap-3">
          <QuickLink href={`/books/${bookId}`}        icon={<BookOpen size={15} />}  label="Storefront View" />
          <QuickLink href={`/books/${bookId}/covers`} icon={<ImageIcon size={15} />} label="KDP Covers" />
          <QuickLink href={`/books/${bookId}/chapters/1`} icon={<FileText size={15} />} label="Chapter 1" />
        </div>

        {/* Chapter Heatmap */}
        {chapters.length > 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5">
            <h2 className="text-white font-semibold mb-3 flex items-center gap-2">
              <FileText size={16} className="text-amber-400" />
              Chapter Status Heatmap
              <span className="text-slate-500 text-xs font-normal ml-1">(grid: each square = 1 chapter)</span>
            </h2>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {chapters.map((c) => (
                <div
                  key={c.id}
                  title={`Ch.${c.chapter_number}: ${c.title || '—'} [${c.status}]`}
                  className={`w-4 h-4 rounded-sm transition-transform hover:scale-125 ${CHAPTER_STATUS_COLOR[c.status] ?? 'bg-slate-600'}`}
                />
              ))}
            </div>
            {/* Legend */}
            <div className="flex flex-wrap gap-3">
              {Object.entries(CHAPTER_STATUS_COLOR).map(([s, c]) => (
                <div key={s} className="flex items-center gap-1.5">
                  <div className={`w-3 h-3 rounded-sm ${c}`} />
                  <span className="text-slate-400 text-xs capitalize">{s.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function progressForStatus(s: string): number {
  const m: Record<string, number> = {
    concept_pending: 5, keyword_research: 10, keyword_approved: 15,
    description_generation: 20, description_approved: 25,
    bible_generation: 30, bible_approved: 35,
    writing_in_progress: 50, qa_review: 80,
    export_ready: 90, published_kdp: 95, published_all: 100, archived: 100,
  };
  return m[s] ?? 0;
}

function ProgressBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = Math.min(100, Math.round((value / Math.max(max, 1)) * 100));
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400 mb-1">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="bg-slate-700 rounded-full h-2.5 overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function StatBox({ icon, label, val, color }: { icon: React.ReactNode; label: string; val: number; color: string }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 flex items-center gap-3">
      <span className={color}>{icon}</span>
      <div>
        <p className={`text-lg font-bold ${color}`}>{val}</p>
        <p className="text-slate-500 text-xs">{label}</p>
      </div>
    </div>
  );
}

function QuickLink({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-300 hover:text-white hover:border-slate-600 text-sm transition-colors"
    >
      <span className="text-amber-400">{icon}</span>
      {label}
    </Link>
  );
}
