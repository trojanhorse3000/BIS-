import { useState, useEffect, useCallback } from 'react';
import { Search, ChevronLeft, ChevronRight, Loader2, AlertCircle } from 'lucide-react';
import { searchCrosswalk, listCrosswalk } from '../services/api';
import type { CrosswalkItem } from '../types';

export default function CrosswalkView() {
  const [items, setItems] = useState<CrosswalkItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  const fetchData = useCallback(async (p: number, q?: string) => {
    setLoading(true);
    setError(null);
    try {
      if (q) {
        const res = await searchCrosswalk(q, p);
        setItems(res.data.items);
        setTotal(res.data.total);
      } else {
        const res = await listCrosswalk(p);
        setItems(res.data.items);
        setTotal(res.data.total);
      }
    } catch {
      setError('Failed to load crosswalk data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setPage(1);
    fetchData(1, debouncedSearch);
  }, [debouncedSearch, fetchData]);

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto page-anim">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ink mb-1">QCO Crosswalk</h1>
        <p className="text-muted text-sm">Map products to mandatory Quality Control Orders</p>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by product, HS code, QCO number…"
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-ink placeholder:text-muted outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all"
          aria-label="Search crosswalk"
        />
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted">
          <Loader2 className="animate-spin mb-3" size={24} />
          <p className="text-sm">Loading crosswalk…</p>
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-500 bg-red-50 rounded-xl px-4 py-3 text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      ) : (
        <>
          <p className="text-xs text-muted mb-3">{total.toLocaleString()} entries</p>
          <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-surface border-b border-gray-100">
                    <th className="text-left px-4 py-2.5 font-semibold text-muted text-xs uppercase tracking-wider">IS Number</th>
                    <th className="text-left px-4 py-2.5 font-semibold text-muted text-xs uppercase tracking-wider">Product</th>
                    <th className="text-left px-4 py-2.5 font-semibold text-muted text-xs uppercase tracking-wider hidden sm:table-cell">QCO Number</th>
                    <th className="text-left px-4 py-2.5 font-semibold text-muted text-xs uppercase tracking-wider hidden md:table-cell">Scheme</th>
                    <th className="text-left px-4 py-2.5 font-semibold text-muted text-xs uppercase tracking-wider hidden lg:table-cell">Ministry</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(item => (
                    <tr key={item.id} className="border-b border-gray-50 hover:bg-surface/50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-primary">{item.is_number}</td>
                      <td className="px-4 py-3 text-ink max-w-[200px] truncate" title={item.product}>{item.product}</td>
                      <td className="px-4 py-3 font-mono text-xs text-muted hidden sm:table-cell">{item.qco_number}</td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-xs font-medium">
                          {item.scheme.split('(')[0].trim()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted hidden lg:table-cell">{item.ministry}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {items.length === 0 && (
              <div className="text-center py-12 text-muted text-sm">No crosswalk entries found.</div>
            )}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-xs text-muted">Page {page} of {totalPages}</p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => fetchData(page - 1, debouncedSearch)}
                  disabled={page <= 1 || loading}
                  className="p-2 rounded-lg border border-gray-200 hover:border-primary/30 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  aria-label="Previous page"
                >
                  <ChevronLeft size={16} />
                </button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let p = i + 1;
                  if (totalPages > 5) {
                    if (page <= 3) p = i + 1;
                    else if (page >= totalPages - 2) p = totalPages - 4 + i;
                    else p = page - 2 + i;
                  }
                  return (
                    <button
                      key={p}
                      onClick={() => fetchData(p, debouncedSearch)}
                      className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${
                        p === page ? 'bg-primary text-white' : 'border border-gray-200 hover:border-primary/30 text-muted'
                      }`}
                    >
                      {p}
                    </button>
                  );
                })}
                <button
                  onClick={() => fetchData(page + 1, debouncedSearch)}
                  disabled={page >= totalPages || loading}
                  className="p-2 rounded-lg border border-gray-200 hover:border-primary/30 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  aria-label="Next page"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
