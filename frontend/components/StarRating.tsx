import { Star } from 'lucide-react';

interface StarRatingProps {
  rating: number;
  count?: number;
  className?: string;
}

export default function StarRating({ rating, count, className = '' }: StarRatingProps) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {Array.from({ length: full }).map((_, i) => (
        <Star key={`f${i}`} size={14} className="text-amber-400 fill-amber-400" />
      ))}
      {half && (
        <span className="text-amber-400 text-sm leading-none">½</span>
      )}
      {Array.from({ length: empty }).map((_, i) => (
        <Star key={`e${i}`} size={14} className="text-slate-600" />
      ))}
      <span className="text-amber-400 text-sm font-semibold ml-1">{rating.toFixed(1)}</span>
      {count !== undefined && (
        <span className="text-slate-400 text-sm">({count.toLocaleString()})</span>
      )}
    </div>
  );
}
