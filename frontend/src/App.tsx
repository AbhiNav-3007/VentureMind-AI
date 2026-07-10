import { Routes, Route } from 'react-router-dom'
import LandingPage from '@/pages/LandingPage'
import SubmitPage from '@/pages/SubmitPage'
import AgentDashboard from '@/pages/AgentDashboard'
import BlueprintDashboard from '@/pages/BlueprintDashboard'
import ExportPage from '@/pages/ExportPage'
import NotFoundPage from '@/pages/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/submit" element={<SubmitPage />} />
      <Route path="/agents/:startupId" element={<AgentDashboard />} />
      <Route path="/blueprint/:startupId" element={<BlueprintDashboard />} />
      <Route path="/export/:startupId" element={<ExportPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
