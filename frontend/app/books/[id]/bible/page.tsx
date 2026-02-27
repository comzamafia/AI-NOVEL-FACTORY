'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, BookMarked, Loader2, Sparkles, Save,
  ChevronDown, ChevronRight, Users, Globe, Clock, GitBranch,
  Lightbulb, Palette, Eye, FileText,
} from 'lucide-react';
import { getBook, getStoryBible, updateStoryBible, generateBibleSummary } from '@/lib/api';
import type { Book, StoryBible } from '@/types';

// ── Collapsible JSON section ──────────────────────────────────────
function JsonSection({
  icon,
  title,
  hint,
  value,
  onChange,
}: {
  icon: React.ReactNode;
  title: string;
  hint?: string;
  value: unknown[] | Record<string, unknown>;
  onChange: (val: unknown[] | Record<string, unknown>) => void;
}) {
  const [open, setOpen] = useState(true);
  const [raw, setRaw]   = useState(JSON.stringify(value, null, 2));
  const [err, setErr]   = useState('');

  function handleBlur() {
    try {
      const parsed = JSON.parse(raw) as unknown[] | Record<string, unknown>;
      onChange(parsed);
      setErr('');
    } catch {
      setErr('Invalid JSON — changes not saved');
    }
  }

  // Sync if parent updates
  useEffect(() => {
    setRaw(JSON.stringify(value, null, 2));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-slate-800/50 transition-colors"
      >
        <span className="text-amber-400">{icon}</span>
        <span className="font-semibold text-white text-sm">{title}</span>
        {hint && <span className="text-slate-600 text-xs ml-1">({hint})</span>}
        <span className="ml-auto text-slate-500">
          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </span>
      </button>
      {open && (
        <div className="border-t border-slate-800 px-5 py-4">
          <textarea
            value={raw}
            onChange={e => setRaw(e.target.value)}
            onBlur={handleBlur}
            rows={10}
            className="w-full bg-slate-800/50 border border-slate-700 focus:border-amber-500 rounded-xl p-4 text-sm text-slate-300 font-mono resize-y focus:outline-none"
            placeholder="[]"
          />
          {err && <p className="text-red-400 text-xs mt-1">{err}</p>}
        </div>
      )}
    </div>
  );
}

// ── Text field section ────────────────────────────────────────────
function TextField({
  icon,
  label,
  value,
  onChange,
  multiline = false,
  placeholder,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  multiline?: boolean;
  placeholder?: string;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <label className="flex items-center gap-2 text-sm font-semibold text-slate-400 mb-3">
        <span className="text-amber-400">{icon}</span>
        {label}
      </label>
      {multiline ? (
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          rows={4}
          placeholder={placeholder}
          className="w-full bg-slate-800/50 border border-slate-700 focus:border-amber-500 rounded-xl p-4 text-sm text-white resize-y focus:outline-none"
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-slate-800/50 border border-slate-700 focus:border-amber-500 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none"
        />
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function StoryBiblePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [book, setBook]       = useState<Book | null>(null);
  const [bible, setBible]     = useState<StoryBible | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [generating, setGenerating] = useState(false);
  const [toast, setToast]     = useState<{ msg: string; type: 'ok' | 'err' } | null>(null);

  // Draft editable state
  const [characters, setCharacters]     = useState<unknown[] | Record<string, unknown>>([]);
  const [worldRules, setWorldRules]     = useState<unknown[] | Record<string, unknown>>([]);
  const [timeline, setTimeline]         = useState<unknown[] | Record<string, unknown>>([]);
  const [outline, setOutline]           = useState<unknown[] | Record<string, unknown>>({});
  const [clues, setClues]               = useState<unknown[] | Record<string, unknown>>([]);
  const [themes, setThemes]             = useState('');
  const [tone, setTone]                 = useState('');
  const [pov, setPov]                   = useState('');
  const [tense, setTense]               = useState('');
  const [aiSummary, setAiSummary]       = useState('');

  const showToast = useCallback((msg: string, type: 'ok' | 'err' = 'ok') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [bk, bl] = await Promise.all([getBook(id), getStoryBible(id)]);
      setBook(bk);
      if (bl) {
        setBible(bl);
        setCharacters(bl.characters ?? []);
        setWorldRules(bl.world_rules ?? []);
        setTimeline(bl.timeline ?? []);
        setOutline(bl.four_act_outline ?? {});
        setClues(bl.clues_tracker ?? []);
        setThemes(bl.themes ?? '');
        setTone(bl.tone ?? '');
        setPov(bl.pov ?? '');
        setTense(bl.tense ?? '');
        setAiSummary(bl.summary_for_ai ?? '');
      }
    } catch { showToast('Failed to load', 'err'); }
    finally { setLoading(false); }
  }, [id, showToast]);

  useEffect(() => { load(); }, [load]);

  async function save() {
    if (!bible) return;
    setSaving(true);
    try {
      const updated = await updateStoryBible(bible.id, {
        characters,
        world_rules: worldRules,
        timeline,
        four_act_outline: outline,
        clues_tracker: clues,
        themes,
        tone,
        pov,
        tense,
      });
      setBible(updated);
      showToast('Story Bible saved');
    } catch { showToast('Save failed', 'err'); }
    finally { setSaving(false); }
  }

  async function handleGenerateSummary() {
    if (!bible) return;
    setGenerating(true);
    try {
      const result = await generateBibleSummary(bible.id);
      setAiSummary(result.summary);
      setBible(prev => prev ? { ...prev, summary_for_ai: result.summary } : prev);
      showToast('AI summary generated');
    } catch { showToast('Generation failed', 'err'); }
    finally { setGenerating(false); }
  }

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">
      <Loader2 size={40} className="animate-spin" />
    </div>
  );

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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <button onClick={() => router.back()} className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </button>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Story Bible</p>
              <h1 className="text-xl font-bold text-white flex items-center gap-2 truncate max-w-xs sm:max-w-md">
                <BookMarked size={18} className="text-amber-400 shrink-0" />
                {book?.title ?? '…'}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerateSummary}
              disabled={!bible || generating}
              className="flex items-center gap-2 text-sm border border-slate-700 hover:border-amber-500/50 text-slate-400 hover:text-amber-400 px-3 py-2 rounded-lg transition-colors disabled:opacity-40"
            >
              {generating ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
              Regen AI Summary
            </button>
            <button
              onClick={save}
              disabled={!bible || saving}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-900 font-bold px-5 py-2 rounded-xl text-sm transition-colors"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              Save Bible
            </button>
          </div>
        </div>
      </div>

      {!bible ? (
        <div className="max-w-4xl mx-auto px-4 py-20 text-center text-slate-600">
          <BookMarked size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg mb-2">No Story Bible yet.</p>
          <p className="text-sm text-slate-700">Generate the Story Bible from the Workflow panel.</p>
          <Link href={`/books/${id}/workflow`} className="inline-block mt-4 text-amber-400 hover:text-amber-300 text-sm underline">
            Go to Workflow →
          </Link>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-5">

          {/* Prose metadata fields */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <TextField icon={<Palette size={14} />} label="Themes" value={themes} onChange={setThemes} placeholder="dark, redemption…" />
            <TextField icon={<Eye size={14} />} label="Tone" value={tone} onChange={setTone} placeholder="dark, fast-paced…" />
            <TextField icon={<Eye size={14} />} label="POV" value={pov} onChange={setPov} placeholder="3rd limited…" />
            <TextField icon={<FileText size={14} />} label="Tense" value={tense} onChange={setTense} placeholder="past…" />
          </div>

          {/* JSON sections */}
          <JsonSection icon={<Users size={14} />} title="Characters" hint="array of character objects" value={characters} onChange={setCharacters} />
          <JsonSection icon={<Globe size={14} />} title="World Rules" hint="array or object" value={worldRules} onChange={setWorldRules} />
          <JsonSection icon={<Clock size={14} />} title="Timeline" hint="array of events" value={timeline} onChange={setTimeline} />
          <JsonSection icon={<GitBranch size={14} />} title="4-Act Outline" hint="object with act keys" value={outline} onChange={setOutline} />
          <JsonSection icon={<Lightbulb size={14} />} title="Clues Tracker" hint="array of clue objects" value={clues} onChange={setClues} />

          {/* AI Summary (read-only display) */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
                <Sparkles size={14} className="text-amber-400" />
                AI Prompt Summary
                <span className="text-slate-600 font-normal text-xs">(injected into writing sessions)</span>
              </h2>
              <button
                onClick={handleGenerateSummary}
                disabled={generating}
                className="text-xs text-amber-400 hover:text-amber-300 disabled:opacity-40 transition-colors"
              >
                {generating ? 'Generating…' : 'Regenerate'}
              </button>
            </div>
            {aiSummary ? (
              <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{aiSummary}</p>
            ) : (
              <p className="text-sm text-slate-600 italic">No summary yet. Click &quot;Regen AI Summary&quot; above.</p>
            )}
          </div>

          {/* Timestamps */}
          <p className="text-xs text-slate-700 text-center pb-4">
            Last updated: {new Date(bible.updated_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}
