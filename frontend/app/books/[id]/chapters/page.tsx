'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Eye,
  BookOpen,
  ArrowLeft,
  Globe,
  GlobeLock,
  Loader2,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Lock,
  Unlock,
} from 'lucide-react';
import { getBook, getChapters, approveChapter, rejectChapter, markChapterReady, updateChapter } from '@/lib/api';
import type { Book, Chapter, ChapterStatus } from '@/types';

// ── Status helpers ────────────────────────────────────────────────
const STATUS_STYLE: Record<ChapterStatus, string> = {
  pending:        'bg-slate-700 text-slate-300',
  ready_to_write: 'bg-blue-900/50 text-blue-300',
  writing:        'bg-cyan-900/50 text-cyan-300',
  written:        'bg-yellow-900/50 text-yellow-300',
  pending_qa:     'bg-purple-900/50 text-purple-300',
  approved:       'bg-emerald-900/50 text-emerald-300',
  rejected:       'bg-red-900/50 text-red-300',
  published:      'bg-green-900/50 text-green-300',
};

const STATUS_LABEL: Record<ChapterStatus, string> = {
  pending:        'Pending',
  ready_to_write: 'Ready to Write',
  writing:        'Writing',
  written:        'Written',
  pending_qa:     'Pending QA',
  approved:       'Approved',
  rejected:       'Rejected',
  published:      'Published',
};

// ── Reject Modal ──────────────────────────────────────────────────
function RejectModal({
  chapterId,
  chapterNum,
  onClose,
  onDone,
}: {
  chapterId: number;
  chapterNum: number;
  onClose: () => void;
  onDone: (chapterId: number, newStatus: ChapterStatus) => void;
}) {
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  async function submit() {
    if (!notes.trim()) { setErr('Rejection notes are required.'); return; }
    setBusy(true);
    try {
      const res = await rejectChapter(chapterId, notes.trim());
      onDone(chapterId, res.chapter_status as ChapterStatus);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to reject';
      setErr(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-1">Reject Chapter {chapterNum}</h3>
        <p className="text-slate-400 text-sm mb-4">Add QA notes — the AI will rewrite this chapter.</p>
        <textarea
          className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-white placeholder-slate-500 resize-none h-32 focus:outline-none focus:border-amber-500"
          placeholder="Describe what needs to be fixed…"
          value={notes}
          onChange={e => { setNotes(e.target.value); setErr(''); }}
        />
        {err && <p className="text-red-400 text-xs mt-1">{err}</p>}
        <div className="flex gap-3 mt-4 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={busy}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-semibold px-5 py-2 rounded-lg text-sm transition-colors"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
            Reject & Rewrite
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function ChapterManagePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [book, setBook] = useState<Book | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage]   = useState(1);
  const [filterStatus, setFilterStatus] = useState<ChapterStatus | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy]   = useState<Record<number, boolean>>({});
  const [toast, setToast] = useState<{ msg: string; type: 'ok' | 'err' } | null>(null);
  const [rejectTarget, setRejectTarget] = useState<{ id: number; num: number } | null>(null);

  const PAGE_SIZE = 25;

  const showToast = useCallback((msg: string, type: 'ok' | 'err' = 'ok') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        book: id,
        page,
        page_size: PAGE_SIZE,
        ordering: 'chapter_number',
      };
      if (filterStatus !== 'all') params.status = filterStatus;
      const [bk, ch] = await Promise.all([
        getBook(id),
        getChapters(params as Parameters<typeof getChapters>[0]),
      ]);
      setBook(bk);
      setChapters(ch.results);
      setTotal(ch.count);
    } catch {
      showToast('Failed to load chapters', 'err');
    } finally {
      setLoading(false);
    }
  }, [id, page, filterStatus, showToast]);

  useEffect(() => { load(); }, [load]);

  function setBusyFor(chId: number, val: boolean) {
    setBusy(prev => ({ ...prev, [chId]: val }));
  }

  async function handleApprove(ch: Chapter) {
    setBusyFor(ch.id, true);
    try {
      const res = await approveChapter(ch.id);
      setChapters(prev => prev.map(c => c.id === ch.id ? { ...c, status: res.chapter_status as ChapterStatus } : c));
      showToast(`Chapter ${ch.chapter_number} approved`);
    } catch { showToast('Approve failed', 'err'); }
    finally { setBusyFor(ch.id, false); }
  }

  async function handleMarkReady(ch: Chapter) {
    setBusyFor(ch.id, true);
    try {
      const res = await markChapterReady(ch.id);
      setChapters(prev => prev.map(c => c.id === ch.id ? { ...c, status: res.chapter_status as ChapterStatus } : c));
      showToast(`Chapter ${ch.chapter_number} queued for writing`);
    } catch { showToast('Action failed', 'err'); }
    finally { setBusyFor(ch.id, false); }
  }

  function handleRejectDone(chId: number, newStatus: ChapterStatus) {
    setChapters(prev => prev.map(c => c.id === chId ? { ...c, status: newStatus } : c));
    setRejectTarget(null);
    showToast('Chapter rejected — rewrite queued');
  }

  async function togglePublish(ch: Chapter) {
    setBusyFor(ch.id, true);
    try {
      const updated = await updateChapter(ch.id, { is_published: !ch.is_published });
      setChapters(prev => prev.map(c => c.id === ch.id ? { ...c, is_published: updated.is_published } : c));
      showToast(`Chapter ${ch.chapter_number} ${updated.is_published ? 'published' : 'unpublished'}`);
    } catch { showToast('Toggle failed', 'err'); }
    finally { setBusyFor(ch.id, false); }
  }

  async function toggleFree(ch: Chapter) {
    setBusyFor(ch.id, true);
    try {
      const updated = await updateChapter(ch.id, { is_free: !ch.is_free });
      setChapters(prev => prev.map(c => c.id === ch.id ? { ...c, is_free: updated.is_free } : c));
      showToast(`Chapter ${ch.chapter_number} marked ${updated.is_free ? 'free' : 'paid'}`);
    } catch { showToast('Toggle failed', 'err'); }
    finally { setBusyFor(ch.id, false); }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const approved   = chapters.filter(c => c.status === 'approved').length;
  const inReview   = chapters.filter(c => c.status === 'pending_qa').length;
  const rejected   = chapters.filter(c => c.status === 'rejected').length;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-xl animate-fade-in
          ${toast.type === 'ok' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}`}>
          {toast.msg}
        </div>
      )}

      {/* Reject Modal */}
      {rejectTarget && (
        <RejectModal
          chapterId={rejectTarget.id}
          chapterNum={rejectTarget.num}
          onClose={() => setRejectTarget(null)}
          onDone={handleRejectDone}
        />
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <button onClick={() => router.back()} className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </button>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Chapter Management</p>
              <h1 className="text-xl font-bold text-white truncate max-w-xs sm:max-w-md">
                {book?.title ?? 'Loading…'}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href={`/books/${id}/workflow`}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-2 rounded-lg transition-colors"
            >
              <RefreshCw size={14} /> Workflow
            </Link>
            <Link
              href={`/books/${id}`}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-2 rounded-lg transition-colors"
            >
              <BookOpen size={14} /> Book Page
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Chapters', value: total, color: 'text-white' },
            { label: 'Approved', value: approved, color: 'text-emerald-400' },
            { label: 'In QA Review', value: inReview, color: 'text-purple-400' },
            { label: 'Rejected', value: rejected, color: 'text-red-400' },
          ].map(s => (
            <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-slate-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mb-6 flex-wrap">
          {(['all', 'pending', 'ready_to_write', 'writing', 'written', 'pending_qa', 'approved', 'rejected', 'published'] as const).map(f => (
            <button
              key={f}
              onClick={() => { setFilterStatus(f); setPage(1); }}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                filterStatus === f
                  ? 'bg-amber-500 text-slate-900'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {f === 'all' ? 'All' : STATUS_LABEL[f as ChapterStatus]}
            </button>
          ))}
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-500">
            <Loader2 size={32} className="animate-spin" />
          </div>
        ) : chapters.length === 0 ? (
          <div className="text-center py-16 text-slate-600">
            <BookOpen size={48} className="mx-auto mb-3 opacity-30" />
            <p>No chapters found for this filter.</p>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
                    <th className="text-left px-4 py-3 w-12">#</th>
                    <th className="text-left px-4 py-3">Title</th>
                    <th className="text-left px-4 py-3 w-28">Words</th>
                    <th className="text-left px-4 py-3 w-32">Status</th>
                    <th className="text-left px-4 py-3 w-24">Published</th>
                    <th className="text-left px-4 py-3 w-16">Free</th>
                    <th className="text-right px-4 py-3 w-52">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {chapters.map(ch => (
                    <tr key={ch.id} className="hover:bg-slate-800/50 transition-colors">
                      {/* # */}
                      <td className="px-4 py-3 font-mono text-slate-500">{ch.chapter_number}</td>

                      {/* Title */}
                      <td className="px-4 py-3">
                        <Link
                          href={`/books/${id}/chapters/${ch.chapter_number}`}
                          className="text-white hover:text-amber-400 font-medium transition-colors line-clamp-1"
                        >
                          {ch.title || `Chapter ${ch.chapter_number}`}
                        </Link>
                      </td>

                      {/* Words */}
                      <td className="px-4 py-3 text-slate-400 font-mono">
                        {ch.word_count?.toLocaleString() ?? '—'}
                      </td>

                      {/* Status badge */}
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLE[ch.status]}`}>
                          {STATUS_LABEL[ch.status]}
                        </span>
                      </td>

                      {/* Publish toggle */}
                      <td className="px-4 py-3">
                        <button
                          onClick={() => togglePublish(ch)}
                          disabled={busy[ch.id]}
                          title={ch.is_published ? 'Unpublish' : 'Publish'}
                          className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full transition-colors disabled:opacity-40 ${
                            ch.is_published
                              ? 'bg-emerald-900/50 text-emerald-300 hover:bg-red-900/50 hover:text-red-300'
                              : 'bg-slate-700 text-slate-400 hover:bg-emerald-900/50 hover:text-emerald-300'
                          }`}
                        >
                          {busy[ch.id] ? <Loader2 size={10} className="animate-spin" /> : ch.is_published ? <Globe size={10} /> : <GlobeLock size={10} />}
                          {ch.is_published ? 'Live' : 'Draft'}
                        </button>
                      </td>

                      {/* Free toggle */}
                      <td className="px-4 py-3">
                        <button
                          onClick={() => toggleFree(ch)}
                          disabled={busy[ch.id]}
                          title={ch.is_free ? 'Make paid' : 'Make free'}
                          className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-colors disabled:opacity-40 ${
                            ch.is_free
                              ? 'bg-amber-900/50 text-amber-300 hover:bg-slate-700'
                              : 'bg-slate-700 text-slate-400 hover:bg-amber-900/50 hover:text-amber-300'
                          }`}
                        >
                          {ch.is_free ? <Unlock size={10} /> : <Lock size={10} />}
                          {ch.is_free ? 'Free' : 'Paid'}
                        </button>
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 justify-end">
                          {/* View */}
                          <Link
                            href={`/books/${id}/chapters/${ch.chapter_number}`}
                            title="View Chapter"
                            className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-slate-700 transition-colors"
                          >
                            <Eye size={14} />
                          </Link>

                          {/* Mark Ready (pending state only) */}
                          {ch.status === 'pending' && (
                            <button
                              onClick={() => handleMarkReady(ch)}
                              disabled={busy[ch.id]}
                              title="Queue for AI writing"
                              className="flex items-center gap-1 text-xs bg-blue-900/50 hover:bg-blue-800 text-blue-300 disabled:opacity-40 px-2.5 py-1 rounded-lg transition-colors"
                            >
                              {busy[ch.id] ? <Loader2 size={10} className="animate-spin" /> : <RefreshCw size={10} />}
                              Queue
                            </button>
                          )}

                          {/* Approve (written or pending_qa) */}
                          {(ch.status === 'written' || ch.status === 'pending_qa') && (
                            <button
                              onClick={() => handleApprove(ch)}
                              disabled={busy[ch.id]}
                              title="Approve chapter"
                              className="flex items-center gap-1 text-xs bg-emerald-900/50 hover:bg-emerald-800 text-emerald-300 disabled:opacity-40 px-2.5 py-1 rounded-lg transition-colors"
                            >
                              {busy[ch.id] ? <Loader2 size={10} className="animate-spin" /> : <CheckCircle2 size={10} />}
                              Approve
                            </button>
                          )}

                          {/* Reject */}
                          {(ch.status === 'written' || ch.status === 'pending_qa' || ch.status === 'approved') && (
                            <button
                              onClick={() => setRejectTarget({ id: ch.id, num: ch.chapter_number })}
                              disabled={busy[ch.id]}
                              title="Reject & rewrite"
                              className="flex items-center gap-1 text-xs bg-red-900/50 hover:bg-red-800 text-red-300 disabled:opacity-40 px-2.5 py-1 rounded-lg transition-colors"
                            >
                              <XCircle size={10} />
                              Reject
                            </button>
                          )}

                          {/* Warning for rejected */}
                          {ch.status === 'rejected' && (
                            <span className="flex items-center gap-1 text-xs text-yellow-400">
                              <AlertTriangle size={10} /> Rewriting
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="border-t border-slate-800 px-4 py-3 flex items-center justify-between text-sm text-slate-400">
                <span>Page {page} of {totalPages} &middot; {total} chapters</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-1. disabled:opacity-30 hover:text-white disabled:cursor-not-allowed"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-1 disabled:opacity-30 hover:text-white disabled:cursor-not-allowed"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
