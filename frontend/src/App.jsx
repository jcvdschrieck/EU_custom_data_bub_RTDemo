import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import EclLayout          from './components/EclLayout'
import MainPage           from './pages/MainPage'
import Dashboard          from './pages/Dashboard'
import SuspiciousPage     from './pages/SuspiciousPage'
import ProcessingLogPage  from './pages/ProcessingLogPage'
import IrelandPage        from './pages/IrelandPage'

export default function App() {
  return (
    <BrowserRouter>
      <EclLayout>
        <Routes>
          <Route path="/"             element={<MainPage />} />
          <Route path="/dashboard"    element={<Dashboard />} />
          <Route path="/suspicious"   element={<SuspiciousPage />} />
          <Route path="/agent-log"    element={<ProcessingLogPage />} />
          <Route path="/ireland"      element={<IrelandPage />} />
          <Route path="*"             element={<Navigate to="/" replace />} />
        </Routes>
      </EclLayout>
    </BrowserRouter>
  )
}
