import { ExternalLink, Zap } from 'lucide-react';

interface UpsellBannerProps {
  bookTitle: string;
  amazonUrl?: string;
  price?: number;
}

export default function UpsellBanner({ bookTitle, amazonUrl, price = 3.99 }: UpsellBannerProps) {
  return (
    <div className="my-8 rounded-2xl bg-gradient-to-r from-amber-500/20 via-amber-400/10 to-amber-500/20 border border-amber-500/40 p-5 text-center">
      <div className="flex items-center justify-center gap-2 mb-2">
        <Zap size={18} className="text-amber-400 fill-amber-400" />
        <span className="text-amber-300 font-bold text-sm uppercase tracking-wider">Read Faster</span>
        <Zap size={18} className="text-amber-400 fill-amber-400" />
      </div>

      <p className="text-white font-semibold text-lg leading-snug mb-1">
        Get the complete <em className="text-amber-300">&ldquo;{bookTitle}&rdquo;</em>
      </p>
      <p className="text-slate-300 text-sm mb-4">
        Don&apos;t wait for new chapters — own the full book on Amazon for just{' '}
        <span className="text-amber-400 font-bold">${price.toFixed(2)}</span>
      </p>

      {amazonUrl ? (
        <a
          href={amazonUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-6 py-2.5 rounded-full transition-colors"
        >
          <ExternalLink size={15} />
          Buy on Amazon ${price.toFixed(2)}
        </a>
      ) : (
        <span className="inline-flex items-center gap-2 bg-slate-700 text-slate-400 px-6 py-2.5 rounded-full text-sm">
          Coming soon on Amazon
        </span>
      )}
    </div>
  );
}
