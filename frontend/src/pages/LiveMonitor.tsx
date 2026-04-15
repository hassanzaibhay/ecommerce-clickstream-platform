import { useEffect, useState, useRef } from 'react';
import type { LiveSession } from '../api/client';
import { fmtNum } from '../api/client';

const formatCategory = (cat: string | null): string => {
  if (!cat) return '—';
  const root = cat.split('.')[0];
  return root.charAt(0).toUpperCase() + root.slice(1);
};

const timeAgo = (dateStr: string | null): string => {
  if (!dateStr) return '—';
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
};

const Badge = ({ value }: { value: boolean }) => (
  <span style={{
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: 600,
    backgroundColor: value ? '#064e3b' : '#1f2937',
    color: value ? '#34d399' : '#6b7280',
  }}>
    {value ? 'Yes' : 'No'}
  </span>
);

export default function LiveMonitor() {
  const [sessions, setSessions] = useState<LiveSession[]>([]);
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const backoffRef = useRef(1000);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      const es = new EventSource('/api/live/sessions');
      esRef.current = es;

      es.onopen = () => {
        setConnected(true);
        backoffRef.current = 1000;
      };

      es.onmessage = (event) => {
        try {
          const data: LiveSession[] = JSON.parse(event.data as string);
          setSessions(data.slice(0, 20));
        } catch {
          // ignore parse errors
        }
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        esRef.current = null;
        if (!cancelled) {
          const delay = Math.min(backoffRef.current, 30000);
          backoffRef.current = Math.min(backoffRef.current * 2, 30000);
          setTimeout(connect, delay);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      esRef.current?.close();
      esRef.current = null;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-white text-xl font-bold">Live Monitor</h2>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2.5 h-2.5 rounded-full ${
              connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className={`text-sm ${connected ? 'text-green-400' : 'text-red-400'}`}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-xs uppercase tracking-wide">Active Sessions</p>
          <p className="text-white text-2xl font-bold mt-1">{fmtNum(sessions.length)}</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-xs uppercase tracking-wide">With Cart</p>
          <p className="text-orange-400 text-2xl font-bold mt-1">
            {fmtNum(sessions.filter((s) => s.has_cart).length)}
          </p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-xs uppercase tracking-wide">Purchased</p>
          <p className="text-green-400 text-2xl font-bold mt-1">
            {fmtNum(sessions.filter((s) => s.has_purchase).length)}
          </p>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 overflow-x-auto">
        <h3 className="text-white text-sm font-semibold mb-4">Live Sessions (last 20)</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 border-b border-slate-700">
              <th className="text-left pb-2">Session ID</th>
              <th className="text-left pb-2">User ID</th>
              <th className="text-left pb-2">Last Event</th>
              <th className="text-right pb-2">Events</th>
              <th className="text-center pb-2">Cart</th>
              <th className="text-center pb-2">Purchase</th>
              <th className="text-left pb-2">Category</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {sessions.map((s) => (
              <tr key={s.session_id} className="text-slate-300 hover:bg-slate-700/30">
                <td className="py-2">
                  <span style={{ fontFamily: 'monospace', fontSize: '12px', color: '#94a3b8' }}>
                    {s.session_id.substring(0, 8)}…
                  </span>
                </td>
                <td className="py-2">{s.user_id}</td>
                <td className="py-2 text-slate-400 text-xs">
                  {timeAgo(s.last_event_time)}
                </td>
                <td className="py-2 text-right">{s.event_count}</td>
                <td className="py-2 text-center"><Badge value={s.has_cart} /></td>
                <td className="py-2 text-center"><Badge value={s.has_purchase} /></td>
                <td className="py-2">{formatCategory(s.last_category)}</td>
              </tr>
            ))}
            {sessions.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">
                  Waiting for live events...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
