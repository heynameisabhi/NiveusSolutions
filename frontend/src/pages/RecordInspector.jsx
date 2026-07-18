import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getClaims, getDocumentDetails } from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'

function JsonViewer({ data, title }) {
  return (
    <div className="flex flex-col h-full bg-surface-900/50 rounded-xl border border-white/5 overflow-hidden">
      <div className="px-4 py-3 border-b border-white/5 bg-white/2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400">{title}</h3>
      </div>
      <pre className="flex-1 overflow-auto text-xs text-emerald-400 p-4 leading-relaxed font-mono">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}

function StatusBadge({ classification }) {
  const map = {
    'Above Range': 'badge-warning',
    'Below Range': 'badge-info',
    'Outlier':     'badge-purple',
    'Invalid':     'badge-danger',
    'Within Range':'badge-success',
  }
  return <span className={map[classification] || 'badge-gray'}>{classification || 'Within Range'}</span>
}

export default function RecordInspector() {
  const { id } = useParams() // this is document_id
  const navigate = useNavigate()

  const [claims, setClaims] = useState([])
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [listLoading, setListLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('labs') // 'labs' | 'meds' | 'clinical' | 'raw'

  // Load claims list for the sidebar
  useEffect(() => {
    getClaims()
      .then(setClaims)
      .catch(() => setClaims([]))
      .finally(() => setListLoading(false))
  }, [])

  // Load document details when id (document_id) changes
  useEffect(() => {
    if (!id) return
    setLoading(true)
    getDocumentDetails(id)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setLoading(false))
  }, [id])

  return (
    <div className="flex h-full animate-fade-in overflow-hidden">
      {/* Sidebar - Document List */}
      <div className="w-80 flex-shrink-0 border-r border-white/5 flex flex-col bg-surface-800">
        <div className="px-5 py-4 border-b border-white/5">
          <h1 className="text-sm font-bold text-white uppercase tracking-wider">Claims & Documents</h1>
          <p className="text-xs text-gray-500 mt-0.5">Select a document to inspect</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          {listLoading ? (
            <LoadingSpinner size="sm" text="Loading claims..." />
          ) : claims.length === 0 ? (
            <p className="text-gray-600 text-xs text-center py-8">No records yet. Run the pipeline.</p>
          ) : (
            claims.map((c) => (
              <button
                key={c.document_id}
                onClick={() => navigate(`/records/${c.document_id}`)}
                className={`w-full text-left px-5 py-4 border-b border-white/5 transition-all duration-150 hover:bg-white/2 ${
                  id === c.document_id ? 'bg-brand-600/10 border-l-2 border-l-brand-500' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-gray-100 truncate">
                    {c.patient_name || 'Anonymous Patient'}
                  </span>
                  <span className="text-[10px] uppercase font-bold text-brand-400 bg-brand-500/10 px-1.5 py-0.5 rounded">
                    {c.source_system}
                  </span>
                </div>
                <div className="text-xs text-gray-400 truncate font-mono mb-2">
                  Claim: {c.claim_no || 'N/A'}
                </div>
                <div className="flex items-center justify-between text-[11px] text-gray-500">
                  <span>{c.reports_date}</span>
                  <span className="bg-white/5 px-2 py-0.5 rounded-full text-gray-400">
                    {c.record_count} items
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Panel - Details */}
      <div className="flex-1 flex flex-col overflow-hidden bg-surface-900/40">
        {!id ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-400 mb-1">No Document Selected</h3>
              <p className="text-sm text-gray-600">Choose a document from the sidebar to view details</p>
            </div>
          </div>
        ) : loading ? (
          <LoadingSpinner />
        ) : !detail ? (
          <div className="flex items-center justify-center h-full text-red-400 text-sm">
            Failed to load document details.
          </div>
        ) : (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Header Block */}
            <div className="px-8 py-6 border-b border-white/5 bg-surface-800">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-white">
                      {detail.patient_name || 'Anonymous Patient'}
                    </h2>
                    <span className="badge-purple font-mono text-[11px]">
                      {detail.gender} • {detail.age || 'N/A'} yrs
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-gray-400">
                    <span className="font-mono">Document: {detail.document_id}</span>
                    <span>•</span>
                    <span className="font-mono">Claim: {detail.claim_no || 'N/A'}</span>
                    <span>•</span>
                    <span>Hospital: {detail.hospital_name || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Tab navigation */}
            <div className="flex border-b border-white/5 bg-surface-800 px-8">
              {[
                { id: 'labs', label: `Lab Results (${detail.lab_results?.length || 0})` },
                { id: 'meds', label: `Medications (${detail.medications?.length || 0})` },
                { id: 'clinical', label: 'Clinical Context' },
                { id: 'raw', label: 'Raw Headers' },
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={`py-3 px-4 text-xs font-semibold uppercase tracking-wider border-b-2 transition-all duration-150 mr-6 ${
                    activeTab === t.id
                      ? 'border-brand-500 text-brand-400'
                      : 'border-transparent text-gray-500 hover:text-gray-300'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Content view */}
            <div className="flex-1 overflow-y-auto p-8">
              {activeTab === 'labs' && (
                <div className="space-y-6">
                  {detail.lab_results?.length === 0 ? (
                    <div className="glass-card p-8 text-center text-gray-500 text-sm">
                      No lab results found in this document.
                    </div>
                  ) : (
                    <div className="glass-card p-0 overflow-hidden border border-white/5">
                      <table className="w-full text-left">
                        <thead>
                          <tr className="border-b border-white/5 bg-white/2">
                            <th className="px-6 py-3.5 text-xs font-bold text-gray-400 uppercase">Test Name</th>
                            <th className="px-6 py-3.5 text-xs font-bold text-gray-400 uppercase">Result</th>
                            <th className="px-6 py-3.5 text-xs font-bold text-gray-400 uppercase">Reference Range</th>
                            <th className="px-6 py-3.5 text-xs font-bold text-gray-400 uppercase">Status</th>
                            <th className="px-6 py-3.5 text-xs font-bold text-gray-400 uppercase">Standardization</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.lab_results.map((lab, i) => (
                            <tr key={i} className="border-b border-white/5 last:border-0 hover:bg-white/2 transition-colors">
                              <td className="px-6 py-4">
                                <p className="text-sm font-semibold text-white">
                                  {lab.test_name_canonical || lab.test_name_original}
                                </p>
                                {lab.test_name_canonical && (
                                  <p className="text-[10px] text-gray-500 mt-0.5">Original: "{lab.test_name_original}"</p>
                                )}
                              </td>
                              <td className="px-6 py-4 font-medium text-gray-200">
                                {lab.result_text || lab.result_value || '—'} {lab.unit_canonical || ''}
                              </td>
                              <td className="px-6 py-4 text-xs text-gray-400">
                                {lab.range_text || (lab.range_low != null && lab.range_high != null ? `${lab.range_low} – ${lab.range_high}` : '—')}
                              </td>
                              <td className="px-6 py-4">
                                <StatusBadge classification={lab.test_analytics} />
                              </td>
                              <td className="px-6 py-4 text-xs text-gray-500">
                                <div className="flex flex-col">
                                  <span className="font-semibold uppercase tracking-wider text-[9px] text-brand-400">
                                    {lab.normalization_method?.replace('_', ' ')}
                                  </span>
                                  {lab.normalization_confidence != null && (
                                    <span className="text-[10px] mt-0.5 text-gray-600">
                                      Conf: {(lab.normalization_confidence * 100).toFixed(0)}%
                                    </span>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'meds' && (
                <div className="space-y-6">
                  {detail.medications?.length === 0 ? (
                    <div className="glass-card p-8 text-center text-gray-500 text-sm">
                      No discharge medications found in this document.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {detail.medications.map((med, i) => (
                        <div key={i} className="glass-card p-5 border border-white/5 bg-white/2 rounded-xl flex items-start gap-4">
                          <div className="p-3 bg-brand-500/10 text-brand-400 rounded-lg">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <h4 className="font-bold text-white text-base">{med.medicine}</h4>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-3 text-xs">
                              <div>
                                <span className="text-gray-500 block">Dose</span>
                                <span className="text-gray-200 font-medium">{med.dose || '—'}</span>
                              </div>
                              <div>
                                <span className="text-gray-500 block">Frequency</span>
                                <span className="text-gray-200 font-medium">{med.frequency || '—'}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'clinical' && (
                <div className="space-y-6 max-w-4xl">
                  <div className="glass-card p-6 border border-white/5 space-y-6">
                    <div>
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-brand-400 mb-2">Diagnosis</h3>
                      <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">{detail.diagnosis || '—'}</p>
                    </div>
                    <div className="border-t border-white/5 pt-6">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-brand-400 mb-2">Brief History</h3>
                      <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{detail.brief_history || '—'}</p>
                    </div>
                    {detail.recommendations && (
                      <div className="border-t border-white/5 pt-6">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-brand-400 mb-2">Recommendations & Post-Discharge Advice</h3>
                        <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{detail.recommendations}</p>
                      </div>
                    )}
                    {detail.course_during_hospitalisation && detail.course_during_hospitalisation !== '[]' && (
                      <div className="border-t border-white/5 pt-6">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-brand-400 mb-2">Course During Hospitalisation</h3>
                        <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{detail.course_during_hospitalisation}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'raw' && (
                <div className="h-[500px]">
                  <JsonViewer
                    title="Document Metadata & Wrapper Fields"
                    data={{
                      document_id: detail.document_id,
                      trace_id: detail.trace_id,
                      correlation_id: detail.correlation_id,
                      claim_no: detail.claim_no,
                      source_system: detail.source_system,
                      patient_name: detail.patient_name,
                      age: detail.age,
                      gender: detail.gender,
                      hospital_name: detail.hospital_name,
                      reports_date: detail.reports_date,
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
