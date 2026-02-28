'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Users, ArrowLeft, RefreshCw, Loader2, Plus, Pencil,
  Trash2, X, Save, CheckCircle, AlertCircle,
  Mail, ShieldCheck, ShieldX, Star, Send,
} from 'lucide-react';
import {
  getARCReaders,
  createARCReader,
  updateARCReader,
  deleteARCReader,
  markARCSent,
  markARCReviewed,
} from '@/lib/api';
import type { ARCReader } from '@/types';

// ── Reliability Badge ─────────────────────────────────────────
function ReliabilityBadge({ reader }: { reader: ARCReader }) {
  if (reader.email_opt_out) {
    return <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-400 border border-slate-600">Opted Out</span>;
  }
  return reader.is_reliable
    ? <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 flex items-center gap-1 w-fit"><ShieldCheck size={10} />Reliable</span>
    : <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/25 flex items-center gap-1 w-fit"><ShieldX size={10} />Unreliable</span>;
}

// ── Stars ─────────────────────────────────────────────────────
function Stars({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map(s => (
        <Star key={s} size={10} className={s <= Math.round(rating) ? 'text-amber-400 fill-amber-400' : 'text-slate-700'} />
      ))}
      <span className="text-xs text-slate-500 ml-1">{rating.toFixed(1)}</span>
    </div>
  );
}

// ── Reliability Bar ───────────────────────────────────────────
function ReliabilityBar({ rate }: { rate: number | null }) {
  if (rate === null) return <span className="text-xs text-slate-600">No data</span>;
  const color = rate >= 70 ? 'bg-emerald-500' : rate >= 40 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${Math.min(rate, 100)}%` }} />
      </div>
      <span className="text-xs text-slate-400">{rate.toFixed(0)}%</span>
    </div>
  );
}

// ── Add/Edit Modal ────────────────────────────────────────────
interface ReaderForm {
  name: string; email: string;
  genres_interested: string;
  notes: string; email_opt_out: boolean;
}

const EMPTY: ReaderForm = { name: '', email: '', genres_interested: '', notes: '', email_opt_out: false };

function ReaderModal({
  initial, onClose, onSaved,
}: {
  initial: ARCReader | null;
  onClose: () => void;
  onSaved: (r: ARCReader) => void;
}) {
  const isEdit = !!initial;
  const [form, setForm] = useState<ReaderForm>(
    initial ? {
      name: initial.name,
      email: initial.email,
      genres_interested: initial.genres_interested.join(', '),
      notes: initial.notes,
      email_opt_out: initial.email_opt_out,
    } : { ...EMPTY }
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  function f(key: keyof ReaderForm) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value }));
  }

  async function submit() {
    if (!form.email.trim()) { setErr('Email is required'); return; }
    setBusy(true);
    try {
      const payload: Partial<ARCReader> = {
        name: form.name.trim(),
        email: form.email.trim(),
        genres_interested: form.genres_interested.split(',').map(s => s.trim()).filter(Boolean),
        notes: form.notes.trim(),
        email_opt_out: form.email_opt_out,
      };
      const saved = isEdit
        ? await updateARCReader(initial!.id, payload)
        : await createARCReader(payload);
      onSaved(saved);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 overflow-y-auto">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl my-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Users size={18} className="text-amber-400" />
            {isEdit ? 'Edit ARC Reader' : 'Add ARC Reader'}
          </h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white">{<X size={18} />}</button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Name</label>
            <input type="text" value={form.name} onChange={f('name')} placeholder="Reader name"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Email *</label>
            <input type="email" value={form.email} onChange={f('email')} placeholder="reader@example.com"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Genre Interests (comma-separated)</label>
            <input type="text" value={form.genres_interested} onChange={f('genres_interested')} placeholder="Thriller, Mystery, Romance"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Notes</label>
            <textarea rows={3} value={form.notes} onChange={f('notes')} placeholder="Any notes about this reader…"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none resize-none" />
          </div>
          <div className="flex items-center gap-3 py-1">
            <input type="checkbox" id="opt_out" checked={form.email_opt_out}
              onChange={e => setForm(p => ({ ...p, email_opt_out: e.target.checked }))}
              className="w-4 h-4 rounded accent-amber-500" />
            <label htmlFor="opt_out" className="text-sm text-slate-300 cursor-pointer">Email opt-out</label>
          </div>
          {err && <p className="text-red-400 text-xs">{err}</p>}
          <div className="flex gap-3 pt-1">
            <button onClick={submit} disabled={busy}
              className="flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold py-2.5 rounded-xl transition-colors disabled:opacity-50">
              {busy ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              {busy ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Reader'}
            </button>
            <button onClick={onClose} className="px-5 py-2.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Mark Reviewed Modal ───────────────────────────────────────
function ReviewedModal({
  reader, onClose, onDone,
}: { reader: ARCReader; onClose: () => void; onDone: (r: ARCReader) => void }) {
  const [rating, setRating] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    try {
      const updated = await markARCReviewed(reader.id, rating ? parseFloat(rating) : undefined);
      onDone(updated);
    } finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-xs p-6 shadow-2xl">
        <h3 className="text-base font-bold text-white mb-4">Record Review — {reader.name}</h3>
        <div className="mb-4">
          <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Rating Given (optional)</label>
          <input type="number" min="1" max="5" step="0.1" value={rating}
            onChange={e => setRating(e.target.value)} placeholder="1–5"
            className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
        </div>
        <div className="flex gap-3">
          <button onClick={submit} disabled={busy}
            className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-xl transition-colors">
            {busy ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
            {busy ? 'Saving…' : 'Confirm Review'}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl bg-slate-700 text-slate-300 transition-colors">Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function ARCReadersPage() {
  const [readers,  setReaders]  = useState<ARCReader[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [filter,   setFilter]   = useState<'all' | 'reliable' | 'unreliable' | 'opt_out'>('all');
  const [search,   setSearch]   = useState('');
  const [modal,    setModal]    = useState<{ open: boolean; editing: ARCReader | null }>({ open: false, editing: null });
  const [reviewed, setReviewed] = useState<ARCReader | null>(null);
  const [del,      setDel]      = useState<number | null>(null);
  const [sending,  setSending]  = useState<number | null>(null);
  const [toast,    setToast]    = useState<{ msg: string; ok: boolean } | null>(null);

  function showToast(msg: string, ok = true) {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params =
        filter === 'reliable'   ? { is_reliable: true }  :
        filter === 'unreliable' ? { is_reliable: false } :
        filter === 'opt_out'    ? {} : {};
      const data = await getARCReaders({ ...params, search: search || undefined });
      setReaders(
        filter === 'opt_out'
          ? data.filter(r => r.email_opt_out)
          : filter === 'all'
            ? data
            : data
      );
    } finally { setLoading(false); }
  }, [filter, search]);

  useEffect(() => { load(); }, [load]);

  async function handleDelete(r: ARCReader) {
    if (!confirm(`Remove ${r.name} from ARC list?`)) return;
    setDel(r.id);
    try {
      await deleteARCReader(r.id);
      setReaders(p => p.filter(x => x.id !== r.id));
      showToast('Reader removed');
    } catch { showToast('Failed', false); }
    finally { setDel(null); }
  }

  async function handleSent(r: ARCReader) {
    if (!confirm(`Mark ARC copy as sent to ${r.name}?`)) return;
    setSending(r.id);
    try {
      const updated = await markARCSent(r.id);
      setReaders(p => p.map(x => x.id === updated.id ? updated : x));
      showToast(`ARC sent to ${r.name}`);
    } catch { showToast('Failed', false); }
    finally { setSending(null); }
  }

  function handleSaved(saved: ARCReader) {
    setReaders(p => {
      const idx = p.findIndex(x => x.id === saved.id);
      if (idx >= 0) { const n = [...p]; n[idx] = saved; return n; }
      return [...p, saved];
    });
    setModal({ open: false, editing: null });
    showToast(modal.editing ? 'Updated' : 'Reader added');
  }

  function handleReviewSaved(updated: ARCReader) {
    setReaders(p => p.map(x => x.id === updated.id ? updated : x));
    setReviewed(null);
    showToast('Review recorded');
  }

  // Aggregates
  const reliableCount   = readers.filter(r => r.is_reliable && !r.email_opt_out).length;
  const totalReviews    = readers.reduce((s, r) => s + r.reviews_left_count, 0);
  const avgRate         = readers.filter(r => r.reliability_rate !== null).reduce((s, r, _i, a) => s + (r.reliability_rate! / a.length), 0);

  const FILTERS = [
    { value: 'all',        label: 'All'        },
    { value: 'reliable',   label: 'Reliable'   },
    { value: 'unreliable', label: 'Unreliable' },
    { value: 'opt_out',    label: 'Opted Out'  },
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
        <ReaderModal initial={modal.editing} onClose={() => setModal({ open: false, editing: null })} onSaved={handleSaved} />
      )}
      {reviewed && (
        <ReviewedModal reader={reviewed} onClose={() => setReviewed(null)} onDone={handleReviewSaved} />
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </Link>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">ARC Campaign</p>
              <h1 className="text-xl font-bold">ARC Readers</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setModal({ open: true, editing: null })}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold text-sm px-4 py-2 rounded-xl transition-colors">
              <Plus size={14} /> Add Reader
            </button>
            <button onClick={load} disabled={loading}
              className="text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 p-2 rounded-lg transition-colors disabled:opacity-40">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-amber-400"><Users size={20} /></div>
            <p className="text-2xl font-bold">{readers.length}</p>
            <p className="text-sm text-slate-400 mt-0.5">Total Readers</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-emerald-400"><ShieldCheck size={20} /></div>
            <p className="text-2xl font-bold text-emerald-400">{reliableCount}</p>
            <p className="text-sm text-slate-400 mt-0.5">Reliable</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-blue-400"><Star size={20} /></div>
            <p className="text-2xl font-bold text-blue-400">{totalReviews.toLocaleString()}</p>
            <p className="text-sm text-slate-400 mt-0.5">Total Reviews Left</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="mb-2 text-purple-400"><CheckCircle size={20} /></div>
            <p className="text-2xl font-bold text-purple-400">{avgRate.toFixed(1)}%</p>
            <p className="text-sm text-slate-400 mt-0.5">Avg Reliability</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <input
            type="text" placeholder="Search name or email…" value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 min-w-[200px] max-w-sm px-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500"
          />
          <div className="flex gap-1">
            {FILTERS.map(f => (
              <button key={f.value}
                onClick={() => setFilter(f.value as typeof filter)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  filter === f.value
                    ? 'bg-amber-500 border-amber-500 text-slate-900 font-semibold'
                    : 'border-slate-700 text-slate-400 hover:border-slate-500'
                }`}>
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-500">
            <Loader2 size={36} className="animate-spin" />
          </div>
        ) : readers.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <Users size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400">No ARC readers yet.</p>
            <button onClick={() => setModal({ open: true, editing: null })}
              className="mt-4 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-6 py-3 rounded-xl transition-colors mx-auto">
              <Plus size={16} /> Add First Reader
            </button>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
                    <th className="text-left px-5 py-3">Reader</th>
                    <th className="text-center px-4 py-3">Status</th>
                    <th className="text-center px-4 py-3">ARCs Sent</th>
                    <th className="text-center px-4 py-3">Reviews Left</th>
                    <th className="text-center px-4 py-3">Reliability</th>
                    <th className="text-left px-4 py-3">Avg Rating</th>
                    <th className="text-left px-4 py-3">Genres</th>
                    <th className="text-center px-4 py-3">Last Contacted</th>
                    <th className="py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {readers.map((r, i) => (
                    <tr key={r.id} className={`border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${i % 2 === 0 ? '' : 'bg-slate-900/50'}`}>
                      <td className="px-5 py-4">
                        <p className="font-medium text-white">{r.name}</p>
                        <p className="text-slate-500 text-xs mt-0.5 flex items-center gap-1">
                          <Mail size={10} />{r.email}
                        </p>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <div className="flex justify-center">
                          <ReliabilityBadge reader={r} />
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center text-white font-mono">{r.arc_copies_received}</td>
                      <td className="px-4 py-4 text-center text-emerald-400 font-mono font-semibold">{r.reviews_left_count}</td>
                      <td className="px-4 py-4">
                        <div className="flex justify-center">
                          <ReliabilityBar rate={r.reliability_rate} />
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <Stars rating={r.avg_rating_given} />
                      </td>
                      <td className="px-4 py-4 max-w-[160px]">
                        <div className="flex flex-wrap gap-1">
                          {r.genres_interested.slice(0, 3).map(g => (
                            <span key={g} className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">{g}</span>
                          ))}
                          {r.genres_interested.length > 3 && (
                            <span className="text-xs text-slate-600">+{r.genres_interested.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center text-slate-500 text-xs">
                        {r.last_email_sent ? new Date(r.last_email_sent).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-1">
                          {!r.email_opt_out && (
                            <>
                              <button onClick={() => handleSent(r)} disabled={sending === r.id}
                                className="text-slate-500 hover:text-amber-400 transition-colors p-1 disabled:opacity-40" title="Mark ARC sent">
                                {sending === r.id ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                              </button>
                              <button onClick={() => setReviewed(r)}
                                className="text-slate-500 hover:text-emerald-400 transition-colors p-1" title="Mark reviewed">
                                <CheckCircle size={13} />
                              </button>
                            </>
                          )}
                          <button onClick={() => setModal({ open: true, editing: r })}
                            className="text-slate-500 hover:text-amber-400 transition-colors p-1" title="Edit">
                            <Pencil size={13} />
                          </button>
                          <button onClick={() => handleDelete(r)} disabled={del === r.id}
                            className="text-slate-500 hover:text-red-400 transition-colors p-1 disabled:opacity-40" title="Remove">
                            {del === r.id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
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
      </div>
    </div>
  );
}
