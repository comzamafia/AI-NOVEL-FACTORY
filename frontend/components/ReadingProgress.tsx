'use client';

import { useEffect, useState } from 'react';

export default function ReadingProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const update = () => {
      const article = document.getElementById('chapter-content');
      if (!article) return;

      const { top, height } = article.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const scrolled = Math.max(0, windowHeight - top);
      const pct = Math.min(100, (scrolled / height) * 100);
      setProgress(pct);
    };

    window.addEventListener('scroll', update, { passive: true });
    update();
    return () => window.removeEventListener('scroll', update);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 z-[60] h-0.5 bg-slate-700">
      <div
        className="h-full bg-amber-500 transition-all duration-100"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}
