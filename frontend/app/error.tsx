'use client';

import { useEffect } from 'react';
import { RefreshCw, Home } from 'lucide-react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[Global Error Boundary]', error);
  }, [error]);

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="text-7xl mb-5 select-none">⚠️</div>
        <h1 className="text-3xl font-bold text-white mb-3">Something went wrong</h1>
        <p className="text-slate-400 mb-2 leading-relaxed">
          An unexpected error occurred. This has been logged automatically.
        </p>
        {error?.digest && (
          <p className="text-xs text-slate-600 mb-6 font-mono">
            Error ID: {error.digest}
          </p>
        )}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={reset}
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-6 py-3 rounded-full transition-colors"
          >
            <RefreshCw size={16} />
            Try Again
          </button>
          <Link
            href="/"
            className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold px-6 py-3 rounded-full border border-slate-600 transition-colors"
          >
            <Home size={16} />
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
