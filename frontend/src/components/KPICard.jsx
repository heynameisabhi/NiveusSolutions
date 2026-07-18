export default function KPICard({ label, value, sub, icon, color = 'brand', trend }) {
  const colorMap = {
    brand:   { bg: 'bg-brand-600/10',   icon: 'text-brand-400',   border: 'border-brand-600/20' },
    emerald: { bg: 'bg-emerald-500/10', icon: 'text-emerald-400', border: 'border-emerald-500/20' },
    amber:   { bg: 'bg-amber-500/10',   icon: 'text-amber-400',   border: 'border-amber-500/20' },
    red:     { bg: 'bg-red-500/10',     icon: 'text-red-400',     border: 'border-red-500/20' },
    sky:     { bg: 'bg-sky-500/10',     icon: 'text-sky-400',     border: 'border-sky-500/20' },
    purple:  { bg: 'bg-purple-500/10',  icon: 'text-purple-400',  border: 'border-purple-500/20' },
  }

  const c = colorMap[color] || colorMap.brand

  return (
    <div className={`glass-card p-5 animate-slide-up border ${c.border} relative overflow-hidden`}>
      {/* Background glow */}
      <div className={`absolute -top-8 -right-8 w-24 h-24 rounded-full ${c.bg} blur-2xl pointer-events-none`} />

      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">{label}</p>
          <p className="text-3xl font-bold text-white tabular-nums">
            {value ?? <span className="text-gray-600">—</span>}
          </p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        {icon && (
          <div className={`p-2.5 rounded-xl ${c.bg}`}>
            <span className={c.icon}>{icon}</span>
          </div>
        )}
      </div>

      {trend !== undefined && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <span className={`text-xs font-medium ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
          <span className="text-xs text-gray-600 ml-1">vs last run</span>
        </div>
      )}
    </div>
  )
}
