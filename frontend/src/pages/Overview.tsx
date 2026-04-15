import { useEffect, useState, useCallback } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import KPICard from '../components/KPICard';
import {
  getDataRange,
  getOverview,
  fmtNum,
  fmtCurrency,
  fmtPercent,
  type OverviewData,
} from '../api/client';

function getLast30Days(maxDate: string): { start: string; end: string } {
  const end = new Date(maxDate);
  const start = new Date(end);
  start.setDate(start.getDate() - 29);
  return {
    end: end.toISOString().slice(0, 10),
    start: start.toISOString().slice(0, 10),
  };
}

export default function Overview() {
  const [minDate, setMinDate] = useState('2019-10-01');
  const [maxDate, setMaxDate] = useState('2019-11-30');
  const [startDate, setStartDate] = useState('2019-11-01');
  const [endDate, setEndDate] = useState('2019-11-30');
  const [data, setData] = useState<OverviewData | null>(null);
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
    getOverview(startDate, endDate)
      .then(setData)
      .finally(() => setLoading(false));
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-white text-xl font-bold">Overview</h2>
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

      {loading && <p className="text-slate-400 text-sm">Loading...</p>}

      {data && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <KPICard title="Total Events" value={fmtNum(data.total_events)} color="bg-blue-900/40" />
            <KPICard title="Unique Users" value={fmtNum(data.unique_users)} color="bg-purple-900/40" />
            <KPICard title="Total Revenue" value={fmtCurrency(data.total_revenue)} color="bg-green-900/40" />
            <KPICard title="Conversion Rate" value={fmtPercent(data.conversion_rate)} color="bg-orange-900/40" />
          </div>

          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white text-sm font-semibold mb-4">Daily Trend</h3>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={data.daily_trend} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorCarts" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorPurchases" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={fmtNum} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                  labelStyle={{ color: '#f8fafc' }}
                  formatter={(val: number) => fmtNum(val)}
                />
                <Legend wrapperStyle={{ color: '#94a3b8' }} />
                <Area type="monotone" dataKey="views" stroke="#3b82f6" fill="url(#colorViews)" name="Views" />
                <Area type="monotone" dataKey="carts" stroke="#f97316" fill="url(#colorCarts)" name="Cart Adds" />
                <Area type="monotone" dataKey="purchases" stroke="#22c55e" fill="url(#colorPurchases)" name="Purchases" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <KPICard title="Avg Order Value" value={fmtCurrency(data.avg_order_value)} />
            <KPICard title="Total Views" value={fmtNum(data.total_views)} />
            <KPICard title="Total Cart Adds" value={fmtNum(data.total_carts)} />
            <KPICard title="Total Purchases" value={fmtNum(data.total_purchases)} />
          </div>
        </>
      )}
    </div>
  );
}
