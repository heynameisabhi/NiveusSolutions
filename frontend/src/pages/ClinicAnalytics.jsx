import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { getClaims, getDashboard } from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#10b981']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card px-4 py-3 text-sm shadow-xl border border-white/5 bg-surface-900/90">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }} className="font-semibold">
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  )
}

export default function ClinicAnalytics() {
  const [claims, setClaims] = useState([])
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getClaims(), getDashboard()])
      .then(([claimsData, dashData]) => {
        setClaims(claimsData)
        setDashboardData(dashData)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />

  // Normalization data for charts
  const normData = Object.entries(dashboardData?.normalization_breakdown || {}).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value
  }))

  // Source system breakdown
  const sourceData = Object.entries(dashboardData?.source_breakdown || {}).map(([name, value]) => ({
    name,
    value
  }))

  // Grouped bar chart data: Claim No vs Record counts
  const barData = claims.map(c => ({
    name: c.claim_no ? c.claim_no.substring(0, 15) : 'N/A',
    'Total Items': c.record_count,
    'Lab Results': c.lab_count,
    'Medications': c.record_count - c.lab_count
  }))

  return (
    <div className="p-8 space-y-8 animate-fade-in overflow-y-auto h-full">
      <div>
        <h1 className="text-2xl font-bold text-white">System & Claims Analytics</h1>
        <p className="text-gray-500 text-sm mt-1">
          Operational statistics: normalization confidence, source systems, and claim distributions.
        </p>
      </div>

      {/* Claims KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border border-white/5 bg-white/2 rounded-xl">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-gray-400 text-xs font-semibold uppercase tracking-wider block">Total claims</span>
              <span className="text-3xl font-extrabold text-white mt-1 block">{claims.length}</span>
            </div>
            <div className="p-3 bg-brand-500/10 text-brand-400 rounded-xl">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="glass-card p-6 border border-white/5 bg-white/2 rounded-xl">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-gray-400 text-xs font-semibold uppercase tracking-wider block">Total parsed records</span>
              <span className="text-3xl font-extrabold text-brand-400 mt-1 block">
                {claims.reduce((acc, c) => acc + c.record_count, 0)}
              </span>
            </div>
            <div className="p-3 bg-purple-500/10 text-purple-400 rounded-xl">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
          </div>
        </div>

        <div className="glass-card p-6 border border-white/5 bg-white/2 rounded-xl">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-gray-400 text-xs font-semibold uppercase tracking-wider block">Source systems</span>
              <span className="text-3xl font-extrabold text-emerald-400 mt-1 block">{sourceData.length}</span>
            </div>
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9h18" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts block */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Normalization breakdown */}
        <div className="glass-card p-6 border border-white/5 bg-white/2 rounded-xl">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-6">Test Normalization Confidence</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={normData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
              >
                {normData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Source System share */}
        <div className="glass-card p-6 border border-white/5 bg-white/2 rounded-xl">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-6">Source System Distribution</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={sourceData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
              >
                {sourceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grouped Bar Chart of Claims */}
      <div className="glass-card p-6 border border-white/5 bg-white/2 rounded-xl">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-6">Item Breakdown Per Claim</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="Total Items" fill="#6366f1" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Lab Results" fill="#a855f7" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Medications" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
