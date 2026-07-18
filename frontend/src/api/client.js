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
