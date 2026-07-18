import { useState, useRef, useEffect, useCallback } from 'react'
import {
  uploadSampleData,
  uploadClinicConfig,
  listClinicConfigs,
  deleteClinicConfig,
  triggerIngest,
} from '../api/client'

// ─── Reusable drop-zone ───────────────────────────────────────────────────────
function DropZone({ accept, label, icon, hint, onFile, loading, result }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer.files?.[0]
      if (file) onFile(file)
    },
    [onFile]
  )

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !loading && inputRef.current?.click()}
      className={`relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed
        p-10 cursor-pointer transition-all duration-200 select-none
        ${dragging
          ? 'border-brand-500 bg-brand-600/10 scale-[1.01]'
          : 'border-white/10 bg-surface-700/40 hover:border-brand-500/50 hover:bg-brand-600/5'
        }
        ${loading ? 'opacity-70 cursor-not-allowed' : ''}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = '' }}
      />

      {/* Icon */}
      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-colors
        ${dragging ? 'bg-brand-600/30' : 'bg-white/5'}`}>
        {loading
          ? <svg className="w-7 h-7 text-brand-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          : icon
        }
      </div>

      <div className="text-center">
        <p className="text-sm font-semibold text-gray-200">{label}</p>
        <p className="text-xs text-gray-500 mt-1">{hint}</p>
      </div>

      {/* Result toast */}
      {result && (
        <div className={`absolute bottom-3 left-3 right-3 text-xs px-3 py-2 rounded-xl text-center
          ${result.ok
            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/25'
            : 'bg-red-500/15 text-red-300 border border-red-500/25'
          }`}>
          {result.msg}
        </div>
      )}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function UploadManager() {
  const [clinics, setClinics] = useState([])
  const [loadingClinics, setLoadingClinics] = useState(true)

  const [sampleLoading, setSampleLoading] = useState(false)
  const [sampleResult, setSampleResult] = useState(null)

  const [configLoading, setConfigLoading] = useState(false)
  const [configResult, setConfigResult] = useState(null)

  const [deletingId, setDeletingId] = useState(null)
  const [ingesting, setIngesting] = useState(false)
  const [ingestResult, setIngestResult] = useState(null)

  const fetchClinics = useCallback(async () => {
    setLoadingClinics(true)
    try {
      const data = await listClinicConfigs()
      setClinics(data)
    } catch {
      setClinics([])
    } finally {
      setLoadingClinics(false)
    }
  }, [])

  useEffect(() => { fetchClinics() }, [fetchClinics])

  const flash = (setter, result, ms = 4000) => {
    setter(result)
    setTimeout(() => setter(null), ms)
  }

  // ── Upload sample JSON ──
  const handleSampleUpload = async (file) => {
    setSampleLoading(true)
    setSampleResult(null)
    try {
      const res = await uploadSampleData(file)
      flash(setSampleResult, { ok: true, msg: `✓ ${res.message}` })
    } catch (e) {
      flash(setSampleResult, { ok: false, msg: e?.response?.data?.detail || 'Upload failed.' })
    } finally {
      setSampleLoading(false)
    }
  }

  // ── Upload clinic YAML ──
  const handleConfigUpload = async (file) => {
    setConfigLoading(true)
    setConfigResult(null)
    try {
      const res = await uploadClinicConfig(file)
      flash(setConfigResult, { ok: true, msg: `✓ ${res.message}` })
      fetchClinics()
    } catch (e) {
      flash(setConfigResult, { ok: false, msg: e?.response?.data?.detail || 'Upload failed.' })
    } finally {
      setConfigLoading(false)
    }
  }

  // ── Delete clinic config ──
  const handleDelete = async (clinicId) => {
    setDeletingId(clinicId)
    try {
      await deleteClinicConfig(clinicId)
      fetchClinics()
    } catch {
      /* ignore */
    } finally {
      setDeletingId(null)
    }
  }

  // ── Run pipeline ──
  const handleIngest = async () => {
    setIngesting(true)
    setIngestResult(null)
    try {
      const res = await triggerIngest()
      flash(setIngestResult, {
        ok: true,
        msg: `✓ Pipeline complete — ${res.processed} / ${res.total_files} files processed`,
      }, 6000)
    } catch {
      flash(setIngestResult, { ok: false, msg: '✗ Pipeline failed. Check backend logs.' }, 6000)
    } finally {
      setIngesting(false)
    }
  }

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Upload Manager</h1>
          <p className="text-sm text-gray-500 mt-1">
            Add new hospitals / clinics and sample data without touching the filesystem.
          </p>
        </div>

        <button
          id="run-pipeline-btn"
          onClick={handleIngest}
          disabled={ingesting}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {ingesting
            ? <><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg> Processing…</>
            : <><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg> Run Pipeline</>
          }
        </button>
      </div>

      {ingestResult && (
        <div className={`text-sm px-4 py-3 rounded-xl border
          ${ingestResult.ok
            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
            : 'bg-red-500/10 text-red-300 border-red-500/20'
          }`}>
          {ingestResult.msg}
        </div>
      )}

      {/* Upload cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Sample data upload */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-sky-600/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Sample Data</p>
              <p className="text-xs text-gray-500">JSON claim / report files</p>
            </div>
          </div>

          <DropZone
            accept=".json"
            label="Drop a JSON file here or click to browse"
            hint="Saved to sample-data/ · accepted by next pipeline run"
            icon={
              <svg className="w-7 h-7 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            }
            loading={sampleLoading}
            result={sampleResult}
            onFile={handleSampleUpload}
          />
        </div>

        {/* Clinic config upload */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-600/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Clinic / Hospital Config</p>
              <p className="text-xs text-gray-500">YAML field-mapping files</p>
            </div>
          </div>

          <DropZone
            accept=".yaml,.yml"
            label="Drop a YAML file here or click to browse"
            hint="Saved to config/clinics/ · active immediately"
            icon={
              <svg className="w-7 h-7 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            }
            loading={configLoading}
            result={configResult}
            onFile={handleConfigUpload}
          />
        </div>
      </div>

      {/* Registered clinics table */}
      <div className="glass-card overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-white">Registered Clinics</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {clinics.length} clinic config{clinics.length !== 1 ? 's' : ''} found in config/clinics/
            </p>
          </div>
          <button
            onClick={fetchClinics}
            className="btn-ghost text-xs py-1.5"
            title="Refresh"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        {loadingClinics ? (
          <div className="flex items-center justify-center py-16">
            <svg className="w-6 h-6 text-brand-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
        ) : clinics.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-2">
            <svg className="w-10 h-10 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5" />
            </svg>
            <p className="text-sm text-gray-500">No clinic configs found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="table-header text-left">Clinic Name</th>
                <th className="table-header text-left">Clinic ID</th>
                <th className="table-header text-left">File</th>
                <th className="table-header text-center">Field Mappings</th>
                <th className="table-header text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {clinics.map((c) => (
                <tr key={c.clinic_id} className="table-row">
                  <td className="table-cell font-medium text-white">{c.clinic_name || '—'}</td>
                  <td className="table-cell">
                    <span className="badge badge-purple">{c.clinic_id}</span>
                  </td>
                  <td className="table-cell text-gray-500 font-mono text-xs">{c.filename}</td>
                  <td className="table-cell text-center">
                    <span className="badge badge-info">{c.field_count} fields</span>
                  </td>
                  <td className="table-cell text-right">
                    <button
                      id={`delete-clinic-${c.clinic_id}`}
                      onClick={() => handleDelete(c.clinic_id)}
                      disabled={deletingId === c.clinic_id}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg
                        bg-red-500/10 text-red-400 border border-red-500/20
                        hover:bg-red-500/20 transition-all duration-150
                        disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {deletingId === c.clinic_id
                        ? <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                          </svg>
                        : <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                      }
                      {deletingId === c.clinic_id ? 'Deleting…' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* YAML format guide */}
      <div className="glass-card p-6 space-y-3">
        <p className="text-sm font-semibold text-white flex items-center gap-2">
          <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Clinic YAML Format Reference
        </p>
        <pre className="text-xs text-gray-400 bg-surface-900/60 rounded-xl p-4 overflow-x-auto leading-relaxed">{`clinic_id: clinic_c          # unique ID (required)
clinic_name: Apollo Hospital  # display name

field_mappings:
  patient_id:   patient.id       # dot-notation for nested JSON
  patient_name: patient.name
  gender:       patient.gender
  age:          patient.age
  report_date:  report_date
  clinic_id_field: clinic
  medications:  prescriptions
  lab_results:
    hemoglobin: labs.hb
    wbc:        labs.wbc
    platelets:  labs.platelets
    glucose:    labs.glucose

dedup_fields: [patient_id, clinic_id, report_date]

gender_map:
  M: Male
  F: Female`}</pre>
      </div>

    </div>
  )
}
