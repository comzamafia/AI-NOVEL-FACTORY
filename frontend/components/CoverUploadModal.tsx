'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Upload, Loader2 } from 'lucide-react';
import { createCover, getCoverChoices } from '@/lib/api';
import type { BookCover, CoverChoices } from '@/types';

interface Props {
  bookId: number;
  onCreated: (cover: BookCover) => void;
  onClose: () => void;
}

export default function CoverUploadModal({ bookId, onCreated, onClose }: Props) {
  const [choices, setChoices] = useState<CoverChoices | null>(null);
  const [coverType, setCoverType] = useState<'ebook' | 'paperback'>('ebook');
  const [trimSize, setTrimSize] = useState('6x9');
  const [paperType, setPaperType] = useState('bw_white');
  const [pageCount, setPageCount] = useState('');
  const [versionNote, setVersionNote] = useState('');
  const [frontFile, setFrontFile] = useState<File | null>(null);
  const [fullFile, setFullFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getCoverChoices().then(setChoices).catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append('book', String(bookId));
      fd.append('cover_type', coverType);
      fd.append('version_note', versionNote);
      if (coverType === 'paperback') {
        fd.append('trim_size', trimSize);
        fd.append('paper_type', paperType);
        if (pageCount) fd.append('page_count', pageCount);
      }
      if (frontFile) fd.append('front_cover', frontFile);
      if (fullFile) fd.append('full_cover', fullFile);

      const cover = await createCover(fd);
      onCreated(cover);
      onClose();
    } catch (err: unknown) {
      // Try to extract DRF error message
      const anyErr = err as { response?: { data?: Record<string, unknown> } };
      const detail = anyErr?.response?.data;
      setError(detail ? JSON.stringify(detail) : 'Upload failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-700">
          <h2 className="text-white font-semibold text-lg flex items-center gap-2">
            <Upload size={18} className="text-amber-400" />
            Add New Cover Version
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Cover Type */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Cover Type</label>
            <div className="flex gap-2">
              {['ebook', 'paperback'].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setCoverType(t as 'ebook' | 'paperback')}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                    coverType === t
                      ? 'bg-amber-500 text-slate-900'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Paperback fields */}
          {coverType === 'paperback' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Trim Size</label>
                <select
                  value={trimSize}
                  onChange={(e) => setTrimSize(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  {(choices?.trim_sizes ?? []).map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Paper Type</label>
                <select
                  value={paperType}
                  onChange={(e) => setPaperType(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  {(choices?.paper_types ?? []).map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs text-slate-400 mb-1">Page Count</label>
                <input
                  type="number"
                  min={24}
                  max={828}
                  value={pageCount}
                  onChange={(e) => setPageCount(e.target.value)}
                  placeholder="e.g. 300"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>
            </div>
          )}

          {/* Version Note */}
          <div>
            <label className="block text-xs text-slate-400 mb-1">Version Note <span className="text-slate-600">(optional)</span></label>
            <textarea
              value={versionNote}
              onChange={(e) => setVersionNote(e.target.value)}
              rows={2}
              placeholder="e.g. Revised typography, darker background…"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
            />
          </div>

          {/* Front Cover Upload */}
          <FileDropZone
            label="Front Cover"
            hint={coverType === 'ebook' ? 'JPEG/PNG, 1600×2560 px recommended' : 'High-res JPEG/PNG of front cover'}
            file={frontFile}
            onFile={setFrontFile}
          />

          {/* Full Wrap (paperback) */}
          {coverType === 'paperback' && (
            <FileDropZone
              label="Full Wrap Cover"
              hint="PDF or PNG — front + spine + back, print-ready at 300 DPI"
              file={fullFile}
              onFile={setFullFile}
            />
          )}

          {error && (
            <p className="text-red-400 text-xs bg-red-900/20 rounded-lg p-3">{error}</p>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl bg-slate-700 text-slate-300 text-sm font-medium hover:bg-slate-600 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 py-2.5 rounded-xl bg-amber-500 text-slate-900 text-sm font-semibold hover:bg-amber-400 disabled:opacity-60 transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? <><Loader2 size={16} className="animate-spin" /> Uploading…</> : 'Upload Cover'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function FileDropZone({
  label, hint, file, onFile,
}: {
  label: string;
  hint: string;
  file: File | null;
  onFile: (f: File) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div>
      <label className="block text-xs text-slate-400 mb-1">{label}</label>
      <div
        className={`border-2 border-dashed rounded-xl px-4 py-5 text-center cursor-pointer transition-colors ${
          file ? 'border-amber-500 bg-amber-900/10' : 'border-slate-600 hover:border-slate-500'
        }`}
        onClick={() => ref.current?.click()}
      >
        {file ? (
          <p className="text-amber-400 text-sm font-medium truncate">{file.name}</p>
        ) : (
          <>
            <Upload size={20} className="mx-auto text-slate-500 mb-1" />
            <p className="text-slate-400 text-xs">{hint}</p>
          </>
        )}
      </div>
      <input
        ref={ref}
        type="file"
        accept="image/jpeg,image/png,application/pdf"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
      />
    </div>
  );
}
