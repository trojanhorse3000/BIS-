import { useState, useEffect, useCallback } from 'react';
import {
  PieChart, Pie, Tooltip, Cell, Legend, ResponsiveContainer,
} from 'recharts';
import {
  Database, MessageSquare, FileText, ShieldCheck, Clock, Activity,
  Loader2, AlertCircle, TrendingUp,
} from 'lucide-react';
import { getStats, getHistory } from '../services/api';
import type { StatsData, HistoryEntry } from '../types';

const INTENT_COLORS = ['#7C3AED', '#06B6D4', '#F59E0B', '#10B981', '#EF4444', '#6B7280'];

function StatCardSkeleton() {
  return (
    <div className="bg-bg-elevated rounded-xl border border-border p-4">
      <div className="w-8 h-8 rounded-lg bg-primary/10 skeleton mb-3" />
      <div className="h-5 w-12 skeleton mb-2" />
      <div className="h-3 w-20 skeleton" />
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="bg-bg-elevated rounded-xl border border-border p-5">
      <div className="h-4 w-32 skeleton mb-4" />
      <div className="h-60 skeleton" />
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="bg-bg-elevated rounded-xl border border-border p-5">
      <div className="h-4 w-28 skeleton mb-4" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full skeleton flex-shrink-0" />
            <div className="flex-1">
              <div className="h-3 w-3/4 skeleton mb-1.5" />
              <div className="h-2.5 w-1/2 skeleton" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardView() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [recent, setRecent] = useState<HistoryEntry[]>([]);
  const [intentData, setIntentData] = useState<{ name: string; value: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, historyRes] = await Promise.all([getStats(), getHistory(20)]);
      setStats(statsRes.data);
      setRecent(historyRes.entries);

      const intentMap: Record<string, number> = {};
      historyRes.entries.forEach(e => {
        const key = e.intent.replace(/_/g, ' ');
        intentMap[key] = (intentMap[key] || 0) + 1;
      });
      setIntentData(Object.entries(intentMap).map(([name, value]) => ({ name, value })));
    } catch {
      setError('Failed to load dashboard data. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full px-4">
        <div className="flex items-center gap-2 text-red-600 bg-red-50 rounded-xl px-4 py-3 text-sm max-w-md">
          <AlertCircle size={16} /> {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto page-anim">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ink mb-1">Dashboard</h1>
          <p className="text-muted text-sm">Query analytics & system overview</p>
        </div>
        <button
          onClick={loadData}
          className="p-2 rounded-lg border border-border hover:border-primary/30 hover:bg-bg-hover transition-all cursor-pointer"
          aria-label="Refresh data"
        >
          {loading ? (
            <Loader2 size={16} className="text-muted animate-spin" />
          ) : (
            <TrendingUp size={16} className="text-muted" />
          )}
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <StatCardSkeleton key={i} />)
          : [
              { icon: <MessageSquare size={18} />, label: 'Total Queries', value: stats?.total_queries ?? 0, color: 'text-primary', bg: 'bg-primary/10' },
              { icon: <FileText size={18} />, label: 'Standard Lookups', value: stats?.total_standard_queries ?? 0, color: 'text-blue-700', bg: 'bg-blue-50' },
              { icon: <ShieldCheck size={18} />, label: 'HUID Queries', value: stats?.total_huid_queries ?? 0, color: 'text-amber-700', bg: 'bg-amber-50' },
              { icon: <Clock size={18} />, label: 'Avg Latency', value: `${(stats?.avg_latency_ms ?? 0).toFixed(0)}ms`, color: 'text-accent', bg: 'bg-accent/10' },
              { icon: <Activity size={18} />, label: 'Refusals', value: stats?.total_refusals ?? 0, color: 'text-red-600', bg: 'bg-red-50' },
              { icon: <Database size={18} />, label: 'Latest Query', value: stats?.latest_query_at
                ? new Date(stats.latest_query_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : '—', color: 'text-green-700', bg: 'bg-green-50' },
            ].map((card, i) => (
              <div key={i} className="bg-bg-elevated rounded-xl border border-border p-4 hover:shadow-md hover:shadow-primary/10 transition-all">
                <div className={`w-8 h-8 rounded-lg ${card.bg} ${card.color} flex items-center justify-center mb-3`}>
                  {card.icon}
                </div>
                <div className="text-xl font-bold text-ink">{card.value}</div>
                <div className="text-xs text-muted mt-0.5">{card.label}</div>
              </div>
            ))
        }
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Intent distribution */}
        {loading ? (
          <ChartSkeleton />
        ) : (
          <div className="bg-bg-elevated rounded-xl border border-border p-5">
            <h3 className="text-sm font-semibold text-ink mb-4">Intent Distribution</h3>
            {intentData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={intentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {intentData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={INTENT_COLORS[index % INTENT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '12px', background: 'var(--color-bg-elevated)', color: 'var(--color-ink)' }}
                    formatter={(value, name) => [value as number, name as string]}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-60 flex items-center justify-center text-muted text-sm">No data yet</div>
            )}
          </div>
        )}

        {/* Recent queries */}
        {loading ? (
          <ListSkeleton />
        ) : (
          <div className="bg-bg-elevated rounded-xl border border-border p-5">
            <h3 className="text-sm font-semibold text-ink mb-4">Recent Queries</h3>
            {recent.length > 0 ? (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {recent.map((entry, idx) => (
                  <div key={entry.id ?? `pending-${entry.timestamp}-${idx}`} className="flex items-start gap-3 p-2 rounded-lg hover:bg-surface transition-colors cursor-default">
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                      entry.is_refusal ? 'bg-red-500' : entry.verified ? 'bg-green-500' : 'bg-primary/40'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-ink truncate">{entry.query}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-muted">{entry.intent.replace(/_/g, ' ')}</span>
                        <span className="text-xs text-muted">·</span>
                        <span className="text-xs text-muted">{entry.latency_ms.toFixed(0)}ms</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-60 flex items-center justify-center text-muted text-sm">No queries yet</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
