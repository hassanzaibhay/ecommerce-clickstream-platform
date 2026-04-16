import { useEffect, useState, useCallback } from 'react';
import { getDataRange, getFunnel, fmtNum, fmtPercent, formatLabel, type FunnelData } from '../api/client';

function getLast30Days(maxDate: string) {
  const end = new Date(maxDate);
  const start = new Date(end);
  start.setDate(start.getDate() - 29);
  return { end: end.toISOString().slice(0, 10), start: start.toISOString().slice(0, 10) };
}

export default function FunnelAnalysis() {
  const [minDate, setMinDate] = useState('2019-10-01');
  const [maxDate, setMaxDate] = useState('2019-11-30');
  const [startDate, setStartDate] = useState('2019-11-01');
  const [endDate, setEndDate] = useState('2019-11-30');
  const [category, setCategory] = useState('all');
  const [data, setData] = useState<FunnelData | null>(null);
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
    getFunnel(startDate, endDate, category)
      .then(setData)
      .finally(() => setLoading(false));
  }, [startDate, endDate, category]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const stageColors = ['#3b82f6', '#f97316', '#22c55e'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-white text-xl font-bold">Funnel Analysis</h2>
        <div className="flex items-center gap-2 flex-wrap">
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
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="bg-slate-800 text-white text-sm border border-slate-600 rounded px-2 py-1"
          >
            <option value="all">All Categories</option>
            {data?.categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <p className="text-slate-400 text-sm">Loading...</p>}

      {data && (
        <>
          {/* Funnel visualization */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white text-sm font-semibold mb-4">Conversion Funnel</h3>
            <div className="space-y-3">
              {data.stages.map((stage, i) => (
                <div key={stage.stage}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-slate-300 text-sm">{stage.stage}</span>
                    <span className="text-white font-medium text-sm">{fmtNum(stage.count)}</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-6 relative overflow-hidden">
                    <div
                      className="h-6 rounded-full transition-all duration-500"
                      style={{
                        width: `${(stage.rate * 100).toFixed(2)}%`,
                        minWidth: stage.count > 0 ? '4px' : '0',
                        backgroundColor: stageColors[i],
                        opacity: 0.85,
                      }}
                    />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-white font-medium">
                      {i === 0 ? '100%' : fmtPercent(stage.rate)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-700">
              <div className="text-center">
                <p className="text-slate-400 text-xs">View to Cart</p>
                <p className="text-white font-bold">{fmtPercent(data.view_to_cart_rate)}</p>
              </div>
              <div className="text-center">
                <p className="text-slate-400 text-xs">Cart to Purchase</p>
                <p className="text-white font-bold">{fmtPercent(data.cart_to_purchase_rate)}</p>
              </div>
              <div className="text-center">
                <p className="text-slate-400 text-xs">Overall Conversion</p>
                <p className="text-white font-bold">{fmtPercent(data.overall_conversion)}</p>
              </div>
            </div>
          </div>

          {/* Cart abandonment table */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white text-sm font-semibold mb-4">Top Cart Abandonment by Category</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-700">
                    <th className="text-left pb-2">Category</th>
                    <th className="text-right pb-2">Abandoned Carts</th>
                    <th className="text-right pb-2">Abandonment Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {data.top_abandonment.map((row) => (
                    <tr key={row.category} className="text-slate-300">
                      <td className="py-2">{formatLabel(row.category)}</td>
                      <td className="py-2 text-right">{fmtNum(row.abandoned_carts)}</td>
                      <td className="py-2 text-right">
                        <span className="text-orange-400 font-medium">
                          {fmtPercent(row.abandonment_rate)}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {data.top_abandonment.length === 0 && (
                    <tr>
                      <td colSpan={3} className="py-4 text-center text-slate-500">No data</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
