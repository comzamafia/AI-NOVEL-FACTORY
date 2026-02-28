'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  FileText, ArrowLeft, RefreshCw, Loader2, Save,
  CheckCircle, AlertCircle, Star, ToggleLeft, ToggleRight,
  Clipboard,
} from 'lucide-react';
import {
  getBook,
  getBookDescriptionsFull,
  updateBookDescriptionFull,
  setActiveDescription,
  approveDescription,
} from '@/lib/api';
import type { Book, BookDescriptionFull } from '@/types';

// ── Character counter bar ─────────────────────────────────────
function CharBar({ count, max = 4000 }: { count: number; max?: number }) {
  const pct = Math.min((count / max) * 100, 100);
  const color = pct > 90 ? 'bg-red-500' : pct > 75 ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-mono ${pct > 90 ? 'text-red-400' : pct > 75 ? 'text-amber-400' : 'text-slate-500'}`}>
        {count}/{max}
      </span>
    </div>
  );
}

// ── HTML Preview ──────────────────────────────────────────────
function HtmlPreview({ html }: { html: string }) {
  return (
    <div
      className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed [&_b]:text-white [&_em]:text-amber-300 [&_ul]:pl-4 [&_li]:text-slate-300"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// ── Version Card ──────────────────────────────────────────────
function VersionCard({
  desc,
  onSave,
  onSetActive,
  onApprove,
}: {
  desc: BookDescriptionFull;
  onSave: (id: number, payload: Partial<BookDescriptionFull>) => Promise<void>;
  onSetActive: (id: number) => void;
  onApprove: (id: number) => void;
}) {
  const isA = desc.version === 'A';
  const [form, setForm] = useState({
    hook_line: desc.hook_line,
    setup_paragraph: desc.setup_paragraph,
    stakes_paragraph: desc.stakes_paragraph,
    twist_tease: desc.twist_tease,
    call_to_action: desc.call_to_action,
    description_html: desc.description_html,
    comparable_authors: desc.comparable_authors.join(', '),
  });
  const [mode, setMode] = useState<'formula' | 'html' | 'preview'>('formula');
  const [saving, setSaving] = useState(false);
  const [activating, setActivating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleSave() {
    setSaving(true);
    await onSave(desc.id, {
      hook_line: form.hook_line,
      setup_paragraph: form.setup_paragraph,
      stakes_paragraph: form.stakes_paragraph,
      twist_tease: form.twist_tease,
      call_to_action: form.call_to_action,
      description_html: form.description_html,
      comparable_authors: form.comparable_authors.split(',').map(s => s.trim()).filter(Boolean),
    });
    setSaving(false);
  }

  function copyHtml() {
    navigator.clipboard.writeText(desc.description_html).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const accentColor = isA ? 'border-amber-500/40 bg-amber-500/5' : 'border-blue-500/40 bg-blue-500/5';
  const badgeColor  = isA ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-blue-500/20 text-blue-400 border-blue-500/30';

  return (
    <div className={`border rounded-2xl p-6 ${accentColor} flex flex-col gap-4`}>
      {/* Card Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold px-3 py-1 rounded-full border ${badgeColor}`}>
            Version {desc.version}
          </span>
          {desc.is_active && (
            <span className="text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 px-2.5 py-1 rounded-full flex items-center gap-1">
              <CheckCircle size={10} /> Active
            </span>
          )}
          {desc.is_approved && (
            <span className="text-xs bg-purple-500/15 text-purple-400 border border-purple-500/25 px-2.5 py-1 rounded-full flex items-center gap-1">
              <Star size={10} className="fill-purple-400" /> Approved
            </span>
          )}
          <CharBar count={desc.character_count} />
        </div>
        <div className="flex items-center gap-2">
          <button onClick={copyHtml} title="Copy HTML"
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-white border border-slate-700 px-2.5 py-1.5 rounded-lg transition-colors">
            {copied ? <CheckCircle size={11} /> : <Clipboard size={11} />}
            {copied ? 'Copied!' : 'Copy HTML'}
          </button>

          {!desc.is_active && (
            <button
              onClick={() => { setActivating(true); onSetActive(desc.id); setTimeout(() => setActivating(false), 600); }}
              disabled={activating}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-2.5 py-1.5 rounded-lg transition-colors disabled:opacity-50">
              {activating ? <Loader2 size={11} className="animate-spin" /> : <ToggleLeft size={11} />}
              Set Active
            </button>
          )}

          {!desc.is_approved && (
            <button
              onClick={() => { setApproving(true); onApprove(desc.id); setTimeout(() => setApproving(false), 600); }}
              disabled={approving}
              className="flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 border border-purple-500/30 hover:border-purple-500/60 px-2.5 py-1.5 rounded-lg transition-colors disabled:opacity-50">
              {approving ? <Loader2 size={11} className="animate-spin" /> : <Star size={11} />}
              Approve
            </button>
          )}

          <button onClick={handleSave} disabled={saving}
            className="flex items-center gap-1.5 text-xs bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50">
            {saving ? <Loader2 size={11} className="animate-spin" /> : <Save size={11} />}
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-slate-900/50 p-1 rounded-xl w-fit">
        {(['formula', 'html', 'preview'] as const).map(t => (
          <button key={t} onClick={() => setMode(t)}
            className={`text-xs px-3 py-1.5 rounded-lg capitalize transition-colors ${
              mode === t ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-white'}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Formula Mode */}
      {mode === 'formula' && (
        <div className="space-y-3">
          {([
            { key: 'hook_line',        label: 'Hook Line',          ph: 'Opening hook — question or exciting statement' },
            { key: 'setup_paragraph',  label: 'Setup',              ph: 'Who is the protagonist, what do they face' },
            { key: 'stakes_paragraph', label: 'Stakes',             ph: 'What happens if they fail' },
            { key: 'twist_tease',      label: 'Twist Tease',        ph: '"But nothing is what it seems…"' },
            { key: 'call_to_action',   label: 'Call to Action',     ph: '"Perfect for fans of X and Y. Grab your copy today."' },
            { key: 'comparable_authors', label: 'Comparable Authors (comma-separated)', ph: 'Author A, Author B' },
          ] as { key: keyof typeof form; label: string; ph: string }[]).map(({ key, label, ph }) => (
            <div key={key}>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1.5">{label}</label>
              {key === 'comparable_authors' ? (
                <input type="text" value={form[key]} placeholder={ph}
                  onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
                  className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none" />
              ) : (
                <textarea rows={2} value={form[key]} placeholder={ph}
                  onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
                  className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none resize-none" />
              )}
            </div>
          ))}
        </div>
      )}

      {/* HTML Mode */}
      {mode === 'html' && (
        <div>
          <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1.5">
            Amazon HTML — allowed: &lt;b&gt; &lt;em&gt; &lt;br&gt; &lt;ul&gt; &lt;li&gt;
          </label>
          <textarea
            rows={14}
            value={form.description_html}
            onChange={e => setForm(p => ({ ...p, description_html: e.target.value }))}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none resize-y font-mono leading-relaxed"
          />
          <CharBar count={form.description_html.length} />
        </div>
      )}

      {/* Preview Mode */}
      {mode === 'preview' && (
        <div className="bg-slate-900 rounded-xl p-5 min-h-[200px]">
          {desc.description_html
            ? <HtmlPreview html={desc.description_html} />
            : <p className="text-slate-600 text-sm">No HTML content yet. Switch to HTML mode to add a description.</p>
          }
        </div>
      )}

      {/* Approval info */}
      {desc.approved_at && (
        <p className="text-xs text-slate-600">Approved {new Date(desc.approved_at).toLocaleDateString()}</p>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function DescriptionsPage() {
  const { id } = useParams<{ id: string }>();

  const [book,   setBook]   = useState<Book | null>(null);
  const [descs,  setDescs]  = useState<BookDescriptionFull[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast,   setToast]  = useState<{ msg: string; ok: boolean } | null>(null);

  function showToast(msg: string, ok = true) {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, d] = await Promise.all([getBook(id), getBookDescriptionsFull(id)]);
      setBook(b);
      setDescs(d);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  async function handleSave(descId: number, payload: Partial<BookDescriptionFull>) {
    try {
      const updated = await updateBookDescriptionFull(descId, payload);
      setDescs(p => p.map(d => d.id === updated.id ? updated : d));
      showToast('Version saved');
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Failed to save', false);
    }
  }

  async function handleSetActive(descId: number) {
    try {
      const updated = await setActiveDescription(descId);
      setDescs(p => p.map(d => ({
        ...d,
        is_active: d.id === updated.id,
      })) as typeof p);
      showToast(`Version ${updated.version} is now active`);
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Failed', false);
    }
  }

  async function handleApprove(descId: number) {
    try {
      const updated = await approveDescription(descId);
      setDescs(p => p.map(d => d.id === updated.id ? updated : d));
      showToast(`Version ${updated.version} approved`);
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Failed', false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl text-sm font-medium ${toast.ok ? 'bg-emerald-600' : 'bg-red-600'}`}>
          {toast.ok ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href={`/books/${id}`} className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </Link>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">A/B Descriptions</p>
              <h1 className="text-lg font-bold truncate max-w-[300px]">{book?.title ?? 'Loading…'}</h1>
            </div>
          </div>
          <button onClick={load} disabled={loading}
            className="text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 p-2 rounded-lg transition-colors disabled:opacity-40">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-500">
            <Loader2 size={36} className="animate-spin" />
          </div>
        ) : descs.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <FileText size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400">No description versions found.</p>
            <p className="text-sm mt-2 text-slate-600">Use the AI writer task to generate A/B descriptions for this book.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Legend */}
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5"><CheckCircle size={12} className="text-emerald-400" />Active = shown on storefront</span>
              <span className="flex items-center gap-1.5"><Star size={12} className="text-purple-400 fill-purple-400" />Approved = locked for KDP export</span>
              <span className="flex items-center gap-1.5"><ToggleRight size={12} className="text-amber-400" />4000 char limit for Amazon</span>
            </div>

            {/* Side by side on large screens, stacked on small */}
            <div className={`grid gap-6 ${descs.length > 1 ? 'lg:grid-cols-2' : ''}`}>
              {descs.map(desc => (
                <VersionCard
                  key={desc.id}
                  desc={desc}
                  onSave={handleSave}
                  onSetActive={handleSetActive}
                  onApprove={handleApprove}
                />
              ))}
            </div>

            {/* Compare active description plain text */}
            {descs.some(d => d.is_active) && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <FileText size={14} className="text-amber-400" />
                  Active Plain Text Preview (for copywriting reference)
                </h2>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {descs.find(d => d.is_active)?.description_plain ?? '—'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
