'use client';

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useState, useRef } from 'react';
import { BookOpen, Menu, X, Users, Home, BookMarked, Search, BarChart3, UserCog, BookPlus, TrendingUp } from 'lucide-react';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchVal, setSearchVal] = useState('');
  const router = useRouter();
  const pathname = usePathname();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const navLinks = [
    { href: '/',          label: 'Home',      icon: <Home size={15} /> },
    { href: '/books',     label: 'Books',     icon: <BookMarked size={15} /> },
    { href: '/authors',   label: 'Authors',   icon: <Users size={15} /> },
    { href: '/dashboard', label: 'Dashboard', icon: <BarChart3 size={15} /> },
    { href: '/pen-names', label: 'Pen Names', icon: <UserCog size={15} /> },
    { href: '/books/new', label: 'New Book',  icon: <BookPlus size={15} /> },
    { href: '/analytics',  label: 'Analytics',  icon: <TrendingUp size={15} /> },
  ];

  const handleSearch = (q: string) => {
    setSearchVal(q);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      if (q.trim()) router.push(`/search?q=${encodeURIComponent(q.trim())}`);
    }, 400);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (timerRef.current) clearTimeout(timerRef.current);
    if (searchVal.trim()) router.push(`/search?q=${encodeURIComponent(searchVal.trim())}`);
  };

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  return (
    <nav className="bg-slate-900 border-b border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-white flex-shrink-0">
            <BookOpen className="text-amber-400" size={22} />
            <span className="hidden sm:inline">
              Novel<span className="text-amber-400">Factory</span>
            </span>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive(l.href)
                    ? 'text-white bg-slate-800'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                {l.icon}
                {l.label}
              </Link>
            ))}
          </div>

          {/* Desktop search bar */}
          <form onSubmit={handleSearchSubmit} className="hidden md:flex flex-1 max-w-sm relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            <input
              type="text"
              value={searchVal}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search books, authors…"
              className="w-full bg-slate-800 border border-slate-700 focus:border-amber-500 text-white placeholder-slate-500 rounded-lg pl-9 pr-3 py-2 text-sm outline-none transition-colors"
            />
          </form>

          {/* Right side */}
          <div className="flex items-center gap-2">
            <Link
              href="/subscribe"
              className="hidden md:flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2 rounded-full text-sm transition-colors"
            >
              Subscribe $9.99/mo
            </Link>
            <button
              onClick={() => setSearchOpen((o) => !o)}
              className="md:hidden text-slate-300 hover:text-white p-2 rounded-lg hover:bg-slate-800"
              aria-label="Search"
            >
              <Search size={20} />
            </button>
            <button
              onClick={() => setMenuOpen((o) => !o)}
              className="md:hidden text-slate-300 hover:text-white p-2 rounded-lg hover:bg-slate-800"
              aria-label="Toggle menu"
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile search bar */}
        {searchOpen && (
          <div className="md:hidden pb-3">
            <form onSubmit={handleSearchSubmit} className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                type="text"
                value={searchVal}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search books, authors…"
                autoFocus
                className="w-full bg-slate-800 border border-slate-600 focus:border-amber-500 text-white placeholder-slate-500 rounded-xl pl-9 pr-3 py-3 text-sm outline-none transition-colors"
              />
            </form>
          </div>
        )}
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <div className="md:hidden bg-slate-800 border-t border-slate-700 px-4 py-4 flex flex-col gap-1">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive(l.href)
                  ? 'text-white bg-slate-700'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              {l.icon}
              {l.label}
            </Link>
          ))}
          <Link
            href="/subscribe"
            onClick={() => setMenuOpen(false)}
            className="flex items-center gap-2 mt-2 bg-amber-500 text-slate-900 font-semibold px-4 py-2.5 rounded-full text-sm w-fit"
          >
            <BookOpen size={15} />
            Subscribe $9.99/mo
          </Link>
        </div>
      )}
    </nav>
  );
}
