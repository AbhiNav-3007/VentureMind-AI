// VentureMind AI — 404 Not Found Page
import { useNavigate } from 'react-router-dom'
import { Brain, Home } from 'lucide-react'

export default function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-6">
      <div className="text-center max-w-sm">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
          <Brain className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-6xl font-bold text-primary mb-4">404</h1>
        <p className="text-xl font-semibold text-dark mb-2">Page Not Found</p>
        <p className="text-muted mb-8">
          The page you're looking for doesn't exist. Let's get you back on track.
        </p>
        <button
          onClick={() => navigate('/')}
          className="btn-primary flex items-center gap-2 mx-auto"
        >
          <Home className="w-4 h-4" /> Back to Home
        </button>
      </div>
    </div>
  )
}
