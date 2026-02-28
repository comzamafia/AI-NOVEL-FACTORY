'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Fingerprint, ArrowLeft, RefreshCw, Loader2, Save,
  CheckCircle, AlertCircle, Wand2, Plus, X,
} from 'lucide-react';
import {
  getPenNames,
  getStyleFingerprint,
  updateStyleFingerprint,
  generateStylePrompt,
  createStyleFingerprint,
} from '@/lib/api';
import type { PenName, StyleFingerprint, CommonWordPatterns } from '@/types';

// ── Metric Slider ─────────────────────────────────────────────
function MetricRow({
  label, value, min, max, step, unit, onChange, color = 'bg-amber-500',
}: {
  label: string; value: number; min: number; max: number; step: number;
  unit?: string; onChange: (v: number) => void; color?: string;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-300">{label}</span>
        <span className="text-sm font-mono text-white">{value}{unit}</span>
      </div>
      <div className="relative h-2 bg-slate-800 rounded-full">
        <div className={`absolute h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
        <input
          type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(parseFloat(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer h-full"
        />
      </div>
      <div className="flex justify-between text-xs text-slate-600 mt-1">
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

// ── Word Pattern Editor ───────────────────────────────────────
function PatternEditor({
  label, items, onAdd, onRemove,
}: {
  label: string;
  items: string[];
  onAdd: (item: string) => void;
  onRemove: (i: number) => void;
}) {
  const [input, setInput] = useState('');
  return (
    <div>
      <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">{label}</p>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {items.map((item, i) => (
          <span key={i} className="flex items-center gap-1 text-xs bg-slate-800 border border-slate-700 text-slate-300 px-2.5 py-1 rounded-full">
            {item}
            <button onClick={() => onRemove(i)} className="text-slate-500 hover:text-red-400 transition-colors ml-0.5">
              <X size={10} />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text" value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && input.trim()) { onAdd(input.trim()); setInput(''); } }}
          placeholder="Add item, press Enter"
          className="flex-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500"
        />
        <button
          onClick={() => { if (input.trim()) { onAdd(input.trim()); setInput(''); } }}
          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs transition-colors">
          <Plus size={12} />
        </button>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function StyleFingerprintPage() {
  const { id } = useParams<{ id: string }>();

  const [penName, setPenName]  = useState<PenName | null>(null);
  const [fp,      setFp]       = useState<StyleFingerprint | null>(null);
  const [loading, setLoading]  = useState(true);
  const [saving,  setSaving]   = useState(false);
  const [genning, setGenning]  = useState(false);
  const [dirty,   setDirty]    = useState(false);
  const [toast,   setToast]    = useState<{ msg: string; ok: boolean } | null>(null);

  function showToast(msg: string, ok = true) {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [names, fingerprint] = await Promise.all([
        getPenNames(),
        getStyleFingerprint(id),
      ]);
      const pn = names.results.find((p: PenName) => String(p.id) === String(id));
      setPenName(pn ?? null);
      setFp(fingerprint);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  async function createEmpty() {
    if (!penName) return;
    try {
      const created = await createStyleFingerprint({ pen_name: penName.id });
      setFp(created);
      showToast('Style fingerprint created');
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Failed to create', false);
    }
  }

  async function handleSave() {
    if (!fp) return;
    setSaving(true);
    try {
      const updated = await updateStyleFingerprint(fp.id, {
        avg_sentence_length:  fp.avg_sentence_length,
        avg_paragraph_length: fp.avg_paragraph_length,
        avg_chapter_length:   fp.avg_chapter_length,
        dialogue_ratio:       fp.dialogue_ratio,
        adverb_frequency:     fp.adverb_frequency,
        passive_voice_ratio:  fp.passive_voice_ratio,
        common_word_patterns: fp.common_word_patterns,
        forbidden_words:      fp.forbidden_words,
        chapters_analyzed:    fp.chapters_analyzed,
        needs_recalculation:  fp.needs_recalculation,
      });
      setFp(updated);
      setDirty(false);
      showToast('Fingerprint saved');
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Failed to save', false);
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerate() {
    if (!fp) return;
    setGenning(true);
    try {
      const { fingerprint } = await generateStylePrompt(fp.id);
      setFp(fingerprint);
      showToast('System prompt regenerated');
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Failed to generate', false);
    } finally {
      setGenning(false);
    }
  }

  function update<K extends keyof StyleFingerprint>(key: K, value: StyleFingerprint[K]) {
    setFp(prev => prev ? { ...prev, [key]: value } : prev);
    setDirty(true);
  }

  function updatePattern(key: keyof CommonWordPatterns, items: string[]) {
    setFp(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        common_word_patterns: { ...prev.common_word_patterns, [key]: items },
      };
    });
    setDirty(true);
  }

  function addPattern(key: keyof CommonWordPatterns, item: string) {
    const current = fp?.common_word_patterns?.[key] ?? [];
    updatePattern(key, [...current, item]);
  }

  function removePattern(key: keyof CommonWordPatterns, i: number) {
    const current = fp?.common_word_patterns?.[key] ?? [];
    updatePattern(key, current.filter((_, idx) => idx !== i));
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">
        <Loader2 size={40} className="animate-spin" />
      </div>
    );
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
            <Link href="/pen-names" className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </Link>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Style Fingerprint</p>
              <h1 className="text-lg font-bold">{penName?.name ?? `Pen Name #${id}`}</h1>
            </div>
          </div>
          {fp && (
            <div className="flex items-center gap-2">
              <button onClick={handleGenerate} disabled={genning}
                className="flex items-center gap-2 text-sm bg-purple-600 hover:bg-purple-500 text-white font-semibold px-4 py-2 rounded-xl transition-colors disabled:opacity-50">
                {genning ? <Loader2 size={14} className="animate-spin" /> : <Wand2 size={14} />}
                {genning ? 'Generating…' : 'Regenerate Prompt'}
              </button>
              <button onClick={handleSave} disabled={saving || !dirty}
                className="flex items-center gap-2 text-sm bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-4 py-2 rounded-xl transition-colors disabled:opacity-50">
                {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
              <button onClick={load} className="text-slate-400 hover:text-white border border-slate-700 p-2 rounded-lg transition-colors">
                <RefreshCw size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!fp ? (
          // No fingerprint yet
          <div className="text-center py-24 text-slate-500">
            <Fingerprint size={56} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400 mb-2">No style fingerprint yet</p>
            <p className="text-sm text-slate-600 mb-6">Create one to define {penName?.name ?? 'this pen name'}'s writing DNA.</p>
            <button onClick={createEmpty}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-6 py-3 rounded-xl transition-colors mx-auto">
              <Plus size={16} /> Create Fingerprint
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-6">

              {/* Metadata Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Fingerprint size={14} className="text-amber-400" /> Overview
                </h2>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-slate-800 rounded-xl p-3 text-center">
                    <p className="text-xl font-bold text-white">{fp.chapters_analyzed}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Chapters Analyzed</p>
                  </div>
                  <div className={`bg-slate-800 rounded-xl p-3 text-center ${fp.needs_recalculation ? 'border border-amber-500/40' : ''}`}>
                    <p className={`text-xs font-semibold mt-1 ${fp.needs_recalculation ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {fp.needs_recalculation ? 'Needs Update' : 'Up to Date'}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">Status</p>
                  </div>
                  <div className="bg-slate-800 rounded-xl p-3 text-center">
                    <p className="text-xs text-slate-300 mt-1">
                      {fp.last_recalculated ? new Date(fp.last_recalculated).toLocaleDateString() : 'Never'}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">Last Updated</p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate-400 uppercase tracking-wider block mb-1.5">Chapters Analyzed</label>
                    <input
                      type="number" min="0" value={fp.chapters_analyzed}
                      onChange={e => update('chapters_analyzed', parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500 font-mono"
                    />
                  </div>
                  <div className="flex items-center gap-3 mt-5">
                    <input type="checkbox" id="needs_recalc" checked={fp.needs_recalculation}
                      onChange={e => update('needs_recalculation', e.target.checked)}
                      className="w-4 h-4 accent-amber-500" />
                    <label htmlFor="needs_recalc" className="text-sm text-slate-300 cursor-pointer">Needs Recalculation</label>
                  </div>
                </div>
              </div>

              {/* Quantitative Metrics */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5">Writing Metrics</h2>
                <div className="space-y-5">
                  <MetricRow label="Avg Sentence Length" value={fp.avg_sentence_length}
                    min={5} max={40} step={0.5} unit=" words"
                    onChange={v => update('avg_sentence_length', v)}
                    color="bg-amber-500" />
                  <MetricRow label="Avg Paragraph Length" value={fp.avg_paragraph_length}
                    min={1} max={10} step={0.25} unit=" sentences"
                    onChange={v => update('avg_paragraph_length', v)}
                    color="bg-blue-500" />
                  <MetricRow label="Avg Chapter Length" value={fp.avg_chapter_length}
                    min={500} max={5000} step={50} unit=" words"
                    onChange={v => update('avg_chapter_length', v)}
                    color="bg-purple-500" />
                </div>
              </div>

              {/* Style Ratios */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5">Style Ratios</h2>
                <div className="space-y-5">
                  <MetricRow label="Dialogue Ratio" value={Math.round(fp.dialogue_ratio * 100)}
                    min={0} max={80} step={1} unit="%"
                    onChange={v => update('dialogue_ratio', v / 100)}
                    color="bg-emerald-500" />
                  <MetricRow label="Adverb Frequency" value={Math.round(fp.adverb_frequency * 100)}
                    min={0} max={10} step={0.1} unit="%"
                    onChange={v => update('adverb_frequency', v / 100)}
                    color="bg-orange-500" />
                  <MetricRow label="Passive Voice Ratio" value={Math.round(fp.passive_voice_ratio * 100)}
                    min={0} max={40} step={1} unit="%"
                    onChange={v => update('passive_voice_ratio', v / 100)}
                    color="bg-red-500" />
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">

              {/* Word Patterns */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5">Word Patterns</h2>
                <div className="space-y-5">
                  <PatternEditor
                    label="Sentence Starters"
                    items={fp.common_word_patterns?.sentence_starters ?? []}
                    onAdd={item => addPattern('sentence_starters', item)}
                    onRemove={i => removePattern('sentence_starters', i)}
                  />
                  <PatternEditor
                    label="Transitions"
                    items={fp.common_word_patterns?.transitions ?? []}
                    onAdd={item => addPattern('transitions', item)}
                    onRemove={i => removePattern('transitions', i)}
                  />
                  <PatternEditor
                    label="Descriptive Patterns"
                    items={fp.common_word_patterns?.descriptive_patterns ?? []}
                    onAdd={item => addPattern('descriptive_patterns', item)}
                    onRemove={i => removePattern('descriptive_patterns', i)}
                  />
                </div>
              </div>

              {/* Forbidden Words */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                  Forbidden Words <span className="text-slate-600 text-xs">(clichés, overused terms)</span>
                </h2>
                <PatternEditor
                  label=""
                  items={fp.forbidden_words}
                  onAdd={item => update('forbidden_words', [...fp.forbidden_words, item])}
                  onRemove={i => update('forbidden_words', fp.forbidden_words.filter((_, idx) => idx !== i))}
                />
              </div>

              {/* Generated System Prompt */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <Wand2 size={14} className="text-purple-400" /> AI System Prompt
                  </h2>
                  {!fp.style_system_prompt && (
                    <button onClick={handleGenerate} disabled={genning}
                      className="text-xs bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 border border-purple-500/30 px-3 py-1 rounded-lg transition-colors flex items-center gap-1">
                      {genning ? <Loader2 size={10} className="animate-spin" /> : <Wand2 size={10} />}
                      Generate
                    </button>
                  )}
                </div>
                {fp.style_system_prompt ? (
                  <pre className="text-xs text-slate-300 bg-slate-800 rounded-xl p-4 whitespace-pre-wrap leading-relaxed font-mono overflow-auto max-h-64">
                    {fp.style_system_prompt}
                  </pre>
                ) : (
                  <div className="text-center py-8 text-slate-600">
                    <Wand2 size={24} className="mx-auto mb-2 opacity-40" />
                    <p className="text-sm">Click "Regenerate Prompt" to generate an AI system prompt from your metrics.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
