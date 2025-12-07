import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types matching FastAPI backend
export interface QueryRequest {
  question: string;
  mode?: 'hybrid' | 'graph' | 'vector';
  limit?: number;
}

export interface PaperResult {
  pmid: string;
  title: string;
  abstract?: string;
  publication_date?: string;
  authors: string[];
  genes: string[];
  mesh_terms: string[];
  score?: number;
}

export interface QueryResponse {
  question: string;
  answer: string;
  papers: PaperResult[];
  authors: any[];
  genes: any[];
  graph_data?: any;
  execution_time_ms: number;
  query_type: string;
}

export interface SystemHealth {
  status: string;
  neo4j_connected: boolean;
  qdrant_connected: boolean;
  api_online: boolean;
  prefect_running: boolean;
  rate_limit_percent: number;
  last_update: string;
  uptime_seconds: number;
}

export interface StatsResponse {
  total_papers: number;
  total_genes: number;
  total_authors: number;
  total_institutions: number;
  total_mesh_terms: number;
  last_updated?: string;
}

// API Functions
export const api = {
  // Query endpoints
  async query(data: QueryRequest): Promise<QueryResponse> {
    const response = await apiClient.post('/api/query/', data);
    return response.data;
  },

  async getExampleQueries(): Promise<string[]> {
    const response = await apiClient.get('/api/query/examples');
    return response.data;
  },

  // Health and Stats
  async getHealth(): Promise<SystemHealth> {
    const response = await apiClient.get('/api/health/');
    return response.data;
  },

  async getStats(): Promise<StatsResponse> {
    const response = await apiClient.get('/api/stats/');
    return response.data;
  },

  // Search
  async search(query: string, limit = 10): Promise<any> {
    const response = await apiClient.post('/api/search/', { query, limit });
    return response.data;
  },

  // Graph exploration
  async exploreGraph(nodeId: string, nodeType: string, depth = 1): Promise<any> {
    const response = await apiClient.post('/api/graph/explore', {
      node_id: nodeId,
      node_type: nodeType,
      depth,
    });
    return response.data;
  },
};

export default api;
