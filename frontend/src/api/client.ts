import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface DataRange {
  min_date: string;
  max_date: string;
}

export interface OverviewData {
  total_events: number;
  unique_users: number;
  total_revenue: number;
  conversion_rate: number;
  avg_order_value: number;
  total_views: number;
  total_carts: number;
  total_purchases: number;
  daily_trend: Array<{
    date: string;
    views: number;
    carts: number;
    purchases: number;
    revenue: number;
  }>;
}

export interface FunnelData {
  stages: Array<{ stage: string; count: number; rate: number }>;
  categories: string[];
  view_to_cart_rate: number;
  cart_to_purchase_rate: number;
  overall_conversion: number;
  top_abandonment: Array<{
    category: string;
    abandonment_rate: number;
    abandoned_carts: number;
  }>;
}

export interface Product {
  product_id: number;
  category: string;
  brand: string;
  price: number;
  views: number;
  carts: number;
  purchases: number;
  revenue: number;
}

export interface Brand {
  brand: string;
  views: number;
  carts: number;
  purchases: number;
  revenue: number;
}

export interface Category {
  category: string;
  views: number;
  carts: number;
  purchases: number;
  revenue: number;
}

export interface LiveSession {
  session_id: string;
  user_id: number;
  last_event_time: string;
  event_count: number;
  has_cart: boolean;
  has_purchase: boolean;
  last_category: string;
}

// ---- Formatters ----
export function fmtNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return new Intl.NumberFormat('en-US').format(n);
}

export function fmtCurrency(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(n);
}

export function fmtPercent(n: number): string {
  return `${(n * 100).toFixed(2)}%`;
}

// ---- API calls ----
export const getDataRange = (): Promise<DataRange> =>
  api.get('/data-range').then((r) => r.data);

export const getOverview = (startDate: string, endDate: string): Promise<OverviewData> =>
  api.get('/overview', { params: { start_date: startDate, end_date: endDate } }).then((r) => r.data);

export const getFunnel = (
  startDate: string,
  endDate: string,
  category = 'all'
): Promise<FunnelData> =>
  api
    .get('/funnel', { params: { start_date: startDate, end_date: endDate, category } })
    .then((r) => r.data);

export const getProducts = (
  startDate: string,
  endDate: string,
  limit = 20
): Promise<{ products: Product[] }> =>
  api
    .get('/products', { params: { start_date: startDate, end_date: endDate, limit } })
    .then((r) => r.data);

export const getBrands = (
  startDate: string,
  endDate: string,
  limit = 20
): Promise<{ brands: Brand[] }> =>
  api
    .get('/brands', { params: { start_date: startDate, end_date: endDate, limit } })
    .then((r) => r.data);

export const getCategories = (
  startDate: string,
  endDate: string
): Promise<{ categories: Category[] }> =>
  api
    .get('/categories', { params: { start_date: startDate, end_date: endDate } })
    .then((r) => r.data);

export const getLiveEvents = (limit = 50): Promise<LiveSession[]> =>
  api.get('/live/events', { params: { limit } }).then((r) => r.data);
