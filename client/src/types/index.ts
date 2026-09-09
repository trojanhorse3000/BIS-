export interface EntityData {
  is_numbers: string[];
  huid_codes: string[];
  hs_codes: string[];
  product_terms: string[];
  search_keywords: string[];
  detected_input_lang: string;
  requested_output_lang: string;
  is_hindi: boolean;
}

export interface IntentData {
  intent: string;
  confidence: number;
  primary_target: string | null;
  reason: string | null;
}

export interface VectorResult {
  id: string;
  text: string;
  metadata: Record<string, unknown>;
  similarity_score: number;
}

export interface Citation {
  is_number: string;
  product: string;
  title: string;
  scheme: string;
  source_url: string;
  score: number;
}

export interface QueryResponse {
  status: string;
  query: string;
  cleaned_query: string;
  entities: EntityData;
  intent: IntentData;
  retrieved: {
    structured_results: Record<string, unknown>[];
    vector_results: VectorResult[];
    additional_count: number;
    context_type: string;
  };
  answer: string;
  citations: Citation[];
  source: string;
  verified: boolean;
  is_refusal: boolean;
  latency_ms: number;
}

export interface HistoryEntry {
  id: number | null;
  query: string;
  intent: string;
  source: string;
  verified: boolean;
  is_refusal: boolean;
  latency_ms: number;
  timestamp: string;
}

export interface HistoryResponse {
  status: string;
  total: number;
  entries: HistoryEntry[];
}

export interface StatsData {
  total_queries: number;
  total_huid_queries: number;
  total_standard_queries: number;
  total_refusals: number;
  avg_latency_ms: number;
  latest_query_at: string | null;
}

export interface StatsResponse {
  status: string;
  data: StatsData;
}

export interface HealthResponse {
  status: string;
  message: string;
  version: string;
  components: Record<string, string>;
}

// ── Browser data types ────────────────────────────────────────

export interface StandardItem {
  id: number;
  is_number: string;
  title: string;
  status: string;
  technical_committee: string;
  description?: string;
  published_date?: string;
}

export interface PaginatedResponse<T> {
  status: string;
  data: {
    items: T[];
    total: number;
    page: number;
    page_size: number;
  };
}

export interface CrosswalkItem {
  id: number;
  is_number: string;
  product: string;
  product_category: string;
  qco_number: string;
  scheme: string;
  notification_date: string;
  ministry: string;
}

export interface HUIDItem {
  id: number;
  caratage: string;
  gold_fineness_grade: string | null;
  purity_percentage: string | null;
  carving_mark: string;
  description: string | null;
}

// ── Chat message type (local) ────────────────────────────────

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: IntentData;
  citations?: Citation[];
  verified?: boolean;
  latency_ms?: number;
  timestamp: Date;
  isStreaming?: boolean;
}
