'use client';

import { useState, useEffect } from 'react';
import { calculateKDPDimensions, getCoverChoices } from '@/lib/api';
import type { KDPDimensions, CoverChoices } from '@/types';
import { Calculator, Info } from 'lucide-react';

export default function KDPCalculator() {
  const [choices, setChoices] = useState<CoverChoices | null>(null);
  const [coverType, setCoverType] = useState<'ebook' | 'paperback'>('ebook');
  const [trimSize, setTrimSize] = useState('6x9');
  const [paperType, setPaperType] = useState('bw_white');
  const [pageCount, setPageCount] = useState(300);
  const [result, setResult] = useState<KDPDimensions | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCoverChoices().then(setChoices).catch(() => {});
  }, []);

  async function calculate() {
    setLoading(true);
    try {
      const data = await calculateKDPDimensions({
        cover_type: coverType,
        trim_size: trimSize,
        paper_type: paperType,
        page_count: pageCount,
      });
      setResult(data);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }

  // Auto-calc on param change
  useEffect(() => { calculate(); }, [coverType, trimSize, paperType, pageCount]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
      <h2 className="flex items-center gap-2 text-white font-semibold text-lg">
        <Calculator size={18} className="text-amber-400" />
        KDP Dimension Calculator
      </h2>

      {/* Cover Type */}
      <div className="flex gap-2">
        {['ebook', 'paperback'].map((t) => (
          <button
            key={t}
            onClick={() => setCoverType(t as 'ebook' | 'paperback')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              coverType === t
                ? 'bg-amber-500 text-slate-900'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Paperback options */}
      {coverType === 'paperback' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Trim Size</label>
            <select
              value={trimSize}
              onChange={(e) => setTrimSize(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              {(choices?.trim_sizes ?? []).map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Paper Type</label>
            <select
              value={paperType}
              onChange={(e) => setPaperType(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              {(choices?.paper_types ?? []).map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              Page Count <span className="text-slate-500">(interior pages)</span>
            </label>
            <input
              type="number"
              min={24}
              max={828}
              value={pageCount}
              onChange={(e) => setPageCount(Number(e.target.value))}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>
        </div>
      )}

      {/* Results */}
      {loading && <p className="text-slate-400 text-sm text-center py-2">Calculating…</p>}

      {result && !loading && (
        <div className="space-y-3">
          {result.cover_type === 'ebook' && (
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Width" value={`${result.width_px} px`} />
              <Stat label="Height" value={`${result.height_px} px`} />
              <Stat label="Aspect Ratio" value={`1 : ${result.aspect_ratio.toFixed(2)}`} />
              <Stat label="Est. File Size" value={`~${(result.file_size_kb_approx / 1024).toFixed(1)} MB`} />
            </div>
          )}

          {result.cover_type === 'paperback' && (
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Spine Width" value={`${result.spine_width_in.toFixed(4)}"`} accent />
              <Stat label="Canvas (px)" value={`${result.total_width_px} × ${result.total_height_px}`} accent />
              <Stat label="Total Width" value={`${result.total_width_in.toFixed(4)}"`} />
              <Stat label="Total Height" value={`${result.total_height_in.toFixed(4)}"`} />
              <Stat label="Trim" value={`${result.trim_width_in}" × ${result.trim_height_in}"`} />
              <Stat label="DPI" value={`${result.dpi}`} />
            </div>
          )}

          {/* Notes */}
          <div className="bg-slate-900/50 rounded-xl p-3 space-y-1">
            {result.notes.map((n, i) => (
              <p key={i} className="text-xs text-slate-400 flex gap-2">
                <Info size={12} className="shrink-0 mt-0.5 text-amber-400" />
                {n}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="bg-slate-900/50 rounded-xl p-3">
      <p className="text-xs text-slate-500 mb-0.5">{label}</p>
      <p className={`text-sm font-semibold ${accent ? 'text-amber-400' : 'text-white'}`}>{value}</p>
    </div>
  );
}
