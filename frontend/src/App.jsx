import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import FlaggedRecords from './pages/FlaggedRecords'
import RecordInspector from './pages/RecordInspector'
import ClinicAnalytics from './pages/ClinicAnalytics'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/flags" element={<FlaggedRecords />} />
            <Route path="/records" element={<RecordInspector />} />
            <Route path="/records/:id" element={<RecordInspector />} />
            <Route path="/clinics" element={<ClinicAnalytics />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
