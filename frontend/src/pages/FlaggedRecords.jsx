import { useEffect, useState } from 'react'
import { getFlags } from '../api/client'
import DataTable from '../components/DataTable'
import LoadingSpinner from '../components/LoadingSpinner'

const CLASSIFICATIONS = ['All', 'Above Range', 'Below Range', 'Outlier', 'Invalid']

function ClassificationBadge({ value }) {
  const map = {
    'Above Range': 'badge-warning',
    'Below Range': 'badge-info',
    'Outlier':     'badge-purple',
    'Invalid':     'badge-danger',
    'Within Range':'badge-success',
  }
  return <span className={map[value] || 'badge-gray'}>{value}</span>
}

const COLUMNS = [
  { key: 'patient_name', label: 'Patient' },
  { key: 'clinic_id',    label: 'Clinic' },
  { key: 'report_date',  label: 'Date' },
  { key: 'field_name',   label: 'Test' },
  {
    key: 'numeric_value',
    label: 'Value',
    render: (v, row) => v != null ? `${v} ${row.unit || ''}`.trim() : row.raw_value || '—',
  },
  {
    key: 'reference_min',
    label: 'Range',
    render: (_, row) =>
      row.reference_min != null && row.reference_max != null
        ? `${row.reference_min} – ${row.reference_max}`
        : '—',
  },
  {
    key: 'classification',
    label: 'Classification',
    render: (v) => <ClassificationBadge value={v} />,
  },
  {
    key: 'flagged_at',
    label: 'Flagged At',
    render: (v) => v ? new Date(v).toLocaleString() : '—',
  },
]

export default function FlaggedRecords() {
  const [flags, setFlags] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')
  const [search, setSearch] = useState('')

  useEffect(() => {
    const params = {}
    if (filter !== 'All') params.classification = filter
    setLoading(true)
    getFlags(params)
      .then(setFlags)
      .catch(() => setFlags([]))
      .finally(() => setLoading(false))
  }, [filter])

  const filtered = search
    ? flags.filter(f =>
        [f.patient_name, f.clinic_id, f.field_name, f.report_date].some(
          v => v?.toLowerCase().includes(search.toLowerCase())
        )
      )
    : flags

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Flagged Records</h1>
        <p className="text-gray-500 text-sm mt-1">
          Lab results outside reference ranges, outliers, and invalid values.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          id="search-flags"
          type="text"
          placeholder="Search patient, clinic, test…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="input-field w-64"
        />
        <div className="flex gap-2 flex-wrap">
          {CLASSIFICATIONS.map(c => (
            <button
              key={c}
              onClick={() => setFilter(c)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200 ${
                filter === c
                  ? 'bg-brand-600 text-white border-brand-500'
                  : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-600 ml-auto">{filtered.length} records</span>
      </div>

      {/* Table */}
      <div className="glass-card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner />
        ) : (
          <DataTable
            columns={COLUMNS}
            rows={filtered}
            emptyText="No flagged records found for this filter."
          />
        )}
      </div>
    </div>
  )
}
