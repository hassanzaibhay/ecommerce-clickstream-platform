interface KPICardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: number;
  color?: string;
}

export default function KPICard({ title, value, subtitle, trend, color = 'bg-slate-800' }: KPICardProps) {
  return (
    <div className={`${color} rounded-xl p-4 border border-slate-700`}>
      <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">{title}</p>
      <p className="text-white text-2xl font-bold mt-1">{value}</p>
      {(subtitle || trend !== undefined) && (
        <div className="flex items-center gap-2 mt-1">
          {trend !== undefined && (
            <span className={`text-xs font-medium ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend >= 0 ? '▲' : '▼'} {Math.abs(trend).toFixed(1)}%
            </span>
          )}
          {subtitle && <span className="text-slate-500 text-xs">{subtitle}</span>}
        </div>
      )}
    </div>
  );
}
