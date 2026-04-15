import { useEffect, useState, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import {
  getDataRange,
  getProducts,
  getBrands,
  getCategories,
  fmtNum,
  fmtCurrency,
  type Product,
  type Brand,
  type Category,
} from '../api/client';

function getLast30Days(maxDate: string) {
  const end = new Date(maxDate);
  const start = new Date(end);
  start.setDate(start.getDate() - 29);
  return { end: end.toISOString().slice(0, 10), start: start.toISOString().slice(0, 10) };
}

const PIE_COLORS = [
  '#3b82f6', '#f97316', '#22c55e', '#a855f7', '#ec4899',
  '#14b8a6', '#f59e0b', '#ef4444', '#84cc16', '#06b6d4',
];

interface TooltipPayloadEntry {
  name: string;
  value: number;
  payload: { category: string; revenue: number };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const { category, revenue } = payload[0].payload;
  return (
    <div style={{
      backgroundColor: '#1e293b',
      border: '1px solid #475569',
      borderRadius: 8,
      padding: '8px 12px',
    }}>
      <p style={{ color: '#f1f5f9', fontWeight: 600, marginBottom: 4 }}>{category || '—'}</p>
      <p style={{ color: '#4ade80', margin: 0 }}>{fmtCurrency(revenue)}</p>
    </div>
  );
}

type Tab = 'products' | 'brands' | 'categories';

export default function ProductAnalytics() {
  const [tab, setTab] = useState<Tab>('products');
  const [minDate, setMinDate] = useState('2019-10-01');
  const [maxDate, setMaxDate] = useState('2019-11-30');
  const [startDate, setStartDate] = useState('2019-11-01');
  const [endDate, setEndDate] = useState('2019-11-30');
  const [products, setProducts] = useState<Product[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getDataRange().then(({ min_date, max_date }) => {
      setMinDate(min_date);
      setMaxDate(max_date);
      const { start, end } = getLast30Days(max_date);
      setStartDate(start);
      setEndDate(end);
    });
  }, []);

  const fetchData = useCallback(() => {
    setLoading(true);
    Promise.all([
      getProducts(startDate, endDate, 20),
      getBrands(startDate, endDate, 20),
      getCategories(startDate, endDate),
    ])
      .then(([p, b, c]) => {
        setProducts(p.products);
        setBrands(b.brands);
        setCategories(c.categories);
      })
      .finally(() => setLoading(false));
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-white text-xl font-bold">Product Analytics</h2>
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={startDate}
            min={minDate}
            max={endDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="bg-slate-800 text-white text-sm border border-slate-600 rounded px-2 py-1"
          />
          <span className="text-slate-400">to</span>
          <input
            type="date"
            value={endDate}
            min={startDate}
            max={maxDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="bg-slate-800 text-white text-sm border border-slate-600 rounded px-2 py-1"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-800 rounded-lg p-1 w-fit">
        {(['products', 'brands', 'categories'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors capitalize ${
              tab === t ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {loading && <p className="text-slate-400 text-sm">Loading...</p>}

      {/* Products Tab */}
      {tab === 'products' && (
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                <th className="text-left pb-2">#</th>
                <th className="text-left pb-2">Product ID</th>
                <th className="text-left pb-2">Category</th>
                <th className="text-left pb-2">Brand</th>
                <th className="text-right pb-2">Price</th>
                <th className="text-right pb-2">Views</th>
                <th className="text-right pb-2">Cart Adds</th>
                <th className="text-right pb-2">Purchases</th>
                <th className="text-right pb-2">Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {products.map((p, i) => (
                <tr key={p.product_id} className="text-slate-300 hover:bg-slate-700/30">
                  <td className="py-2 text-slate-500">{i + 1}</td>
                  <td className="py-2">{p.product_id}</td>
                  <td className="py-2">{p.category || '—'}</td>
                  <td className="py-2">{p.brand || '—'}</td>
                  <td className="py-2 text-right">{fmtCurrency(p.price)}</td>
                  <td className="py-2 text-right">{fmtNum(p.views)}</td>
                  <td className="py-2 text-right">{fmtNum(p.carts)}</td>
                  <td className="py-2 text-right">{fmtNum(p.purchases)}</td>
                  <td className="py-2 text-right text-green-400">{fmtCurrency(p.revenue)}</td>
                </tr>
              ))}
              {products.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-4 text-center text-slate-500">No data</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Brands Tab */}
      {tab === 'brands' && (
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white text-sm font-semibold mb-4">Top 10 Brands by Revenue</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={brands.slice(0, 10)} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={fmtNum} />
                <YAxis type="category" dataKey="brand" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                  formatter={(val: number) => fmtCurrency(val)}
                />
                <Bar dataKey="revenue" fill="#3b82f6" name="Revenue" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-left pb-2">Brand</th>
                  <th className="text-right pb-2">Views</th>
                  <th className="text-right pb-2">Cart Adds</th>
                  <th className="text-right pb-2">Purchases</th>
                  <th className="text-right pb-2">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {brands.map((b) => (
                  <tr key={b.brand} className="text-slate-300">
                    <td className="py-2 font-medium">{b.brand || '—'}</td>
                    <td className="py-2 text-right">{fmtNum(b.views)}</td>
                    <td className="py-2 text-right">{fmtNum(b.carts)}</td>
                    <td className="py-2 text-right">{fmtNum(b.purchases)}</td>
                    <td className="py-2 text-right text-green-400">{fmtCurrency(b.revenue)}</td>
                  </tr>
                ))}
                {brands.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-slate-500">No data</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Categories Tab */}
      {tab === 'categories' && (
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white text-sm font-semibold mb-4">Revenue by Category</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categories.slice(0, 10)}
                  dataKey="revenue"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  labelLine={false}
                  label={({ percent }: { percent: number }) =>
                    percent > 0.03 ? `${(percent * 100).toFixed(1)}%` : ''
                  }
                >
                  {categories.slice(0, 10).map((_, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ color: '#94a3b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-left pb-2">Category</th>
                  <th className="text-right pb-2">Views</th>
                  <th className="text-right pb-2">Cart Adds</th>
                  <th className="text-right pb-2">Purchases</th>
                  <th className="text-right pb-2">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {categories.map((c) => (
                  <tr key={c.category} className="text-slate-300">
                    <td className="py-2 font-medium">{c.category || '—'}</td>
                    <td className="py-2 text-right">{fmtNum(c.views)}</td>
                    <td className="py-2 text-right">{fmtNum(c.carts)}</td>
                    <td className="py-2 text-right">{fmtNum(c.purchases)}</td>
                    <td className="py-2 text-right text-green-400">{fmtCurrency(c.revenue)}</td>
                  </tr>
                ))}
                {categories.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-slate-500">No data</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
