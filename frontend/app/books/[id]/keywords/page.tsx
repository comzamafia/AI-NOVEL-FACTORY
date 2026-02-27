'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, Search, CheckCircle2, RefreshCw, AlertTriangle,
  Copy, Check, Loader2, Tag, ShoppingCart, BookOpen, Layers,
} from 'lucide-react';
import {
  getBook,
  getKeywordResearch,
  updateKeywordResearch,
  approveKeywordResearch,
  rerunKeywordResearch,
  validateKeywords,
} from '@/lib/api';
import type { Book, KeywordResearch, KeywordPrimary, CompetitorAsin } from '@/types';

// ── Clipboard helper ──────────────────────────────────────────────
function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }
  return (
    <button onClick={copy} className="ml-2 text-slate-500 hover:text-amber-400 transition-colors" title="Copy">
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

// ── Keyword tag ───────────────────────────────────────────────────
function KwTag({ kw, onRemove }: { kw: KeywordPrimary; onRemove: () => void }) {
  const vol = kw.volume ? `${(kw.volume / 1000).toFixed(0)}K` : null;
  return (
    <span className="inline-flex items-center gap-1.5 bg-slate-800 border border-slate-700 rounded-full px-3 py-1 text-sm text-slate-300 group">
      {kw.keyword}
      {vol && <span className="text-xs text-slate-500">·{vol}</span>}
      <button onClick={onRemove} className="text-slate-600 hover:text-red-400 transition-colors ml-1">&times;</button>
    </span>
  );
}

export default function KeywordsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [book, setBook]       = useState<Book | null>(null);
  const [kw, setKw]           = useState<KeywordResearch | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [validating, setValidating] = useState(false);
  const [running, setRunning] = useState(false);
  const [validErrors, setValidErrors] = useState<string[]>([]);
  const [toast, setToast]     = useState<{ msg: string; type: 'ok' | 'err' } | null>(null);

  // Draft state
  const [backendKws, setBackendKws] = useState<string[]>(Array(7).fill(''));
  const [cat1, setCat1]   = useState('');
  const [cat2, setCat2]   = useState('');
  const [primaryKws, setPrimaryKws] = useState<KeywordPrimary[]>([]);
  const [newKwInput, setNewKwInput] = useState('');

  const showToast = useCallback((msg: string, type: 'ok' | 'err' = 'ok') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [bk, kwData] = await Promise.all([getBook(id), getKeywordResearch(id)]);
      setBook(bk);
      if (kwData) {
        setKw(kwData);
        const bkws = kwData.kdp_backend_keywords || [];
        setBackendKws([...bkws, ...Array(7).fill('')].slice(0, 7));
        setCat1(kwData.kdp_category_1 || '');
        setCat2(kwData.kdp_category_2 || '');
        setPrimaryKws(kwData.primary_keywords || []);
      }
    } catch { showToast('Failed to load', 'err'); }
    finally { setLoading(false); }
  }, [id, showToast]);

  useEffect(() => { load(); }, [load]);

  async function save() {
    if (!kw) return;
    setSaving(true);
    try {
      const updated = await updateKeywordResearch(kw.id, {
        kdp_backend_keywords: backendKws.filter(k => k.trim()),
        kdp_category_1: cat1,
        kdp_category_2: cat2,
        primary_keywords: primaryKws,
      });
      setKw(updated);
      showToast('Saved');
    } catch { showToast('Save failed', 'err'); }
    finally { setSaving(false); }
  }

  async function handleApprove() {
    if (!kw) return;
    setSaving(true);
    try {
      await approveKeywordResearch(kw.id);
      setKw(prev => prev ? { ...prev, is_approved: true } : prev);
      showToast('Keywords approved ✓');
    } catch { showToast('Approve failed', 'err'); }
    finally { setSaving(false); }
  }

  async function handleRerun() {
    if (!kw) return;
    setRunning(true);
    try {
      await rerunKeywordResearch(kw.id);
      showToast('Research task queued — refresh in a minute');
    } catch { showToast('Failed to queue', 'err'); }
    finally { setRunning(false); }
  }

  async function handleValidate() {
    if (!kw) return;
    setValidating(true);
    setValidErrors([]);
    try {
      const result = await validateKeywords(kw.id);
      setValidErrors(result.errors);
      if (result.valid) showToast(`All ${result.keyword_count} keywords valid ✓`);
      else showToast(`${result.errors.length} validation issue(s)`, 'err');
    } catch { showToast('Validate failed', 'err'); }
    finally { setValidating(false); }
  }

  function addPrimaryKw() {
    const kw = newKwInput.trim();
    if (!kw) return;
    setPrimaryKws(prev => [...prev, { keyword: kw }]);
    setNewKwInput('');
  }

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">
      <Loader2 size={40} className="animate-spin" />
    </div>
  );

  const competitors: CompetitorAsin[] = kw?.competitor_asins || [];

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-xl
          ${toast.type === 'ok' ? 'bg-emerald-600' : 'bg-red-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <button onClick={() => router.back()} className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </button>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Keyword Research</p>
              <h1 className="text-xl font-bold text-white truncate max-w-xs sm:max-w-md">
                {book?.title ?? '…'}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Status badge */}
            {kw && (
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                kw.is_approved ? 'bg-emerald-900/50 text-emerald-300' : 'bg-yellow-900/50 text-yellow-300'
              }`}>
                {kw.is_approved ? 'Approved ✓' : 'Pending Review'}
              </span>
            )}
            <button
              onClick={handleValidate}
              disabled={!kw || validating}
              className="flex items-center gap-2 text-sm border border-slate-700 hover:border-slate-500 text-slate-400 hover:text-white px-3 py-2 rounded-lg transition-colors disabled:opacity-40"
            >
              {validating ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
              Validate
            </button>
            <button
              onClick={handleRerun}
              disabled={!kw || running}
              className="flex items-center gap-2 text-sm border border-slate-700 hover:border-slate-500 text-slate-400 hover:text-white px-3 py-2 rounded-lg transition-colors disabled:opacity-40"
            >
              {running ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Re-run Research
            </button>
            <button
              onClick={save}
              disabled={!kw || saving}
              className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : null}
              Save
            </button>
            <button
              onClick={handleApprove}
              disabled={!kw || saving || kw?.is_approved}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold px-4 py-2 rounded-lg text-sm transition-colors"
            >
              <CheckCircle2 size={14} />
              Approve
            </button>
          </div>
        </div>
      </div>

      {!kw ? (
        <div className="max-w-6xl mx-auto px-4 py-20 text-center text-slate-600">
          <Search size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg mb-2">No keyword research yet.</p>
          <p className="text-sm text-slate-700">Start keyword research from the Workflow panel.</p>
          <Link href={`/books/${id}/workflow`} className="inline-block mt-4 text-amber-400 hover:text-amber-300 text-sm underline">
            Go to Workflow →
          </Link>
        </div>
      ) : (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

          {/* Validation errors */}
          {validErrors.length > 0 && (
            <div className="bg-red-900/20 border border-red-700/50 rounded-xl p-4 space-y-1">
              <p className="text-red-300 font-medium text-sm flex items-center gap-2">
                <AlertTriangle size={14} /> {validErrors.length} validation issue(s)
              </p>
              {validErrors.map((e, i) => <p key={i} className="text-red-400/80 text-xs ml-5">{e}</p>)}
            </div>
          )}

          {/* ── Section: Suggested Metadata ── */}
          {(kw.suggested_title || kw.suggested_subtitle) && (
            <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <BookOpen size={14} /> AI-Suggested Metadata
              </h2>
              {kw.suggested_title && (
                <div className="mb-3">
                  <p className="text-xs text-slate-600 mb-1">Title</p>
                  <p className="text-white font-semibold flex items-center">
                    {kw.suggested_title}
                    <CopyBtn text={kw.suggested_title} />
                  </p>
                </div>
              )}
              {kw.suggested_subtitle && (
                <div>
                  <p className="text-xs text-slate-600 mb-1">Subtitle</p>
                  <p className="text-slate-300 flex items-center">
                    {kw.suggested_subtitle}
                    <CopyBtn text={kw.suggested_subtitle} />
                  </p>
                </div>
              )}
            </section>
          )}

          {/* ── Section: KDP Backend Keywords ── */}
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-2">
              <Tag size={14} /> KDP Backend Keywords
            </h2>
            <p className="text-xs text-slate-600 mb-4">7 keywords max, 50 chars each. No duplicates with title.</p>
            <div className="space-y-2">
              {Array(7).fill(null).map((_, i) => {
                const val = backendKws[i] || '';
                const overLimit = val.length > 50;
                return (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-slate-600 text-xs w-4 shrink-0">{i + 1}</span>
                    <input
                      type="text"
                      value={val}
                      maxLength={60}
                      onChange={e => {
                        const next = [...backendKws];
                        next[i] = e.target.value;
                        setBackendKws(next);
                      }}
                      className={`flex-1 bg-slate-800 border rounded-lg px-3 py-2 text-sm text-white focus:outline-none transition-colors ${
                        overLimit ? 'border-red-500 focus:border-red-400' : 'border-slate-700 focus:border-amber-500'
                      }`}
                      placeholder={`Keyword ${i + 1}`}
                    />
                    <span className={`text-xs w-10 text-right ${overLimit ? 'text-red-400' : 'text-slate-600'}`}>
                      {val.length}/50
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ── Section: KDP Categories ── */}
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Layers size={14} /> KDP Categories
            </h2>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">Category 1 (Primary)</label>
                <input
                  type="text"
                  value={cat1}
                  onChange={e => setCat1(e.target.value)}
                  placeholder="Fiction › Thrillers › Psychological"
                  className="w-full bg-slate-800 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Category 2 (Secondary)</label>
                <input
                  type="text"
                  value={cat2}
                  onChange={e => setCat2(e.target.value)}
                  placeholder="Fiction › Mystery & Detective › Amateur Sleuth"
                  className="w-full bg-slate-800 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none"
                />
              </div>
            </div>
          </section>

          {/* ── Section: Primary Keywords ── */}
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Search size={14} /> Primary Keywords ({primaryKws.length})
            </h2>
            <div className="flex flex-wrap gap-2 mb-4">
              {primaryKws.map((kw, i) => (
                <KwTag key={i} kw={kw} onRemove={() => setPrimaryKws(prev => prev.filter((_, idx) => idx !== i))} />
              ))}
              {primaryKws.length === 0 && <p className="text-slate-600 text-sm">No primary keywords yet.</p>}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newKwInput}
                onChange={e => setNewKwInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addPrimaryKw()}
                placeholder="Add keyword and press Enter…"
                className="flex-1 bg-slate-800 border border-slate-700 focus:border-amber-500 rounded-lg px-4 py-2 text-sm text-white focus:outline-none"
              />
              <button
                onClick={addPrimaryKw}
                className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
              >
                Add
              </button>
            </div>
          </section>

          {/* ── Section: Competitor ASINs ── */}
          {competitors.length > 0 && (
            <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <ShoppingCart size={14} /> Competitor Analysis ({competitors.length} books)
                <span className="text-slate-600 font-normal normal-case text-xs ml-auto">
                  avg {kw.avg_competitor_reviews} reviews
                </span>
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-500 text-xs uppercase border-b border-slate-800">
                      <th className="text-left pb-2">ASIN</th>
                      <th className="text-left pb-2">Title</th>
                      <th className="text-right pb-2">BSR</th>
                      <th className="text-right pb-2">Reviews</th>
                      <th className="text-right pb-2">Rating</th>
                      <th className="text-right pb-2">Price</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {competitors.map((c, i) => (
                      <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-2 font-mono text-xs text-amber-400">
                          <a
                            href={`https://amazon.com/dp/${c.asin}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-amber-300"
                          >
                            {c.asin} ↗
                          </a>
                        </td>
                        <td className="py-2 text-slate-300 max-w-xs truncate">{c.title || '—'}</td>
                        <td className="py-2 text-right text-slate-400">{c.bsr?.toLocaleString() ?? '—'}</td>
                        <td className="py-2 text-right text-slate-400">{c.reviews?.toLocaleString() ?? '—'}</td>
                        <td className="py-2 text-right text-amber-400">{c.rating ? `${c.rating}★` : '—'}</td>
                        <td className="py-2 text-right text-emerald-400">{c.price ? `$${c.price}` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Last research info */}
          <div className="text-xs text-slate-700 text-center pb-4">
            Last research: {kw.last_research_at ? new Date(kw.last_research_at).toLocaleString() : 'Never'}
            {' · '}
            Created: {new Date(kw.created_at).toLocaleDateString()}
          </div>

        </div>
      )}
    </div>
  );
}
