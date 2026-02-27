'use client';

import Image from 'next/image';
import { CheckCircle, BookOpen, Star, Trash2, Maximize2 } from 'lucide-react';
import { useState } from 'react';
import type { BookCover } from '@/types';
import { activateCover, deleteCover } from '@/lib/api';

interface Props {
  cover: BookCover;
  onActivate: (cover: BookCover) => void;
  onDelete: (id: number) => void;
}

export default function CoverCard({ cover, onActivate, onDelete }: Props) {
  const [busy, setBusy] = useState(false);
  const [lightbox, setLightbox] = useState(false);

  const imgUrl = cover.front_cover_url;
  const typeLabel = cover.cover_type_display;
  const isEbook = cover.cover_type === 'ebook';

  async function handleActivate() {
    setBusy(true);
    try {
      const updated = await activateCover(cover.id);
      onActivate(updated);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete cover v${cover.version_number}?`)) return;
    setBusy(true);
    try {
      await deleteCover(cover.id);
      onDelete(cover.id);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div
        className={`relative bg-slate-800 rounded-2xl border transition-shadow overflow-hidden ${
          cover.is_active
            ? 'border-amber-500 shadow-lg shadow-amber-900/20'
            : 'border-slate-700 hover:border-slate-600'
        }`}
      >
        {/* Active Badge */}
        {cover.is_active && (
          <div className="absolute top-2 left-2 z-10 flex items-center gap-1 bg-amber-500 text-slate-900 text-xs font-bold px-2 py-1 rounded-full">
            <Star size={10} fill="currentColor" /> Active
          </div>
        )}

        {/* Cover image */}
        <div
          className="relative bg-slate-900 cursor-pointer group"
          style={{ aspectRatio: isEbook ? '10/16' : '16/10' }}
          onClick={() => imgUrl && setLightbox(true)}
        >
          {imgUrl ? (
            <>
              <Image src={imgUrl} alt={`Cover v${cover.version_number}`} fill className="object-cover" />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                <Maximize2 size={24} className="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600 gap-2">
              <BookOpen size={32} />
              <p className="text-xs">No image uploaded</p>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className="text-xs text-amber-400 font-medium uppercase tracking-wide">{typeLabel}</span>
              <p className="text-white font-semibold">Version {cover.version_number}</p>
            </div>
            <div className="flex gap-1">
              {!cover.is_active && (
                <button
                  onClick={handleActivate}
                  disabled={busy}
                  title="Set as active"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-700 transition-colors disabled:opacity-50"
                >
                  <CheckCircle size={16} />
                </button>
              )}
              <button
                onClick={handleDelete}
                disabled={busy}
                title="Delete version"
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-700 transition-colors disabled:opacity-50"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>

          {/* Dims */}
          <div className="space-y-1">
            {cover.cover_type === 'ebook' && cover.ebook_width_px && (
              <DimRow label="Size" val={`${cover.ebook_width_px} × ${cover.ebook_height_px} px`} />
            )}
            {cover.cover_type === 'paperback' && (
              <>
                {cover.trim_size && <DimRow label="Trim" val={cover.trim_size_display || cover.trim_size} />}
                {cover.spine_width_in && (
                  <DimRow label="Spine" val={`${parseFloat(cover.spine_width_in).toFixed(4)}"`} />
                )}
                {cover.total_width_px && (
                  <DimRow label="Canvas" val={`${cover.total_width_px} × ${cover.total_height_px} px`} />
                )}
                {cover.page_count && <DimRow label="Pages" val={String(cover.page_count)} />}
              </>
            )}
          </div>

          {cover.version_note && (
            <p className="text-xs text-slate-400 italic line-clamp-2">{cover.version_note}</p>
          )}

          <p className="text-xs text-slate-600">
            {new Date(cover.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
          </p>
        </div>
      </div>

      {/* Lightbox */}
      {lightbox && imgUrl && (
        <div
          className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4"
          onClick={() => setLightbox(false)}
        >
          <div className="relative max-w-2xl max-h-[90vh]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imgUrl} alt="" className="max-h-[90vh] max-w-full object-contain rounded-xl" />
            <button
              onClick={() => setLightbox(false)}
              className="absolute top-2 right-2 text-white bg-black/50 rounded-full p-1 hover:bg-black"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function DimRow({ label, val }: { label: string; val: string }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-300 font-mono">{val}</span>
    </div>
  );
}
