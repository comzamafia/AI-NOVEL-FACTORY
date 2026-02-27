import Image from 'next/image';
import Link from 'next/link';
import { Star, ExternalLink } from 'lucide-react';
import type { Book } from '@/types';
import { formatPrice } from '@/lib/utils';
import { buildCoverUrl } from '@/lib/api';

interface BookCardProps {
  book: Book;
  size?: 'sm' | 'md' | 'lg';
}

export default function BookCard({ book, size = 'md' }: BookCardProps) {
  const coverUrl = buildCoverUrl(book);
  const penName = typeof book.pen_name === 'object' ? book.pen_name : null;
  const price = book.current_price_usd;

  const cardSizes = {
    sm: 'w-36',
    md: 'w-48',
    lg: 'w-56',
  };

  const imgSizes = {
    sm: { w: 144, h: 216 },
    md: { w: 192, h: 288 },
    lg: { w: 224, h: 336 },
  };

  const { w, h } = imgSizes[size];

  return (
    <Link
      href={`/books/${book.id}`}
      className={`${cardSizes[size]} group flex flex-col rounded-xl overflow-hidden bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-amber-500 transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-amber-500/10`}
    >
      {/* Cover image */}
      <div className="relative overflow-hidden" style={{ height: h }}>
        <Image
          src={coverUrl}
          alt={book.title}
          width={w}
          height={h}
          className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300"
          unoptimized
        />
        {price !== undefined && price !== null && (
          <span className="absolute top-2 right-2 bg-amber-500 text-slate-900 text-xs font-bold px-2 py-0.5 rounded-full">
            {price === 0 ? 'FREE' : formatPrice(price)}
          </span>
        )}
      </div>

      {/* Info */}
      <div className="p-3 flex flex-col gap-1 flex-1">
        <h3 className="text-white text-sm font-semibold leading-snug line-clamp-2 group-hover:text-amber-300 transition-colors">
          {book.title}
        </h3>

        {penName && (
          <p className="text-slate-400 text-xs">{penName.name}</p>
        )}

        {/* Rating */}
        {book.avg_rating !== undefined && book.avg_rating !== null && (
          <div className="flex items-center gap-1 mt-auto pt-1">
            <Star size={12} className="text-amber-400 fill-amber-400" />
            <span className="text-amber-400 text-xs font-medium">{book.avg_rating.toFixed(1)}</span>
            {book.review_count !== undefined && (
              <span className="text-slate-500 text-xs">({book.review_count})</span>
            )}
          </div>
        )}

        {/* Amazon link */}
        {book.amazon_url && (
          <a
            href={book.amazon_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-amber-400 hover:text-amber-300 text-xs mt-1"
          >
            <ExternalLink size={11} />
            Amazon
          </a>
        )}
      </div>
    </Link>
  );
}
