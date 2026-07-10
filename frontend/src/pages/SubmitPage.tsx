// VentureMind AI — Submit Page (Redesigned v3)
// Premium dark form with animated idea input

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Brain, Send, Lightbulb, ChevronLeft, AlertCircle,
  Clock, ChevronRight, Rocket, Zap,
} from 'lucide-react'
import { generateBlueprint, listBlueprints } from '@/services/api'
import { useStore } from '@/store'

const industries = [
  'Technology / SaaS', 'FinTech', 'HealthTech', 'EdTech', 'AgriTech',
  'CleanTech / GreenTech', 'E-Commerce / Retail', 'AI / Machine Learning',
  'Logistics / Supply Chain', 'HR Tech', 'Real Estate Tech', 'FoodTech',
  'Travel / Hospitality', 'Media / Entertainment', 'Other',
]

const budgets = [
  'Below ₹5 Lakhs', '₹5 – 25 Lakhs', '₹25 Lakhs – 1 Crore', '₹1 – 5 Crore', '₹5 Crore+',
]

const examples = [
  'An AI-powered waste management platform that helps municipalities reduce landfill waste by 40% using smart IoT sensors.',
  'A hyper-personalised EdTech app that adapts curriculum in real-time based on individual student learning patterns.',
  'A blockchain-based supply chain transparency tool for the pharmaceutical industry to prevent counterfeit drugs.',
  'A B2B SaaS platform that automates GST compliance and filing for SMEs using natural language processing.',
]

const features = [
  { icon: Rocket,   label: 'Market Research',    detail: 'TAM, competition & trends' },
  { icon: Zap,      label: 'Financial Plan',      detail: '3-year projections & pricing' },
  { icon: Send,     label: 'GTM Strategy',        detail: 'Launch phases & channels' },
  { icon: Brain,    label: 'Investor Pitch',      detail: 'Executive summary & ask' },
]

export default function SubmitPage() {
  const navigate = useNavigate()
  const setStartupId = useStore((s) => s.setStartupId)
  const setWorkflowStatus = useStore((s) => s.setWorkflowStatus)

  const [history, setHistory] = useState<any[]>([])
  const [idea, setIdea] = useState('')
  const [industry, setIndustry] = useState('')
  const [audience, setAudience] = useState('')
  const [country, setCountry] = useState('India')
  const [budget, setBudget] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listBlueprints(5, 0)
      .then((data) => setHistory(data.items ?? []))
      .catch(console.error)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!idea.trim() || idea.trim().length < 10) {
      setError('Please describe your startup idea in at least 10 characters.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const resp = await generateBlueprint({
        idea: idea.trim(),
        industry: industry || undefined,
        target_audience: audience || undefined,
        country: country || 'India',
        budget: budget || undefined,
      })
      setStartupId(resp.startup_id)
      setWorkflowStatus('pending')
      navigate(`/agents/${resp.startup_id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--gradient-hero)' }}>
      {/* Ambient glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[10%] right-[20%] w-[400px] h-[400px] rounded-full opacity-08"
          style={{ background: 'radial-gradient(circle, #6366F1 0%, transparent 70%)', filter: 'blur(80px)' }} />
        <div className="absolute bottom-[10%] left-[15%] w-[300px] h-[300px] rounded-full opacity-05"
          style={{ background: 'radial-gradient(circle, #22D3EE 0%, transparent 70%)', filter: 'blur(60px)' }} />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-12">
        {/* Back */}
        <button
          onClick={() => navigate('/')}
          className="btn-ghost text-xs mb-10"
        >
          <ChevronLeft className="w-4 h-4" /> Back to Home
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">

          {/* ── Left Panel: Feature highlights ──────────────────────── */}
          <div className="lg:col-span-2 space-y-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-5 animate-pulse-glow"
                style={{ background: 'var(--gradient-brand)' }}>
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold mb-3" style={{ color: 'var(--color-text)' }}>
                Start Your<br />
                <span className="gradient-text">Blueprint</span>
              </h1>
              <p className="text-sm text-muted leading-relaxed">
                Describe your startup idea. Our 5 AI agents will research the market, build your financials, find funding, and craft your go-to-market strategy — all automatically.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="space-y-3"
            >
              <p className="text-xs font-semibold uppercase tracking-wider text-dim">What You'll Get</p>
              {features.map(({ icon: Icon, label, detail }) => (
                <div key={label} className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)' }}>
                    <Icon className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>{label}</p>
                    <p className="text-xs text-dim">{detail}</p>
                  </div>
                </div>
              ))}
            </motion.div>

            {/* Recent History */}
            {history.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="glass p-4"
              >
                <h3 className="text-xs font-semibold uppercase tracking-wider text-dim mb-3 flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5" /> Recent
                </h3>
                <div className="space-y-2">
                  {history.map((bp) => (
                    <div
                      key={bp.id}
                      onClick={() => navigate(bp.status === 'done' ? `/blueprint/${bp.id}` : `/agents/${bp.id}`)}
                      className="flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all"
                      style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)' }}
                    >
                      <p className="text-xs truncate flex-1" style={{ color: 'var(--color-text-2)' }}>{bp.idea_text}</p>
                      <span className={`status-${bp.status} ml-2 flex-shrink-0`}>{bp.status}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* ── Right Panel: Form ───────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
            className="lg:col-span-3"
          >
            <div className="glass p-8">
              <form onSubmit={handleSubmit} className="space-y-6">

                {/* Idea Textarea */}
                <div>
                  <label className="label">
                    Your Startup Idea <span style={{ color: '#F87171' }}>*</span>
                  </label>
                  <textarea
                    id="startup-idea"
                    value={idea}
                    onChange={(e) => setIdea(e.target.value)}
                    rows={5}
                    placeholder="e.g. An AI-powered platform that helps farmers predict crop diseases using satellite imagery and IoT sensors, reducing agricultural losses by up to 30%."
                    className="input"
                    style={{ resize: 'none' }}
                    required
                  />
                  <div className="flex justify-between mt-2">
                    <p className="text-xs text-dim">Include the problem, solution and target audience for best results.</p>
                    <span className="text-xs text-dim">{idea.length}/2000</span>
                  </div>
                </div>

                {/* Example Ideas */}
                <div>
                  <p className="text-xs font-semibold flex items-center gap-1.5 mb-2.5" style={{ color: 'var(--color-text-3)' }}>
                    <Lightbulb className="w-3.5 h-3.5 text-yellow-400" />
                    Example ideas — click to use
                  </p>
                  <div className="space-y-2">
                    {examples.map((ex) => (
                      <button
                        key={ex}
                        type="button"
                        onClick={() => setIdea(ex)}
                        className="w-full text-left text-xs px-3 py-2.5 rounded-lg transition-all"
                        style={{
                          background: 'var(--color-surface-2)',
                          border: '1px solid var(--color-border)',
                          color: 'var(--color-text-2)',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={e => {
                          (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.4)'
                          ;(e.currentTarget as HTMLElement).style.color = 'var(--color-text)'
                        }}
                        onMouseLeave={e => {
                          (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-border)'
                          ;(e.currentTarget as HTMLElement).style.color = 'var(--color-text-2)'
                        }}
                      >
                        {ex}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Optional Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Industry</label>
                    <select value={industry} onChange={(e) => setIndustry(e.target.value)} className="input"
                      style={{ appearance: 'auto', background: 'rgba(255,255,255,0.05)' }}>
                      <option value="" style={{ background: '#0d1733' }}>Auto-detect</option>
                      {industries.map((i) => (
                        <option key={i} value={i} style={{ background: '#0d1733' }}>{i}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Target Audience</label>
                    <input
                      type="text"
                      value={audience}
                      onChange={(e) => setAudience(e.target.value)}
                      placeholder="e.g. SME owners, Students 18–25"
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label">Country</label>
                    <select value={country} onChange={(e) => setCountry(e.target.value)} className="input"
                      style={{ appearance: 'auto', background: 'rgba(255,255,255,0.05)' }}>
                      {['India', 'USA', 'UK', 'Singapore', 'UAE', 'Other'].map((c) => (
                        <option key={c} value={c} style={{ background: '#0d1733' }}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Estimated Budget</label>
                    <select value={budget} onChange={(e) => setBudget(e.target.value)} className="input"
                      style={{ appearance: 'auto', background: 'rgba(255,255,255,0.05)' }}>
                      <option value="" style={{ background: '#0d1733' }}>Not specified</option>
                      {budgets.map((b) => (
                        <option key={b} value={b} style={{ background: '#0d1733' }}>{b}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Error */}
                {error && (
                  <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm"
                    style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#F87171' }}>
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    {error}
                  </div>
                )}

                {/* Submit */}
                <button
                  id="generate-blueprint-btn"
                  type="submit"
                  disabled={loading || !idea.trim()}
                  className="btn-primary w-full justify-center py-4 text-base"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Launching 5 AI Agents…
                    </>
                  ) : (
                    <>
                      Generate Startup Blueprint
                      <Send className="w-4 h-4" />
                    </>
                  )}
                </button>

                <p className="text-center text-xs text-dim">
                  No sign-up required · Powered by IBM Granite (watsonx.ai) · Takes ~3–5 minutes
                </p>
              </form>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
