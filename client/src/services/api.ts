import axios from 'axios';
import type {
  HistoryResponse,
  StatsResponse,
  HealthResponse,
  PaginatedResponse,
  StandardItem,
  CrosswalkItem,
  HUIDItem,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// ── Query ─────────────────────────────────────────────────────

export async function postQuery(query: string, lang = 'en') {
  const res = await api.post('/api/query', { query, lang, include_telemetry: true });
  return res.data;
}

// ── History ───────────────────────────────────────────────────

export async function getHistory(limit = 50, intent?: string): Promise<HistoryResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (intent) params.set('intent', intent);
  const res = await api.get(`/api/history?${params}`);
  return res.data;
}

// ── Stats ─────────────────────────────────────────────────────

export async function getStats(): Promise<StatsResponse> {
  const res = await api.get('/api/stats');
  return res.data;
}

// ── Health ────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthResponse> {
  const res = await api.get('/health');
  return res.data;
}

// ── Standards ─────────────────────────────────────────────────

export async function listStandards(
  page = 1,
  pageSize = 20,
  status?: string
): Promise<PaginatedResponse<StandardItem>> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (status) params.set('status', status);
  const res = await api.get(`/api/standards?${params}`);
  return res.data;
}

export async function searchStandards(
  q: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<StandardItem>> {
  const res = await api.get('/api/standards/search', {
    params: { q, page, page_size: pageSize },
  });
  return res.data;
}

// ── Crosswalk ─────────────────────────────────────────────────

export async function listCrosswalk(
  page = 1,
  pageSize = 20,
  scheme?: string
): Promise<PaginatedResponse<CrosswalkItem>> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (scheme) params.set('scheme', scheme);
  const res = await api.get(`/api/crosswalk?${params}`);
  return res.data;
}

export async function searchCrosswalk(
  q: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<CrosswalkItem>> {
  const res = await api.get('/api/crosswalk/search', {
    params: { q, page, page_size: pageSize },
  });
  return res.data;
}

// ── HUID ──────────────────────────────────────────────────────

export async function getHUIDStandards(): Promise<{ status: string; data: HUIDItem[] }> {
  const res = await api.get('/api/huid/standards');
  return res.data;
}

export default api;
