'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  DollarSign, ArrowLeft, RefreshCw, Loader2, TrendingUp,
  Zap, Calendar, CheckCircle, AlertCircle, Clock, ChevronRight,
  ToggleLeft, ToggleRight, Save,
} from 'lucide-react';
import { getBook, getPricingStrategy, logPriceChange, updatePricingStrategy } from '@/lib/api';
import type { Book, PricingStrategy, PricingPhase, PriceHistoryEntry } from '@/types';

// ── Phase metadata ────────────────────────────────────────────────
const PHASES: { value: PricingPhase; label: string; price: string; color: string; desc: string }[] = [
  { value: 'launch',  label: 'Launch',  price: '$0.99', color: 'bg-blue-500',   desc: 'Initial sales push with low price' },
  { value: 'growth',  label: 'Growth',  price: '$2.99', color: 'bg-indigo-500', desc: 'Reviews building, steady demand' },
  { value: 'mature',  label: 'Mature',  price: '$3.99', color: 'bg-emerald-500',desc: 'Full price, strong review base' },
  { value: 'promo',   label: 'Promo',   price: '$0.99', color: 'bg-amber-500',  desc: 'Kindle Countdown / temporary promo' },
  { value: 'bundle',  label: 'Bundle',  price: 'Varies',color: 'bg-purple-500', desc: 'Box set or bundle pricing' },
];

const PROMO_LABELS: Record<string, string> = {
  kindle_countdown: 'Kindle Countdown Deal',
  free_promo:       'Free Promotion (KDP Select)',
  price_drop:       'Temporary Price Drop',
};

// ── KPI Card ──────────────────────────────────────────────────────
function KpiCard({
  label, value, sub, icon, color = 'text-amber-400',
}: {
  label: string; value: string; sub?: string;
  icon: React.ReactNode; color?: string;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <div className={`mb-3 ${color}`}>{icon}</div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-slate-400 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
    </div>
  );
}

// ── Phase stepper ─────────────────────────────────────────────────
function PhaseStepper({ current }: { current: PricingPhase }) {
  const mainPhases = PHASES.filter(p => p.value !== 'bundle' && p.value !== 'promo');
  return (
    <div className="flex items-center gap-0 overflow-x-auto">
      {mainPhases.map((phase, i) => {
        const isActive  = phase.value === current;
        const isPast    = mainPhases.findIndex(p => p.value === current) > i;
        return (
          <div key={phase.value} className="flex items-center shrink-0">
            <div className={`flex flex-col items-center gap-2 px-4 py-3 rounded-2xl transition-all ${
              isActive
                ? `${phase.color} bg-opacity-20 border-2 border-current ring-2 ring-${phase.color}/30`
                : isPast
                  ? 'opacity-60'
                  : 'opacity-40'
            }`}>
              <div className={`w-3 h-3 rounded-full ${isActive ? phase.color : isPast ? 'bg-emerald-600' : 'bg-slate-700'}`} />
              <p className={`text-xs font-semibold whitespace-nowrap ${isActive ? 'text-white' : 'text-slate-400'}`}>
                {phase.label}
              </p>
              <p className={`text-xs font-mono ${isActive ? 'text-white' : 'text-slate-600'}`}>
                {phase.price}
              </p>
            </div>
            {i < mainPhases.length - 1 && (
              <ChevronRight size={16} className={isPast || isActive ? 'text-slate-500' : 'text-slate-700'} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Price history timeline ─────────────────────────────────────────
function PriceHistory({ entries }: { entries: PriceHistoryEntry[] }) {
  const sorted = [...entries].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  if (sorted.length === 0) return (
    <p className="text-slate-600 text-sm py-4 text-center">No price history yet.</p>
  );

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-4 top-4 bottom-4 w-px bg-slate-800" />
      <div className="space-y-4">
        {sorted.map((entry, i) => {
          const phase = PHASES.find(p => p.value === entry.phase);
          return (
            <div key={i} className="flex items-start gap-4 pl-2">
              <div className={`mt-1.5 w-4 h-4 rounded-full shrink-0 border-2 border-slate-950 z-10 ${phase?.color ?? 'bg-slate-600'}`} />
              <div className="flex-1 pb-2">
                <div className="flex items-baseline gap-3 flex-wrap">
                  <span className="text-white font-mono font-bold text-lg">${Number(entry.price).toFixed(2)}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                    {phase?.label ?? entry.phase}
                  </span>
                </div>
                <p className="text-slate-500 text-xs mt-0.5">{entry.reason}</p>
                <p className="text-slate-700 text-xs font-mono mt-0.5">
                  {new Date(entry.date).toLocaleString()}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Log Change Modal ──────────────────────────────────────────────
function LogChangeModal({
  strategyId,
  currentPrice,
  currentPhase,
  onClose,
  onSaved,
}: {
  strategyId: number;
  currentPrice: number;
  currentPhase: PricingPhase;
  onClose: () => void;
  onSaved: (s: PricingStrategy) => void;
}) {
  const [price,  setPrice]  = useState(String(currentPrice));
  const [phase,  setPhase]  = useState<PricingPhase>(currentPhase);
  const [reason, setReason] = useState('');
  const [busy,   setBusy]   = useState(false);
  const [err,    setErr]    = useState('');

  async function submit() {
    const p = parseFloat(price);
    if (isNaN(p) || p < 0)       { setErr('Enter a valid price'); return; }
    if (!reason.trim())           { setErr('Reason is required'); return; }
    setBusy(true);
    try {
      const updated = await logPriceChange(strategyId, p, phase, reason.trim());
      onSaved(updated);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to log change');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
          <DollarSign size={18} className="text-amber-400" />
          Log Price Change
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">New Price (USD)</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={price}
                onChange={e => setPrice(e.target.value)}
                className="w-full pl-8 pr-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Phase</label>
            <select
              value={phase}
              onChange={e => setPhase(e.target.value as PricingPhase)}
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none"
            >
              {PHASES.map(p => (
                <option key={p.value} value={p.value}>{p.label} — {p.price}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Reason</label>
            <input
              type="text"
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="e.g. Kindle Countdown Deal activated"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl text-white text-sm focus:outline-none"
            />
          </div>

          {err && <p className="text-red-400 text-xs">{err}</p>}

          <div className="flex gap-3 pt-2">
            <button
              onClick={submit}
              disabled={busy}
              className="flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold py-2.5 rounded-xl transition-colors disabled:opacity-50"
            >
              {busy ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              {busy ? 'Saving…' : 'Log Change'}
            </button>
            <button
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function PricingPage() {
  const { id } = useParams<{ id: string }>();
  const bookId = id;

  const [book,     setBook]     = useState<Book | null>(null);
  const [strategy, setStrategy] = useState<PricingStrategy | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [toast,    setToast]    = useState<{ msg: string; ok: boolean } | null>(null);
  const [showModal,setShowModal]= useState(false);
  const [savingAuto, setSavingAuto] = useState(false);

  function showToast(msg: string, ok = true) {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, s] = await Promise.all([getBook(bookId), getPricingStrategy(bookId)]);
      setBook(b);
      setStrategy(s);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => { load(); }, [load]);

  async function toggleAutoPricing() {
    if (!strategy) return;
    setSavingAuto(true);
    try {
      const updated = await updatePricingStrategy(strategy.id, {
        auto_price_enabled: !strategy.auto_price_enabled,
      });
      setStrategy(updated);
      showToast(`Auto-pricing ${updated.auto_price_enabled ? 'enabled' : 'disabled'}`);
    } catch {
      showToast('Failed to update auto-pricing', false);
    } finally {
      setSavingAuto(false);
    }
  }

  const currentPhaseInfo = PHASES.find(p => p.value === strategy?.current_phase);

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

      {/* Log Change Modal */}
      {showModal && strategy && (
        <LogChangeModal
          strategyId={strategy.id}
          currentPrice={parseFloat(String(strategy.current_price_usd))}
          currentPhase={strategy.current_phase}
          onClose={() => setShowModal(false)}
          onSaved={(updated) => { setStrategy(updated); setShowModal(false); showToast('Price change logged'); }}
        />
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link href={`/books/${bookId}`} className="text-slate-400 hover:text-white transition-colors shrink-0">
              <ArrowLeft size={20} />
            </Link>
            <div className="min-w-0">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Pricing Strategy</p>
              <h1 className="text-lg font-bold text-white truncate">{book?.title ?? 'Loading…'}</h1>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {strategy && (
              <button
                onClick={() => setShowModal(true)}
                className="flex items-center gap-2 text-sm bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2 rounded-xl transition-colors"
              >
                <DollarSign size={14} />
                Log Change
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

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-500">
            <Loader2 size={40} className="animate-spin" />
          </div>
        ) : !strategy ? (
          <div className="text-center py-24 text-slate-500">
            <DollarSign size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400">No pricing strategy found.</p>
            <p className="text-sm mt-2">A pricing strategy is created automatically when a book is published.</p>
          </div>
        ) : (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <KpiCard
                label="Current Price"
                value={`$${parseFloat(String(strategy.current_price_usd)).toFixed(2)}`}
                sub="Active listing price"
                icon={<DollarSign size={20} />}
                color="text-emerald-400"
              />
              <KpiCard
                label="Current Phase"
                value={strategy.current_phase_display}
                sub={currentPhaseInfo?.desc}
                icon={<TrendingUp size={20} />}
                color={
                  strategy.current_phase === 'mature' ? 'text-emerald-400' :
                  strategy.current_phase === 'launch' ? 'text-blue-400' :
                  strategy.current_phase === 'promo'  ? 'text-amber-400' : 'text-indigo-400'
                }
              />
              <KpiCard
                label="Reviews for Growth"
                value={String(strategy.reviews_threshold_for_growth)}
                sub="Needed to exit Launch phase"
                icon={<Zap size={20} />}
                color="text-yellow-400"
              />
              <KpiCard
                label="Next Promotion"
                value={strategy.next_promotion_date
                  ? new Date(strategy.next_promotion_date).toLocaleDateString()
                  : '—'}
                sub={strategy.next_promotion_type ? PROMO_LABELS[strategy.next_promotion_type] : undefined}
                icon={<Calendar size={20} />}
                color="text-purple-400"
              />
            </div>

            {/* Phase Stepper */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5 flex items-center gap-2">
                <TrendingUp size={14} className="text-amber-400" />
                Pricing Phase Pipeline
              </h2>
              <PhaseStepper current={strategy.current_phase} />
            </div>

            {/* Settings & Promo */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Settings card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Zap size={14} className="text-amber-400" /> Settings
                </h2>

                {/* Auto-pricing toggle */}
                <div className="flex items-center justify-between py-3 border-b border-slate-800">
                  <div>
                    <p className="text-sm font-medium text-white">Auto-Pricing</p>
                    <p className="text-xs text-slate-500 mt-0.5">Automatically transitions phases based on rules</p>
                  </div>
                  <button
                    onClick={toggleAutoPricing}
                    disabled={savingAuto}
                    className="transition-colors"
                    title={strategy.auto_price_enabled ? 'Disable' : 'Enable'}
                  >
                    {strategy.auto_price_enabled
                      ? <ToggleRight size={32} className="text-emerald-400" />
                      : <ToggleLeft size={32} className="text-slate-600" />}
                  </button>
                </div>

                {/* KDP Select */}
                <div className="flex items-center justify-between py-3 border-b border-slate-800">
                  <div>
                    <p className="text-sm font-medium text-white">KDP Select</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {strategy.kdp_select_enrollment_date
                        ? `Enrolled: ${new Date(strategy.kdp_select_enrollment_date).toLocaleDateString()}`
                        : 'Not enrolled'}
                    </p>
                  </div>
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                    strategy.is_kdp_select
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-slate-700 text-slate-400'
                  }`}>
                    {strategy.is_kdp_select ? 'Active' : 'Inactive'}
                  </span>
                </div>

                {/* Days in launch phase */}
                <div className="flex items-center justify-between py-3 border-b border-slate-800">
                  <div>
                    <p className="text-sm font-medium text-white">Launch Phase Duration</p>
                    <p className="text-xs text-slate-500 mt-0.5">Minimum days before phase transition</p>
                  </div>
                  <span className="text-sm font-mono text-amber-400">{strategy.days_in_launch_phase}d</span>
                </div>

                {/* Days between promotions */}
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium text-white">Promo Cooldown</p>
                    <p className="text-xs text-slate-500 mt-0.5">Min days between Kindle Countdown deals</p>
                  </div>
                  <span className="text-sm font-mono text-purple-400">{strategy.days_between_promotions}d</span>
                </div>
              </div>

              {/* Promotion window */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Calendar size={14} className="text-amber-400" /> Promotion Schedule
                </h2>

                <div className="space-y-4 text-sm">
                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Last Promotion</span>
                    <span className="text-white font-mono">
                      {strategy.last_promotion_date
                        ? new Date(strategy.last_promotion_date).toLocaleDateString()
                        : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Next Promotion</span>
                    <span className="text-white font-mono">
                      {strategy.next_promotion_date
                        ? new Date(strategy.next_promotion_date).toLocaleDateString()
                        : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-3">
                    <span className="text-slate-400">Promotion Type</span>
                    <span className="text-purple-400">
                      {strategy.next_promotion_type
                        ? PROMO_LABELS[strategy.next_promotion_type] || strategy.next_promotion_type
                        : '—'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Price History Timeline */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-5 flex items-center gap-2">
                <Clock size={14} className="text-amber-400" />
                Price Change History
                <span className="text-slate-600 font-normal">({strategy.price_history.length} entries)</span>
              </h2>
              <PriceHistory entries={strategy.price_history} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
