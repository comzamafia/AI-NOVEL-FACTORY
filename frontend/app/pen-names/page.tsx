'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import {
  UserPlus,
  Pencil,
  Trash2,
  X,
  Check,
  Loader2,
  BookOpen,
  DollarSign,
  RefreshCw,
  ArrowLeft,
  Fingerprint,
} from 'lucide-react';
import {
  getPenNames,
  createPenName,
  updatePenName,
  deletePenName,
  buildAvatarUrl,
} from '@/lib/api';
import type { PenNamePayload } from '@/lib/api';
import type { PenName } from '@/types';

const NICHE_OPTIONS = [
  'Thriller', 'Mystery', 'Suspense', 'Horror', 'Crime', 'Psychological Thriller',
  'Legal Thriller', 'Medical Thriller', 'Action & Adventure', 'Spy Thriller',
  'Fantasy', 'Science Fiction', 'Romance', 'Historical Fiction', 'Other',
];

const EMPTY_FORM: PenNamePayload = {
  name: '',
  niche_genre: '',
  bio: '',
  writing_style_prompt: '',
  website_url: '',
  amazon_author_url: '',
};

// ── Form modal ────────────────────────────────────────────────────
function PenNameModal({
  initial,
  onClose,
  onSaved,
}: {
  initial: (PenName & { id: number }) | null;
  onClose: () => void;
  onSaved: (pn: PenName) => void;
}) {
  const isEdit = !!initial;
  const [form, setForm] = useState<PenNamePayload>(
    initial
      ? {
          name:                 initial.name,
          niche_genre:          initial.niche_genre ?? '',
          bio:                  initial.bio ?? '',
          writing_style_prompt: initial.writing_style_prompt ?? '',
          website_url:          initial.website_url ?? '',
          amazon_author_url:    initial.amazon_author_url ?? '',
        }
      : { ...EMPTY_FORM }
  );
  const [busy, setBusy]   = useState(false);
  const [error, setError] = useState('');

  function setF(key: keyof PenNamePayload, val: string) {
    setForm(f => ({ ...f, [key]: val }));
    setError('');
  }

  async function save() {
    if (!form.name.trim()) { setError('Name is required'); return; }
    setBusy(true);
    try {
      const payload: PenNamePayload = {
        name:                 form.name.trim(),
        niche_genre:          form.niche_genre?.trim() || undefined,
        bio:                  form.bio?.trim()          || undefined,
        writing_style_prompt: form.writing_style_prompt?.trim() || undefined,
        website_url:          form.website_url?.trim()  || undefined,
        amazon_author_url:    form.amazon_author_url?.trim() || undefined,
      };
      const saved = isEdit
        ? await updatePenName(initial!.id, payload)
        : await createPenName(payload);
      onSaved(saved);
    } catch (e: unknown) {
      const err = e as { response?: { data?: Record<string, string[]> }; message?: string };
      if (err.response?.data) {
        const msgs = Object.entries(err.response.data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`).join('; ');
        setError(msgs);
      } else {
        setError(err.message ?? 'Save failed');
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Modal header */}
        <div className="flex items-center justify-between border-b border-slate-700 px-6 py-4">
          <h2 className="text-lg font-bold text-white">
            {isEdit ? `Edit ${initial!.name}` : 'New Pen Name'}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <div className="px-6 py-5 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
              Pen Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={e => setF('name', e.target.value)}
              placeholder="e.g. Morgan Blake"
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm placeholder-slate-600 focus:outline-none"
            />
          </div>

          {/* Niche Genre */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
              Niche / Genre
            </label>
            <select
              value={form.niche_genre}
              onChange={e => setF('niche_genre', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none"
            >
              <option value="">— Select niche —</option>
              {NICHE_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>

          {/* Bio */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
              Author Bio
            </label>
            <textarea
              rows={3}
              value={form.bio}
              onChange={e => setF('bio', e.target.value)}
              placeholder="A brief author bio shown on the storefront…"
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm placeholder-slate-600 resize-none focus:outline-none"
            />
          </div>

          {/* Writing Style Prompt */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
              AI Writing Style Prompt
            </label>
            <textarea
              rows={4}
              value={form.writing_style_prompt}
              onChange={e => setF('writing_style_prompt', e.target.value)}
              placeholder="Write in a dark, fast-paced style similar to Lee Child. Short punchy sentences. Strong verbs. Minimal adverbs…"
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm placeholder-slate-600 resize-none focus:outline-none"
            />
            <p className="text-xs text-slate-600 mt-1">Injected into every AI writing session for this pen name.</p>
          </div>

          {/* URLs */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">Website URL</label>
              <input
                type="url"
                value={form.website_url}
                onChange={e => setF('website_url', e.target.value)}
                placeholder="https://…"
                className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-3 py-2 text-white text-sm placeholder-slate-600 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">Amazon URL</label>
              <input
                type="url"
                value={form.amazon_author_url}
                onChange={e => setF('amazon_author_url', e.target.value)}
                placeholder="https://amazon.com/…"
                className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-lg px-3 py-2 text-white text-sm placeholder-slate-600 focus:outline-none"
              />
            </div>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-700 px-6 py-4 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={save}
            disabled={busy}
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-bold px-6 py-2 rounded-xl text-sm transition-colors"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
            {isEdit ? 'Save Changes' : 'Create Pen Name'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Confirm delete modal ──────────────────────────────────────────
function ConfirmDelete({
  penName,
  onClose,
  onDeleted,
}: {
  penName: PenName;
  onClose: () => void;
  onDeleted: (id: number) => void;
}) {
  const [busy, setBusy]   = useState(false);
  const [error, setError] = useState('');
  async function doDelete() {
    setBusy(true);
    try {
      await deletePenName(penName.id);
      onDeleted(penName.id);
    } catch (e: unknown) {
      const err = e as { message?: string };
      setError(err.message ?? 'Delete failed');
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-sm p-6 shadow-2xl text-center">
        <Trash2 size={36} className="mx-auto text-red-400 mb-3" />
        <h3 className="text-lg font-bold text-white mb-1">Delete Pen Name?</h3>
        <p className="text-slate-400 text-sm mb-5">
          <strong>{penName.name}</strong> and all its books will be soft-deleted. This action can be reversed from Django admin, but is not shown on the site.
        </p>
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <div className="flex gap-3 justify-center">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-700">Cancel</button>
          <button
            onClick={doDelete}
            disabled={busy}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-semibold px-5 py-2 rounded-lg text-sm"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function PenNamesPage() {
  const [penNames, setPenNames]         = useState<PenName[]>([]);
  const [loading, setLoading]           = useState(true);
  const [editTarget, setEditTarget]     = useState<PenName | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<PenName | null>(null);
  const [showCreate, setShowCreate]     = useState(false);
  const [toast, setToast]               = useState<string | null>(null);

  const showMsg = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPenNames({ page: 1 });
      setPenNames(res.results);
    } catch {
      showMsg('Failed to load pen names');
    } finally {
      setLoading(false);
    }
  }, [showMsg]);

  useEffect(() => { load(); }, [load]);

  function handleSaved(pn: PenName) {
    if (editTarget) {
      setPenNames(prev => prev.map(p => p.id === pn.id ? pn : p));
      showMsg(`${pn.name} updated`);
    } else {
      setPenNames(prev => [pn, ...prev]);
      showMsg(`${pn.name} created`);
    }
    setEditTarget(null);
    setShowCreate(false);
  }

  function handleDeleted(id: number) {
    setPenNames(prev => prev.filter(p => p.id !== id));
    setDeleteTarget(null);
    showMsg('Pen name deleted');
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium bg-emerald-600 text-white shadow-xl">
          {toast}
        </div>
      )}

      {/* Modals */}
      {(showCreate || editTarget) && (
        <PenNameModal
          initial={editTarget as (PenName & { id: number }) | null}
          onClose={() => { setEditTarget(null); setShowCreate(false); }}
          onSaved={handleSaved}
        />
      )}
      {deleteTarget && (
        <ConfirmDelete
          penName={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDeleted={handleDeleted}
        />
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </Link>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Admin</p>
              <h1 className="text-xl font-bold text-white">Pen Name Management</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={load}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Refresh"
            >
              <RefreshCw size={16} />
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-4 py-2 rounded-xl text-sm transition-colors"
            >
              <UserPlus size={16} />
              New Pen Name
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-500">
            <Loader2 size={32} className="animate-spin" />
          </div>
        ) : penNames.length === 0 ? (
          <div className="text-center py-20 text-slate-600">
            <UserPlus size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-lg mb-6">No pen names yet.</p>
            <button
              onClick={() => setShowCreate(true)}
              className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-6 py-3 rounded-xl transition-colors"
            >
              Create Your First Pen Name
            </button>
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {penNames.map(pn => (
              <div
                key={pn.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700 transition-colors"
              >
                {/* Top section */}
                <div className="p-5 flex items-start gap-4">
                  {/* Avatar */}
                  <Image
                    src={buildAvatarUrl(pn)}
                    alt={pn.name}
                    width={56}
                    height={56}
                    className="w-14 h-14 rounded-full object-cover shrink-0 ring-2 ring-slate-700"
                    unoptimized
                  />
                  <div className="min-w-0 flex-1">
                    <h3 className="font-bold text-white text-base truncate">{pn.name}</h3>
                    {pn.niche_genre && (
                      <p className="text-xs text-amber-400 mt-0.5">{pn.niche_genre}</p>
                    )}
                    {pn.bio && (
                      <p className="text-xs text-slate-500 mt-1.5 line-clamp-2">{pn.bio}</p>
                    )}
                  </div>
                </div>

                {/* Stats bar */}
                <div className="border-t border-slate-800 px-5 py-3 flex items-center gap-4 text-sm text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <BookOpen size={13} className="text-slate-600" />
                    {pn.book_count ?? 0} books
                  </span>
                  <span className="flex items-center gap-1.5">
                    <BookOpen size={13} className="text-slate-600" />
                    {pn.total_books_published ?? 0} published
                  </span>
                  <span className="flex items-center gap-1.5 ml-auto">
                    <DollarSign size={13} className="text-emerald-600" />
                    {Number(pn.total_revenue_usd ?? 0).toFixed(2)}
                  </span>
                </div>

                {/* Links */}
                <div className="border-t border-slate-800 px-5 py-3 flex items-center gap-2 text-xs">
                  {pn.website_url && (
                    <a href={pn.website_url} target="_blank" rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 truncate">
                      Website ↗
                    </a>
                  )}
                  {pn.amazon_author_url && (
                    <a href={pn.amazon_author_url} target="_blank" rel="noopener noreferrer"
                      className="text-orange-400 hover:text-orange-300 ml-auto">
                      Amazon ↗
                    </a>
                  )}
                </div>

                {/* Style prompt preview */}
                {pn.writing_style_prompt && (
                  <div className="border-t border-slate-800 px-5 py-3">
                    <p className="text-xs text-slate-600 uppercase tracking-wider mb-1">AI Style</p>
                    <p className="text-xs text-slate-500 line-clamp-2 italic">{pn.writing_style_prompt}</p>
                  </div>
                )}

                {/* Actions */}
                <div className="border-t border-slate-800 px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Link
                      href={`/authors/${pn.id}`}
                      className="text-xs text-slate-400 hover:text-amber-400 transition-colors"
                    >
                      View storefront →
                    </Link>
                    <Link
                      href={`/pen-names/${pn.id}/style`}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-purple-400 transition-colors"
                    >
                      <Fingerprint size={11} /> Style
                    </Link>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setEditTarget(pn)}
                      className="flex items-center gap-1 text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1.5 rounded-lg transition-colors"
                    >
                      <Pencil size={12} /> Edit
                    </button>
                    <button
                      onClick={() => setDeleteTarget(pn)}
                      className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-300 bg-slate-800 hover:bg-red-900/50 px-2.5 py-1.5 rounded-lg transition-colors"
                    >
                      <Trash2 size={12} /> Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
