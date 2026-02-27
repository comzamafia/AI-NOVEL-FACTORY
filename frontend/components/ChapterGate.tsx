'use client';

import { useState } from 'react';
import { Lock, Check } from 'lucide-react';
import { PRICES } from '@/lib/stripe';

interface ChapterGateProps {
  chapterId: number;
  chapterNum: number;
  bookTitle: string;
}

export default function ChapterGate({ chapterId, chapterNum, bookTitle }: ChapterGateProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBuyChapter = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'chapter',
          chapterId,
          successUrl: `${window.location.href}?unlocked=1`,
          cancelUrl: window.location.href,
        }),
      });
      if (!res.ok) throw new Error('Failed to create checkout session');
      const { url } = await res.json();
      window.location.href = url;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Payment error. Please try again.');
      setLoading(false);
    }
  };

  const handleSubscribe = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'subscription',
          plan: 'monthly',
          successUrl: `${window.location.href}?subscribed=1`,
          cancelUrl: window.location.href,
        }),
      });
      if (!res.ok) throw new Error('Failed to create checkout session');
      const { url } = await res.json();
      window.location.href = url;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Payment error. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="relative my-8">
      {/* Blurred preview gradient */}
      <div className="h-24 bg-gradient-to-b from-transparent to-slate-900 absolute bottom-full left-0 right-0 pointer-events-none" />

      <div className="rounded-2xl bg-slate-800 border border-slate-600 p-8 text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="bg-slate-700 rounded-full p-4">
            <Lock size={28} className="text-amber-400" />
          </div>
        </div>

        <h3 className="text-white text-2xl font-bold mb-2">
          Chapter {chapterNum} is Locked
        </h3>
        <p className="text-slate-400 text-sm mb-6 max-w-sm mx-auto">
          Unlock this chapter of <em className="text-slate-200">&ldquo;{bookTitle}&rdquo;</em> with a one-time purchase, or get unlimited access with a subscription.
        </p>

        {error && (
          <p className="text-red-400 text-sm mb-4">{error}</p>
        )}

        {/* Options */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          {/* Buy chapter */}
          <button
            onClick={handleBuyChapter}
            disabled={loading}
            className="flex flex-col items-center bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-bold px-8 py-4 rounded-xl transition-colors"
          >
            <span className="text-lg">${PRICES.chapter.toFixed(2)}</span>
            <span className="text-xs font-normal">Buy this chapter</span>
          </button>

          {/* Subscribe */}
          <button
            onClick={handleSubscribe}
            disabled={loading}
            className="flex flex-col items-center bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white font-bold px-8 py-4 rounded-xl border border-slate-500 transition-colors group"
          >
            <span className="text-lg group-hover:text-amber-300">${PRICES.subscription_monthly.toFixed(2)}/mo</span>
            <span className="text-xs font-normal text-slate-400">Unlimited all books</span>
          </button>
        </div>

        {/* Benefits of subscription */}
        <div className="mt-6 flex flex-wrap justify-center gap-4 text-xs text-slate-400">
          {['All books & chapters', 'New chapters every 3 days', 'Cancel anytime'].map((b) => (
            <span key={b} className="flex items-center gap-1">
              <Check size={12} className="text-green-400" />
              {b}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
