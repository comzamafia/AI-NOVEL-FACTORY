import Image from 'next/image';
import Link from 'next/link';
import { BookOpen } from 'lucide-react';
import type { PenName } from '@/types';
import { truncate } from '@/lib/utils';
import { buildAvatarUrl } from '@/lib/api';

interface AuthorCardProps {
  author: PenName;
}

export default function AuthorCard({ author }: AuthorCardProps) {
  const avatarUrl = buildAvatarUrl(author);

  return (
    <Link
      href={`/authors/${author.id}`}
      className="group flex flex-col items-center text-center p-6 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-amber-500 transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-amber-500/10"
    >
      {/* Avatar */}
      <div className="relative mb-4">
        <Image
          src={avatarUrl}
          alt={author.name}
          width={96}
          height={96}
          className="rounded-full object-cover border-4 border-slate-600 group-hover:border-amber-500 transition-colors"
          unoptimized
        />
      </div>

      {/* Name */}
      <h3 className="text-white font-bold text-lg group-hover:text-amber-300 transition-colors">
        {author.name}
      </h3>

      {/* Genre badge */}
      {author.niche_genre && (
        <span className="mt-1 text-xs bg-slate-700 text-slate-300 px-3 py-0.5 rounded-full">
          {author.niche_genre}
        </span>
      )}

      {/* Bio */}
      {author.bio && (
        <p className="mt-3 text-slate-400 text-sm leading-relaxed line-clamp-3">
          {truncate(author.bio, 120)}
        </p>
      )}

      {/* Book count */}
      {(author.book_count ?? 0) > 0 && (
        <div className="flex items-center gap-1.5 mt-4 text-amber-400 text-sm font-medium">
          <BookOpen size={14} />
          {author.book_count} book{author.book_count !== 1 ? 's' : ''}
        </div>
      )}
    </Link>
  );
}
