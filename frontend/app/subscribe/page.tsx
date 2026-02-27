'use client';

import { useState } from 'react';
import { Check, Zap, BookOpen, Lock } from 'lucide-react';
import { PRICES } from '@/lib/stripe';

const FEATURES = [
  'Unlimited access to ALL books and chapters',
  'New chapters every 3 days — read them first',
  'Full backlog of every published chapter',
  'Cancel anytime, no questions asked',
  'Read on any device',
];

export default function SubscribePage() {
  const [plan, setPlan] = useState<'monthly' | 'annual'>('monthly');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const monthlyEquiv = plan === 'annual' ? (PRICES.subscription_annual / 12).toFixed(2) : null;

  const handleSubscribe = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'subscription',
          plan,
          successUrl: `${window.location.origin}/?subscribed=1`,
          cancelUrl: `${window.location.origin}/subscribe?canceled=1`,
        }),
      });
      if (!res.ok) throw new Error('Failed to create checkout session');
      const { url } = await res.json();
      window.location.href = url;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm px-4 py-1.5 rounded-full mb-4">
          <Zap size={14} className="fill-amber-400 text-amber-400" />
          Unlimited Reading
        </div>
        <h1 className="text-5xl font-extrabold text-white mb-3">NovelFactory Premium</h1>
        <p className="text-slate-400 text-lg">
          Unlock every chapter, every book — past, present, and future.
        </p>
      </div>

      {/* Plan toggle */}
      <div className="flex items-center justify-center gap-3 mb-8">
        <button
          onClick={() => setPlan('monthly')}
          className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-colors ${
            plan === 'monthly'
              ? 'bg-amber-500 text-slate-900'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          Monthly
        </button>
        <button
          onClick={() => setPlan('annual')}
          className={`flex items-center gap-1.5 px-5 py-2.5 rounded-full text-sm font-semibold transition-colors ${
            plan === 'annual'
              ? 'bg-amber-500 text-slate-900'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          Annual
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-bold ${
              plan === 'annual' ? 'bg-slate-900 text-amber-400' : 'bg-green-500/20 text-green-400'
            }`}
          >
            Save 33%
          </span>
        </button>
      </div>

      {/* Pricing card */}
      <div className="rounded-3xl bg-slate-800 border border-amber-500/40 p-8 shadow-2xl shadow-amber-500/10 mb-6">
        {/* Price */}
        <div className="text-center mb-8">
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-slate-400 text-xl">$</span>
            <span className="text-7xl font-extrabold text-white">
              {plan === 'annual' ? PRICES.subscription_annual.toFixed(0) : PRICES.subscription_monthly.toFixed(2)}
            </span>
            <span className="text-slate-400 text-lg">/{plan === 'annual' ? 'year' : 'month'}</span>
          </div>
          {monthlyEquiv && (
            <p className="text-green-400 text-sm mt-2">
              Just ${monthlyEquiv}/month — billed annually
            </p>
          )}
        </div>

        {/* Features */}
        <ul className="space-y-3 mb-8">
          {FEATURES.map((f) => (
            <li key={f} className="flex items-start gap-3">
              <Check size={18} className="text-green-400 flex-shrink-0 mt-0.5" />
              <span className="text-slate-200 text-sm">{f}</span>
            </li>
          ))}
        </ul>

        {/* Error */}
        {error && (
          <p className="text-red-400 text-sm text-center mb-4">{error}</p>
        )}

        {/* CTA button */}
        <button
          onClick={handleSubscribe}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-60 text-slate-900 font-extrabold py-4 rounded-2xl text-lg transition-colors shadow-lg shadow-amber-500/30"
        >
          {loading ? (
            <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-slate-900" />
          ) : (
            <>
              <Lock size={18} />
              Start Subscribing
            </>
          )}
        </button>

        <p className="text-center text-slate-500 text-xs mt-4">
          Secured by Stripe · Cancel anytime · No hidden fees
        </p>
      </div>

      {/* Compare vs per-chapter */}
      <div className="text-center p-5 rounded-2xl bg-slate-800/50 border border-slate-700">
        <h3 className="text-white font-semibold mb-3 flex items-center gap-2 justify-center">
          <BookOpen size={16} className="text-amber-400" />
          vs. Pay-per-Chapter
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="p-3 bg-slate-700 rounded-xl">
            <p className="text-amber-400 font-bold">$1.99/chapter</p>
            <p className="text-slate-400 text-xs mt-1">Buy chapters individually — forever yours</p>
          </div>
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
            <p className="text-amber-300 font-bold">
              ${(plan === 'annual' ? PRICES.subscription_annual / 12 : PRICES.subscription_monthly).toFixed(2)}/mo
            </p>
            <p className="text-slate-400 text-xs mt-1">All books, all chapters, all the time</p>
          </div>
        </div>
      </div>
    </div>
  );
}
