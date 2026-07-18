import { useEffect, useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { getDashboard } from '../api/client'
import KPICard from '../components/KPICard'
import LoadingSpinner from '../components/LoadingSpinner'

const COLORS = {
  'Above Range': '#f59e0b',
  'Below Range': '#3b82f6',
  'Outlier':     '#a855f7',
  'Invalid':     '#ef4444',
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card px-4 py-3 text-sm shadow-xl">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }} className="font-semibold">
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    try {
      setLoading(true)
      const d = await getDashboard()
      setData(d)
    } catch {
      setError('Failed to load dashboard. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <LoadingSpinner />
  if (error) return (
    <div className="flex items-center justify-center h-full">
      <div className="glass-card p-8 text-center max-w-md">
        <p className="text-red-400 mb-4">{error}</p>
        <button onClick={load} className="btn-primary">Retry</button>
      </div>
    </div>
  )

  // Build run chart data
  const runChartData = (data.runs || []).slice().reverse().map((r, i) => ({
    name: `Run ${i + 1}`,
    processed: r.processed,
    failed: r.failed,
    flagged: r.flagged,
  }))

  // Classification pie data
  const pieData = Object.entries(data.classification_breakdown || {}).map(([name, value]) => ({
    name, value,
  }))

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Pipeline Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">
            {data.last_run_at
              ? `Last run: ${new Date(data.last_run_at).toLocaleString()}`
              : 'No runs yet. Click Run Pipeline to start.'}
          </p>
        </div>
        <button onClick={load} className="btn-ghost text-sm">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 xl:grid-cols-5 gap-4">
        <KPICard
          label="Total Files"
          value={data.total_files}
          color="brand"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          }
        />
        <KPICard
          label="Processed"
          value={data.processed}
          color="emerald"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          }
        />
        <KPICard
          label="Failed"
          value={data.failed}
          color="red"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          }
        />
        <KPICard
          label="Flagged"
          value={data.flagged}
          color="amber"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
        <KPICard
          label="Duplicates"
          value={data.duplicate_count}
          color="purple"
          sub={data.last_run_duration ? `Last run: ${data.last_run_duration.toFixed(2)}s` : undefined}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          }
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Area Chart - Run History */}
        <div className="glass-card p-6 xl:col-span-2">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-6">Pipeline Run History</h2>
          {runChartData.length === 0 ? (
            <p className="text-gray-600 text-sm text-center py-10">No runs yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={runChartData}>
                <defs>
                  <linearGradient id="gradProcessed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradFlagged" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area type="monotone" dataKey="processed" stroke="#6366f1" strokeWidth={2} fill="url(#gradProcessed)" name="Processed" />
                <Area type="monotone" dataKey="flagged" stroke="#f59e0b" strokeWidth={2} fill="url(#gradFlagged)" name="Flagged" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie Chart - Classification Breakdown */}
        <div className="glass-card p-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-6">Flag Classifications</h2>
          {pieData.length === 0 ? (
            <p className="text-gray-600 text-sm text-center py-10">No flags yet.</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={COLORS[entry.name] || '#6366f1'} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-4 space-y-2">
                {pieData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ background: COLORS[item.name] || '#6366f1' }}
                      />
                      <span className="text-gray-400">{item.name}</span>
                    </div>
                    <span className="text-white font-semibold">{item.value}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Recent Runs Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">Recent Pipeline Runs</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Run ID', 'Started', 'Duration', 'Total', 'Processed', 'Failed', 'Flagged', 'Status'].map(h => (
                  <th key={h} className="table-header text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(data.runs || []).map((r) => (
                <tr key={r.run_id} className="table-row">
                  <td className="table-cell font-mono text-xs text-gray-500">{r.run_id.slice(0, 8)}…</td>
                  <td className="table-cell">{new Date(r.started_at).toLocaleString()}</td>
                  <td className="table-cell">{r.duration_seconds ? `${r.duration_seconds.toFixed(2)}s` : '—'}</td>
                  <td className="table-cell font-semibold text-white">{r.total_files}</td>
                  <td className="table-cell text-emerald-400">{r.processed}</td>
                  <td className="table-cell text-red-400">{r.failed}</td>
                  <td className="table-cell text-amber-400">{r.flagged}</td>
                  <td className="table-cell">
                    <span className={r.status === 'completed' ? 'badge-success' : r.status === 'failed' ? 'badge-danger' : 'badge-info'}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
              {(!data.runs || data.runs.length === 0) && (
                <tr>
                  <td colSpan={8} className="table-cell text-center text-gray-600 py-8">No runs yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
