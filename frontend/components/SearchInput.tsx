'use client';

import { useRouter } from 'next/navigation';
import { useState, useRef } from 'react';
import { Search, X } from 'lucide-react';

interface SearchInputProps {
  defaultValue?: string;
  placeholder?: string;
  className?: string;
}

export default function SearchInput({
  defaultValue = '',
  placeholder = 'Search books, authors, genres…',
  className = '',
}: SearchInputProps) {
  const router = useRouter();
  const [value, setValue] = useState(defaultValue);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const submitSearch = (q: string) => {
    if (q.trim()) {
      router.push(`/search?q=${encodeURIComponent(q.trim())}`);
    } else {
      router.push('/search');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value;
    setValue(q);
    // debounce — navigate after 400ms idle
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => submitSearch(q), 400);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (timerRef.current) clearTimeout(timerRef.current);
    submitSearch(value);
  };

  return (
    <form onSubmit={handleSubmit} className={`relative max-w-2xl ${className}`}>
      <Search
        size={18}
        className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
      />
      <input
        type="text"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        className="w-full bg-slate-800 border border-slate-600 focus:border-amber-500 text-white placeholder-slate-400 rounded-xl pl-11 pr-10 py-3.5 text-base outline-none transition-colors"
        autoFocus
      />
      {value && (
        <button
          type="button"
          onClick={() => { setValue(''); router.push('/search'); }}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors p-1"
        >
          <X size={16} />
        </button>
      )}
    </form>
  );
}
