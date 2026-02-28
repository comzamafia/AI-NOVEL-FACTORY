'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Globe, ArrowLeft, RefreshCw, Loader2, Plus, Pencil,
  Trash2, ExternalLink, DollarSign, BookOpen,
  X, Save, CheckCircle, AlertCircle,
} from 'lucide-react';
import {
  getBook,
  getDistributionChannels,
  createDistributionChannel,
  updateDistributionChannel,
  deleteDistributionChannel,
  getPlatformChoices,
} from '@/lib/api';
import type { Book, DistributionChannel, DistributionPlatform } from '@/types';

// ── Platform icon map ─────────────────────────────────────────────
const PLATFORM_COLORS: Record<string, string> = {
  kdp:            'bg-amber-500/20 text-amber-400 border-amber-500/30',
  draft2digital:  'bg-blue-500/20 text-blue-400 border-blue-500/30',
  acx:            'bg-purple-500/20 text-purple-400 border-purple-500/30',
  publishdrive:   'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  website:        'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  patreon:        'bg-orange-500/20 text-orange-400 border-orange-500/30',
  apple_books:    'bg-pink-500/20 text-pink-400 border-pink-500/30',
  kobo:           'bg-red-500/20 text-red-400 border-red-500/30',
  barnes_noble:   'bg-green-500/20 text-green-400 border-green-500/30',
};

function PlatformBadge({ platform, label }: { platform: string; label: string }) {
  const cls = PLATFORM_COLORS[platform] ?? 'bg-slate-700 text-slate-400 border-slate-600';
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${cls}`}>
      {label}
    </span>
  );
}

// ── Revenue bar ───────────────────────────────────────────────────
function RevenueBar({ channel, max }: { channel: DistributionChannel; max: number }) {
  const rev = parseFloat(String(channel.revenue_usd));
  const pct  = max > 0 ? (rev / max) * 100 : 0;
  const cls  = PLATFORM_COLORS[channel.platform]?.split(' ')[1] ?? 'text-slate-400';

  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-xs text-slate-400 w-28 shrink-0 truncate">{channel.platform_display}</span>
      <div className="flex-1 bg-slate-800 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            PLATFORM_COLORS[channel.platform]?.replace('text-', 'bg-').replace('/20', '').replace('border-', '') ?? 'bg-slate-600'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-sm font-mono shrink-0 w-20 text-right ${cls}`}>
        ${rev.toFixed(2)}
      </span>
    </div>
  );
}

// ── Add / Edit Modal ──────────────────────────────────────────────
interface ChannelForm {
  platform: string;
  asin_or_id: string;
  published_url: string;
  units_sold: string;
  pages_read: string;
  revenue_usd: string;
  royalty_rate: string;
  is_active: boolean;
  published_at: string;
}

const EMPTY_FORM: ChannelForm = {
  platform:     '',
  asin_or_id:   '',
  published_url:'',
  units_sold:   '0',
  pages_read:   '0',
  revenue_usd:  '0',
  royalty_rate: '0.70',
  is_active:    true,
  published_at: '',
};

function ChannelModal({
  bookId,
  initial,
  choices,
  onClose,
  onSaved,
}: {
  bookId: string;
  initial: DistributionChannel | null;
  choices: { value: string; label: string }[];
  onClose: () => void;
  onSaved: (c: DistributionChannel) => void;
}) {
  const isEdit = !!initial;
  const [form, setForm] = useState<ChannelForm>(
    initial
      ? {
          platform:     initial.platform,
          asin_or_id:   initial.asin_or_id,
          published_url:initial.published_url,
          units_sold:   String(initial.units_sold),
          pages_read:   String(initial.pages_read),
          revenue_usd:  String(parseFloat(String(initial.revenue_usd)).toFixed(2)),
          royalty_rate: String(initial.royalty_rate),
          is_active:    initial.is_active,
          published_at: initial.published_at ? initial.published_at.slice(0, 10) : '',
        }
      : { ...EMPTY_FORM, platform: choices[0]?.value ?? '' }
  );
  const [busy, setBusy] = useState(false);
  const [err,  setErr]  = useState('');

  async function submit() {
    if (!form.platform) { setErr('Select a platform'); return; }
    setBusy(true);
    try {
      const payload = {
        book:          Number(bookId),
        platform:      form.platform as DistributionPlatform,
        asin_or_id:    form.asin_or_id.trim(),
        published_url: form.published_url.trim(),
        units_sold:    parseInt(form.units_sold) || 0,
        pages_read:    parseInt(form.pages_read)  || 0,
        revenue_usd:   parseFloat(form.revenue_usd) || 0,
        royalty_rate:  parseFloat(form.royalty_rate) || 0.70,
        is_active:     form.is_active,
        published_at:  form.published_at || null,
      };

      const saved = isEdit
        ? await updateDistributionChannel(initial!.id, payload)
        : await createDistributionChannel(payload);

      onSaved(saved);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to save channel');
    } finally {
      setBusy(false);
    }
  }

  function f(key: keyof ChannelForm) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value }));
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 overflow-y-auto">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl my-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Globe size={18} className="text-amber-400" />
            {isEdit ? 'Edit Channel' : 'Add Distribution Channel'}
          </h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          {/* Platform */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Platform</label>
            <select
              value={form.platform}
              onChange={f('platform')}
              disabled={isEdit}
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none disabled:opacity-50"
            >
              {choices.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>

          {/* ASIN / ID */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">ASIN / Platform ID</label>
            <input
              type="text"
              value={form.asin_or_id}
              onChange={f('asin_or_id')}
              placeholder="e.g. B0XXXXX or ISBN"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono"
            />
          </div>

          {/* URL */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Published URL</label>
            <input
              type="url"
              value={form.published_url}
              onChange={f('published_url')}
              placeholder="https://…"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none"
            />
          </div>

          {/* Units / Pages / Revenue  */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Units Sold</label>
              <input
                type="number" min="0"
                value={form.units_sold}
                onChange={f('units_sold')}
                className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Pages Read</label>
              <input
                type="number" min="0"
                value={form.pages_read}
                onChange={f('pages_read')}
                className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Revenue (USD)</label>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm">$</span>
                <input
                  type="number" min="0" step="0.01"
                  value={form.revenue_usd}
                  onChange={f('revenue_usd')}
                  className="w-full pl-6 pr-3 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono"
                />
              </div>
            </div>
          </div>

          {/* Royalty rate and published date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Royalty Rate</label>
              <select
                value={form.royalty_rate}
                onChange={f('royalty_rate')}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none"
              >
                <option value="0.35">35%</option>
                <option value="0.60">60%</option>
                <option value="0.70">70%</option>
                <option value="0.80">80%</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Published Date</label>
              <input
                type="date"
                value={form.published_at}
                onChange={f('published_at')}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none"
              />
            </div>
          </div>

          {/* Active toggle */}
          <div className="flex items-center gap-3 py-2">
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={e => setForm(prev => ({ ...prev, is_active: e.target.checked }))}
              className="w-4 h-4 rounded accent-amber-500"
            />
            <label htmlFor="is_active" className="text-sm text-slate-300 cursor-pointer">Channel is active</label>
          </div>

          {err && <p className="text-red-400 text-xs">{err}</p>}

          <div className="flex gap-3 pt-2">
            <button
              onClick={submit}
              disabled={busy}
              className="flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold py-2.5 rounded-xl transition-colors disabled:opacity-50"
            >
              {busy ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              {busy ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Channel'}
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

// ── Main Page ─────────────────────────────────────────────────────
export default function DistributionPage() {
  const { id } = useParams<{ id: string }>();
  const bookId = id;

  const [book,     setBook]     = useState<Book | null>(null);
  const [channels, setChannels] = useState<DistributionChannel[]>([]);
  const [choices,  setChoices]  = useState<{ value: string; label: string }[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [modal,    setModal]    = useState<{ open: boolean; editing: DistributionChannel | null }>({ open: false, editing: null });
  const [deleting, setDeleting] = useState<number | null>(null);
  const [toast,    setToast]    = useState<{ msg: string; ok: boolean } | null>(null);

  function showToast(msg: string, ok = true) {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, ch, c] = await Promise.all([
        getBook(bookId),
        getDistributionChannels(bookId),
        getPlatformChoices(),
      ]);
      setBook(b);
      setChannels(ch);
      setChoices(c);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => { load(); }, [load]);

  async function handleDelete(ch: DistributionChannel) {
    if (!confirm(`Remove ${ch.platform_display} channel?`)) return;
    setDeleting(ch.id);
    try {
      await deleteDistributionChannel(ch.id);
      setChannels(prev => prev.filter(c => c.id !== ch.id));
      showToast('Channel removed');
    } catch {
      showToast('Failed to remove channel', false);
    } finally {
      setDeleting(null);
    }
  }

  function handleSaved(saved: DistributionChannel) {
    setChannels(prev => {
      const idx = prev.findIndex(c => c.id === saved.id);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = saved;
        return next;
      }
      return [...prev, saved];
    });
    setModal({ open: false, editing: null });
    showToast(modal.editing ? 'Channel updated' : 'Channel added');
  }

  // Aggregates
  const totalRevenue  = channels.reduce((s, c) => s + parseFloat(String(c.revenue_usd)), 0);
  const totalUnits    = channels.reduce((s, c) => s + c.units_sold, 0);
  const totalPages    = channels.reduce((s, c) => s + c.pages_read, 0);
  const maxRevenue    = Math.max(...channels.map(c => parseFloat(String(c.revenue_usd))), 1);
  const activeCount   = channels.filter(c => c.is_active).length;

  // Used platform values for de-dup in add modal
  const usedPlatforms = new Set(channels.map(c => c.platform));
  const availableChoices = choices.filter(c => !usedPlatforms.has(c.value as DistributionPlatform));

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl text-sm font-medium ${
          toast.ok ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'
        }`}>
          {toast.ok ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {toast.msg}
        </div>
      )}

      {/* Modal */}
      {modal.open && (
        <ChannelModal
          bookId={bookId}
          initial={modal.editing}
          choices={modal.editing ? choices : availableChoices}
          onClose={() => setModal({ open: false, editing: null })}
          onSaved={handleSaved}
        />
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link href={`/books/${bookId}`} className="text-slate-400 hover:text-white transition-colors shrink-0">
              <ArrowLeft size={20} />
            </Link>
            <div className="min-w-0">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Distribution</p>
              <h1 className="text-lg font-bold text-white truncate">{book?.title ?? 'Loading…'}</h1>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {availableChoices.length > 0 && (
              <button
                onClick={() => setModal({ open: true, editing: null })}
                className="flex items-center gap-2 text-sm bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2 rounded-xl transition-colors"
              >
                <Plus size={14} />
                Add Channel
              </button>
            )}
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

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-500">
            <Loader2 size={40} className="animate-spin" />
          </div>
        ) : channels.length === 0 ? (
          <div className="text-center py-24 text-slate-500">
            <Globe size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400">No distribution channels yet.</p>
            <p className="text-sm mt-2">Add a channel to track revenue across platforms.</p>
            {availableChoices.length > 0 && (
              <button
                onClick={() => setModal({ open: true, editing: null })}
                className="mt-6 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-6 py-3 rounded-xl transition-colors mx-auto"
              >
                <Plus size={16} />
                Add First Channel
              </button>
            )}
          </div>
        ) : (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <div className="mb-3 text-emerald-400"><DollarSign size={20} /></div>
                <p className="text-2xl font-bold text-white">${totalRevenue.toFixed(2)}</p>
                <p className="text-sm text-slate-400 mt-0.5">Total Revenue</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <div className="mb-3 text-blue-400"><BookOpen size={20} /></div>
                <p className="text-2xl font-bold text-white">{totalUnits.toLocaleString()}</p>
                <p className="text-sm text-slate-400 mt-0.5">Units Sold</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <div className="mb-3 text-purple-400"><Globe size={20} /></div>
                <p className="text-2xl font-bold text-white">{activeCount}</p>
                <p className="text-sm text-slate-400 mt-0.5">Active Platforms</p>
                <p className="text-xs text-slate-600 mt-1">{channels.length} total</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <div className="mb-3 text-amber-400"><BookOpen size={20} /></div>
                <p className="text-2xl font-bold text-white">{totalPages.toLocaleString()}</p>
                <p className="text-sm text-slate-400 mt-0.5">Pages Read (KU)</p>
              </div>
            </div>

            {/* Revenue bar chart */}
            {channels.length > 1 && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5 flex items-center gap-2">
                  <DollarSign size={14} className="text-amber-400" />
                  Revenue by Platform
                </h2>
                <div className="space-y-2">
                  {[...channels]
                    .sort((a, b) => parseFloat(String(b.revenue_usd)) - parseFloat(String(a.revenue_usd)))
                    .map(ch => (
                      <RevenueBar key={ch.id} channel={ch} max={maxRevenue} />
                    ))}
                </div>
              </div>
            )}

            {/* Channel cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {channels.map(ch => {
                const rev = parseFloat(String(ch.revenue_usd));
                const isPct = totalRevenue > 0 ? ((rev / totalRevenue) * 100).toFixed(1) : '0';

                return (
                  <div
                    key={ch.id}
                    className={`bg-slate-900 border rounded-2xl p-5 flex flex-col gap-4 transition-all ${
                      ch.is_active ? 'border-slate-800' : 'border-slate-800 opacity-60'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <PlatformBadge platform={ch.platform} label={ch.platform_display} />
                      <div className="flex items-center gap-1.5">
                        {!ch.is_active && (
                          <span className="text-xs text-slate-600 font-medium">Inactive</span>
                        )}
                        <button
                          onClick={() => setModal({ open: true, editing: ch })}
                          className="text-slate-500 hover:text-amber-400 transition-colors p-1"
                          title="Edit"
                        >
                          <Pencil size={13} />
                        </button>
                        <button
                          onClick={() => handleDelete(ch)}
                          disabled={deleting === ch.id}
                          className="text-slate-500 hover:text-red-400 transition-colors p-1 disabled:opacity-40"
                          title="Remove"
                        >
                          {deleting === ch.id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                        </button>
                      </div>
                    </div>

                    {/* Revenue */}
                    <div>
                      <p className="text-2xl font-bold text-white">${rev.toFixed(2)}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{isPct}% of total revenue</p>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-slate-800 rounded-lg p-2.5">
                        <p className="text-slate-500">Units Sold</p>
                        <p className="text-white font-mono mt-0.5">{ch.units_sold.toLocaleString()}</p>
                      </div>
                      <div className="bg-slate-800 rounded-lg p-2.5">
                        <p className="text-slate-500">Pages Read</p>
                        <p className="text-white font-mono mt-0.5">{ch.pages_read.toLocaleString()}</p>
                      </div>
                      <div className="bg-slate-800 rounded-lg p-2.5">
                        <p className="text-slate-500">Royalty Rate</p>
                        <p className="text-amber-400 font-mono mt-0.5">{(ch.royalty_rate * 100).toFixed(0)}%</p>
                      </div>
                      <div className="bg-slate-800 rounded-lg p-2.5">
                        <p className="text-slate-500">Royalty Earned</p>
                        <p className="text-emerald-400 font-mono mt-0.5">
                          ${(rev * ch.royalty_rate).toFixed(2)}
                        </p>
                      </div>
                    </div>

                    {/* ASIN and link */}
                    {(ch.asin_or_id || ch.published_url) && (
                      <div className="pt-1 border-t border-slate-800 flex items-center justify-between gap-2">
                        {ch.asin_or_id && (
                          <span className="text-xs text-slate-500 font-mono truncate">{ch.asin_or_id}</span>
                        )}
                        {ch.published_url && (
                          <a
                            href={ch.published_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-500 hover:text-amber-400 transition-colors shrink-0"
                            title="View on platform"
                          >
                            <ExternalLink size={13} />
                          </a>
                        )}
                      </div>
                    )}

                    {/* Published date */}
                    {ch.published_at && (
                      <p className="text-xs text-slate-600">
                        Published: {new Date(ch.published_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
