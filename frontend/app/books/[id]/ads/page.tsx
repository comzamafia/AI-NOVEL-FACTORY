'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Megaphone, ArrowLeft, RefreshCw, DollarSign,
  TrendingUp, TrendingDown, Target, MousePointerClick,
  Eye, ShoppingCart, Loader2, ChevronUp, ChevronDown,
} from 'lucide-react';
import { getBook, getAdsPerformanceHistory } from '@/lib/api';
import type { Book, AdsPerformance } from '@/types';

// ── Helpers ───────────────────────────────────────────────────────
const usd = (v: string | number | null | undefined) =>
  v != null ? `$${parseFloat(String(v)).toFixed(2)}` : '—';

const pct = (v: number | null | undefined) =>
  v != null ? `${v.toFixed(1)}%` : '—';

const num = (v: number | null | undefined) =>
  v != null ? v.toLocaleString() : '—';

function acosColor(acos: number | null) {
  if (acos === null) return 'text-slate-500';
  if (acos < 25) return 'text-emerald-400';
  if (acos < 50) return 'text-yellow-400';
  return 'text-red-400';
}

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

// ── ACOS trend bar ────────────────────────────────────────────────
function AcosTrendBar({
  date, acos, maxAcos,
}: { date: string; acos: number | null; maxAcos: number }) {
  const pctH = acos != null && maxAcos > 0 ? (acos / maxAcos) * 100 : 0;
  const color =
    acos == null ? 'bg-slate-700' :
    acos < 25 ? 'bg-emerald-500' :
    acos < 50 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="flex flex-col items-center gap-1 min-w-0">
      <span className="text-xs font-mono text-slate-400">{acos != null ? acos.toFixed(0) + '%' : '—'}</span>
      <div className="w-8 bg-slate-800 rounded overflow-hidden" style={{ height: '60px' }}>
        <div
          className={`w-full ${color} rounded transition-all duration-700`}
          style={{ height: `${pctH}%`, marginTop: `${100 - pctH}%` }}
        />
      </div>
      <span className="text-xs text-slate-600 truncate w-14 text-center">
        {date.slice(5)}  {/* MM-DD */}
      </span>
    </div>
  );
}

// ── Sort header ───────────────────────────────────────────────────
type SortField = 'report_date' | 'spend_usd' | 'sales_usd' | 'acos' | 'impressions' | 'clicks';

function SortHeader({
  label, field, current, dir, onSort,
}: {
  label: string; field: SortField;
  current: SortField; dir: 'asc' | 'desc';
  onSort: (f: SortField) => void;
}) {
  const active = current === field;
  return (
    <th
      className="text-right px-4 py-3 cursor-pointer select-none hover:text-white transition-colors"
      onClick={() => onSort(field)}
    >
      <span className={`inline-flex items-center gap-1 ${active ? 'text-amber-400' : ''}`}>
        {label}
        {active ? (dir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />) : null}
      </span>
    </th>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function AdsPerformancePage() {
  const { id } = useParams<{ id: string }>();
  const bookId = id;

  const [book, setBook]     = useState<Book | null>(null);
  const [records, setRecords] = useState<AdsPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<SortField>('report_date');
  const [sortDir, setSortDir]   = useState<'asc' | 'desc'>('desc');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, r] = await Promise.all([
        getBook(bookId),
        getAdsPerformanceHistory(bookId),
      ]);
      setBook(b);
      setRecords(r);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => { load(); }, [load]);

  // ── Sorting ────────────────────────────────────────────────────
  function handleSort(field: SortField) {
    if (field === sortField) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  }

  const sorted = [...records].sort((a, b) => {
    const aVal = a[sortField as keyof AdsPerformance];
    const bVal = b[sortField as keyof AdsPerformance];
    const av = aVal == null ? -Infinity : Number(aVal) || String(aVal);
    const bv = bVal == null ? -Infinity : Number(bVal) || String(bVal);
    if (av < bv) return sortDir === 'asc' ? -1 : 1;
    if (av > bv) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  // ── Aggregated totals (last 30 shown records) ──────────────────
  const totalSpend    = records.reduce((s, r) => s + parseFloat(String(r.spend_usd  ?? 0)), 0);
  const totalSales    = records.reduce((s, r) => s + parseFloat(String(r.sales_usd  ?? 0)), 0);
  const totalClicks   = records.reduce((s, r) => s + (r.clicks      ?? 0), 0);
  const totalImpr     = records.reduce((s, r) => s + (r.impressions  ?? 0), 0);
  const totalOrders   = records.reduce((s, r) => s + (r.orders       ?? 0), 0);
  const overallAcos   = totalSales > 0 ? (totalSpend / totalSales) * 100 : null;

  // ── ACOS trend (latest 14 days, oldest → newest) ───────────────
  const trendRecords = [...records]
    .sort((a, b) => a.report_date.localeCompare(b.report_date))
    .slice(-14);
  const maxAcos = Math.max(...trendRecords.map(r => r.acos ?? 0), 1);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link href={`/books/${bookId}`} className="text-slate-400 hover:text-white transition-colors shrink-0">
              <ArrowLeft size={20} />
            </Link>
            <div className="min-w-0">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Ads Performance</p>
              <h1 className="text-lg font-bold text-white truncate">
                {book?.title ?? 'Loading…'}
              </h1>
            </div>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-2 rounded-lg transition-colors disabled:opacity-40 shrink-0"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-500">
            <Loader2 size={40} className="animate-spin" />
          </div>
        ) : records.length === 0 ? (
          <div className="text-center py-24 text-slate-500">
            <Megaphone size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-xl text-slate-400">No ads performance data yet.</p>
            <p className="text-sm mt-2">Ads data syncs daily from Amazon Advertising API.</p>
          </div>
        ) : (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <KpiCard
                label="Total Spend"
                value={usd(totalSpend)}
                icon={<DollarSign size={20} />}
                color="text-orange-400"
              />
              <KpiCard
                label="Total Sales"
                value={usd(totalSales)}
                icon={<TrendingUp size={20} />}
                color="text-emerald-400"
              />
              <KpiCard
                label="Overall ACOS"
                value={overallAcos != null ? `${overallAcos.toFixed(1)}%` : '—'}
                sub="< 25% = great"
                icon={<Target size={20} />}
                color={overallAcos == null ? 'text-slate-500' : overallAcos < 25 ? 'text-emerald-400' : overallAcos < 50 ? 'text-yellow-400' : 'text-red-400'}
              />
              <KpiCard
                label="Impressions"
                value={num(totalImpr)}
                icon={<Eye size={20} />}
                color="text-blue-400"
              />
              <KpiCard
                label="Clicks"
                value={num(totalClicks)}
                sub={totalImpr > 0 ? `CTR ${((totalClicks / totalImpr) * 100).toFixed(2)}%` : undefined}
                icon={<MousePointerClick size={20} />}
                color="text-purple-400"
              />
              <KpiCard
                label="Orders"
                value={num(totalOrders)}
                sub={totalClicks > 0 ? `${((totalOrders / totalClicks) * 100).toFixed(1)}% conv.` : undefined}
                icon={<ShoppingCart size={20} />}
                color="text-amber-400"
              />
            </div>

            {/* ACOS Trend */}
            {trendRecords.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
                  <Target size={14} className="text-amber-400" />
                  ACOS Trend — Last {trendRecords.length} Days
                </h2>
                <div className="flex items-end gap-2 overflow-x-auto pb-2">
                  {trendRecords.map(r => (
                    <AcosTrendBar
                      key={r.id}
                      date={r.report_date}
                      acos={r.acos}
                      maxAcos={maxAcos}
                    />
                  ))}
                </div>
                {/* Legend */}
                <div className="flex items-center gap-5 mt-4 text-xs text-slate-600 justify-center">
                  <span className="flex items-center gap-1.5">
                    <TrendingUp size={12} className="text-emerald-400" />
                    &lt; 25% — Excellent
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Target size={12} className="text-yellow-400" />
                    25–50% — Acceptable
                  </span>
                  <span className="flex items-center gap-1.5">
                    <TrendingDown size={12} className="text-red-400" />
                    &gt; 50% — Unprofitable
                  </span>
                </div>
              </div>
            )}

            {/* Daily Performance Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Megaphone size={14} /> Daily Records
                </h2>
                <span className="text-xs text-slate-600">{records.length} days</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-500 text-xs uppercase tracking-wider border-b border-slate-800">
                      <SortHeader label="Date"        field="report_date"  current={sortField} dir={sortDir} onSort={handleSort} />
                      <SortHeader label="Impressions" field="impressions"  current={sortField} dir={sortDir} onSort={handleSort} />
                      <SortHeader label="Clicks"      field="clicks"       current={sortField} dir={sortDir} onSort={handleSort} />
                      <th className="text-right px-4 py-3 text-slate-500 text-xs uppercase tracking-wider">CTR</th>
                      <SortHeader label="Spend"       field="spend_usd"    current={sortField} dir={sortDir} onSort={handleSort} />
                      <SortHeader label="Sales"       field="sales_usd"    current={sortField} dir={sortDir} onSort={handleSort} />
                      <SortHeader label="ACOS"        field="acos"         current={sortField} dir={sortDir} onSort={handleSort} />
                      <th className="text-right px-4 py-3 text-slate-500 text-xs uppercase tracking-wider">CPC</th>
                      <th className="text-right px-4 py-3 text-slate-500 text-xs uppercase tracking-wider">Orders</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {sorted.map(r => (
                      <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-4 py-3 text-right font-mono text-slate-300 text-xs">
                          {r.report_date}
                        </td>
                        <td className="px-4 py-3 text-right text-slate-400 font-mono">
                          {num(r.impressions)}
                        </td>
                        <td className="px-4 py-3 text-right text-slate-400 font-mono">
                          {num(r.clicks)}
                        </td>
                        <td className="px-4 py-3 text-right text-slate-500 font-mono">
                          {pct(r.ctr)}
                        </td>
                        <td className="px-4 py-3 text-right text-orange-400 font-mono">
                          {usd(r.spend_usd)}
                        </td>
                        <td className="px-4 py-3 text-right text-emerald-400 font-mono">
                          {usd(r.sales_usd)}
                        </td>
                        <td className={`px-4 py-3 text-right font-mono ${acosColor(r.acos)}`}>
                          {pct(r.acos)}
                        </td>
                        <td className="px-4 py-3 text-right text-slate-500 font-mono">
                          {usd(r.cpc)}
                        </td>
                        <td className="px-4 py-3 text-right text-slate-300 font-mono">
                          {r.orders ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  {/* Totals row */}
                  <tfoot>
                    <tr className="border-t-2 border-slate-700 bg-slate-800/40">
                      <td className="px-4 py-3 text-right text-xs text-slate-500 uppercase font-semibold">Totals</td>
                      <td className="px-4 py-3 text-right text-blue-400 font-mono font-semibold">{num(totalImpr)}</td>
                      <td className="px-4 py-3 text-right text-purple-400 font-mono font-semibold">{num(totalClicks)}</td>
                      <td className="px-4 py-3 text-right text-slate-500 font-mono">
                        {totalImpr > 0 ? `${((totalClicks / totalImpr) * 100).toFixed(2)}%` : '—'}
                      </td>
                      <td className="px-4 py-3 text-right text-orange-400 font-mono font-semibold">{usd(totalSpend)}</td>
                      <td className="px-4 py-3 text-right text-emerald-400 font-mono font-semibold">{usd(totalSales)}</td>
                      <td className={`px-4 py-3 text-right font-mono font-semibold ${acosColor(overallAcos)}`}>
                        {overallAcos != null ? `${overallAcos.toFixed(1)}%` : '—'}
                      </td>
                      <td className="px-4 py-3" />
                      <td className="px-4 py-3 text-right text-amber-400 font-mono font-semibold">{num(totalOrders)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
