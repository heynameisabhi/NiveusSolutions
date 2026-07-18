import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export const getDashboard = () => api.get('/dashboard').then(r => r.data)
export const getRecords = (params = {}) => api.get('/records', { params }).then(r => r.data)
export const getRecord = (id) => api.get(`/records/${id}`).then(r => r.data)
export const getFlags = (params = {}) => api.get('/flags', { params }).then(r => r.data)
export const getClaims = () => api.get('/claims').then(r => r.data)
export const getDocumentDetails = (documentId) => api.get(`/documents/${documentId}`).then(r => r.data)
export const getNormalizationReport = () => api.get('/normalization-report').then(r => r.data)
export const triggerIngest = (folder = null) =>
  api.post('/ingest', folder ? { folder } : {}).then(r => r.data)

// Clinic management
export const listClinicConfigs = () => api.get('/clinics/configs').then(r => r.data)
export const deleteClinicConfig = (clinicId) => api.delete(`/clinics/configs/${clinicId}`).then(r => r.data)

// File uploads (multipart)
export const uploadSampleData = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload/sample-data', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const uploadClinicConfig = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload/clinic-config', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

