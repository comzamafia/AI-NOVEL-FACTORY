import { Users } from 'lucide-react';
import AuthorCard from '@/components/AuthorCard';
import { getPenNames } from '@/lib/api';

export const revalidate = 120;

export const metadata = {
  title: 'Authors — NovelFactory',
  description: 'Meet the AI pen names behind NovelFactory novels.',
};

export default async function AuthorsPage() {
  const data = await getPenNames().catch(() => ({ results: [], count: 0 }));
  const authors = data.results;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-10">
        <h1 className="text-4xl font-extrabold text-white mb-2 flex items-center gap-3">
          <Users className="text-amber-400" size={36} />
          Our Authors
        </h1>
        <p className="text-slate-400">
          {authors.length > 0
            ? `${authors.length} AI pen name${authors.length !== 1 ? 's' : ''}, each with a distinct voice and genre`
            : 'Meet our growing team of AI storytellers'}
        </p>
      </div>

      {authors.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {authors.map((author) => (
            <AuthorCard key={author.id} author={author} />
          ))}
        </div>
      ) : (
        <div className="text-center py-24 text-slate-500">
          <Users size={56} className="mx-auto mb-4 opacity-40" />
          <p className="text-xl">No authors yet.</p>
        </div>
      )}
    </div>
  );
}
