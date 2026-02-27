'use client';

import Link from 'next/link';
import { useState } from 'react';
import { BookOpen, Menu, X, Users, Home, BookMarked } from 'lucide-react';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { href: '/', label: 'Home', icon: <Home size={16} /> },
    { href: '/books', label: 'Books', icon: <BookMarked size={16} /> },
    { href: '/authors', label: 'Authors', icon: <Users size={16} /> },
    { href: '/subscribe', label: 'Subscribe $9.99/mo', icon: <BookOpen size={16} />, highlight: true },
  ];

  return (
    <nav className="bg-slate-900 border-b border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-white">
            <BookOpen className="text-amber-400" size={24} />
            <span className="hidden sm:inline">Novel<span className="text-amber-400">Factory</span></span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={
                  l.highlight
                    ? 'flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-4 py-2 rounded-full text-sm transition-colors'
                    : 'flex items-center gap-1.5 text-slate-300 hover:text-white text-sm transition-colors'
                }
              >
                {l.icon}
                {l.label}
              </Link>
            ))}
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="md:hidden text-slate-300 hover:text-white p-2"
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="md:hidden bg-slate-800 border-t border-slate-700 px-4 py-4 flex flex-col gap-3">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              className={
                l.highlight
                  ? 'flex items-center gap-2 bg-amber-500 text-slate-900 font-semibold px-4 py-2 rounded-full text-sm w-fit'
                  : 'flex items-center gap-2 text-slate-300 hover:text-white text-sm py-1'
              }
            >
              {l.icon}
              {l.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
