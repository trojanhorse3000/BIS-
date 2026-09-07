import { useState, useEffect } from 'react';
import { Loader2, AlertCircle, Info } from 'lucide-react';
import { getHUIDStandards } from '../services/api';
import type { HUIDItem } from '../types';

const FINENESS_COLORS: Record<string, string> = {
  '999': 'bg-yellow-100 text-yellow-800',
  '958': 'bg-amber-100 text-amber-800',
  '916': 'bg-orange-100 text-orange-800',
  '875': 'bg-yellow-50 text-yellow-700',
  '750': 'bg-orange-50 text-orange-700',
  '585': 'bg-rose-100 text-rose-700',
};

export default function HuidView() {
  const [items, setItems] = useState<HUIDItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHUIDStandards()
      .then(res => setItems(res.data))
      .catch(() => setError('Failed to load HUID reference data.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto page-anim">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ink mb-1">HUID Hallmarking Reference</h1>
        <p className="text-muted text-sm">Gold fineness grades, carving marks & verification guidelines under IS 2112:2016</p>
      </div>

      {/* Info card */}
      <div className="bg-surface border border-primary/10 rounded-xl px-4 py-3 mb-6 flex items-start gap-3">
        <Info className="text-primary flex-shrink-0 mt-0.5" size={16} />
        <p className="text-sm text-ink-light">
          The <strong>HUID (Hallmarking Unique Identification Number)</strong> scheme uniquely identifies each
          hallmarked gold article. Every piece carries a 6-digit alphanumeric code linked to the assaying &
          hallmarking centre, gold fineness, and manufacturer.
        </p>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted">
          <Loader2 className="animate-spin mb-3" size={24} />
          <p className="text-sm">Loading hallmarking data…</p>
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-500 bg-red-50 rounded-xl px-4 py-3 text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(item => {
            const colorClass = FINENESS_COLORS[item.purity_percentage ?? ''] || 'bg-gray-100 text-gray-700';
            return (
              <div
                key={item.id}
                className="bg-white rounded-xl border border-gray-100 p-4 hover:shadow-md hover:shadow-primary/5 transition-all duration-200"
              >
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className={`px-3 py-1 rounded-lg text-sm font-bold ${colorClass}`}>
                        {item.caratage ?? `${item.gold_fineness_grade}K`}
                      </span>
                      <span className="text-xs font-mono text-muted bg-gray-100 px-2 py-0.5 rounded">
                        {item.purity_percentage ?? item.gold_fineness_grade ?? '—'}% purity
                      </span>
                    </div>
                    <p className="text-sm text-ink">{item.description}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-xs text-muted mb-1">Carving Mark</div>
                    <div className="font-mono text-sm font-semibold text-primary bg-primary/5 px-3 py-1.5 rounded-lg">
                      {item.carving_mark}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
