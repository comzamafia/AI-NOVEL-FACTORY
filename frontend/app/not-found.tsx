import Link from 'next/link';
import { BookOpen, Home, Search } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="text-8xl font-extrabold text-slate-700 mb-4 select-none">404</div>
        <h1 className="text-3xl font-bold text-white mb-3">Page not found</h1>
        <p className="text-slate-400 mb-8 leading-relaxed">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-6 py-3 rounded-full transition-colors"
          >
            <Home size={16} />
            Go Home
          </Link>
          <Link
            href="/books"
            className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold px-6 py-3 rounded-full border border-slate-600 transition-colors"
          >
            <BookOpen size={16} />
            Browse Books
          </Link>
          <Link
            href="/search"
            className="flex items-center gap-2 text-slate-400 hover:text-white text-sm transition-colors"
          >
            <Search size={15} />
            Search
          </Link>
        </div>
      </div>
    </div>
  );
}
