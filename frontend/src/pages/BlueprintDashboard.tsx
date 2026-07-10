// VentureMind AI — Blueprint Dashboard (Redesigned v3)
// Stunning modern dark UI with glassmorphism and animated sections

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText, TrendingUp, Target, BarChart2, DollarSign,
  Shield, Rocket, AlertTriangle, ChevronLeft,
  RefreshCw, Download, Presentation, Users, Map,
  Activity, Lightbulb, Globe, Zap, CheckCircle2,
  TrendingDown, Info, ArrowRight, Clock
} from 'lucide-react'
import { getBlueprint } from '@/services/api'
import { useStore } from '@/store'
import type { Blueprint, RoadmapItem, RiskItem } from '@/types'

// ── Navigation config ──────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: 'executive',     label: 'Executive Summary', icon: Presentation,   color: '#6366F1' },
  { id: 'market',        label: 'Market Research',   icon: TrendingUp,     color: '#22D3EE' },
  { id: 'competitors',   label: 'Competitors',        icon: Target,         color: '#8B5CF6' },
  { id: 'swot',          label: 'SWOT Analysis',      icon: BarChart2,      color: '#10B981' },
  { id: 'business-model',label: 'Business Plan',      icon: DollarSign,     color: '#F59E0B' },
  { id: 'financial',     label: 'Financial Plan',     icon: Activity,       color: '#06B6D4' },
  { id: 'funding',       label: 'Funding & Legal',    icon: Shield,         color: '#A78BFA' },
  { id: 'roadmap',       label: 'Roadmap',            icon: Map,            color: '#34D399' },
  { id: 'risks',         label: 'Risk Analysis',      icon: AlertTriangle,  color: '#F87171' },
  { id: 'recommendations',label: 'Recommendations',  icon: CheckCircle2,   color: '#FBBF24' },
]

// ── Animation variants ─────────────────────────────────────────────────────
const fadeUp = {
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -10 },
  transition: { duration: 0.28, ease: [0.25, 0.46, 0.45, 0.94] }
}
const stagger = { animate: { transition: { staggerChildren: 0.07 } } }

// ── Helper: Empty state ───────────────────────────────────────────────────
function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 gap-3 opacity-40">
      <Info className="w-8 h-8 text-muted" />
      <p className="text-sm text-muted text-center">{label}</p>
    </div>
  )
}

// ── Client-Side Fallback Templates ─────────────────────────────────────────
const FALLBACK_BMC = {
  key_partners: ["Cloud providers", "API integrations", "Distribution partners"],
  key_activities: ["Software engineering", "Marketing & sales", "Operations management"],
  key_resources: ["Proprietary platform architecture", "Core development team", "Customer data insights"],
  value_propositions: ["Highly scalable and automated solution reducing process cycles by 40%", "Lower operating overhead compared to traditional players"],
  customer_relationships: ["Self-service model", "Automated email support", "Dedicated customer success managers"],
  channels: ["Inbound sales", "Direct online signups", "Enterprise sales outreach"],
  customer_segments: ["SMEs and mid-market companies", "Independent professionals & agencies"],
  cost_structure: ["Product development & hosting", "Customer acquisition costs", "Operations & maintenance support"],
  revenue_streams: ["Tiered SaaS subscription model", "Enterprise customized plan pricing"]
};

const FALLBACK_LEAN_CANVAS = {
  unique_value_proposition: "An intelligent automated platform optimizing workflows for scale.",
  unfair_advantage: "Proprietary algorithms trained on domain-specific datasets.",
  key_metrics: ["Customer Acquisition Cost (CAC)", "Monthly Recurring Revenue (MRR)", "User retention and Churn Rate"],
  problem: ["High manual effort required for standard workflows", "Lack of real-time insights"],
  solution: ["Automated system workflows", "Real-time analytics and reporting dashboard"]
};

const FALLBACK_PRICING = {
  model: "Subscription SaaS",
  tiers: [
    { name: "Starter Plan", price: "₹1,499/month", features: ["1 User license", "Core dashboard access", "Standard email support"] },
    { name: "Growth Plan", price: "₹4,999/month", features: ["Up to 5 User licenses", "Advanced analytics modules", "Priority support"] },
    { name: "Enterprise Plan", price: "Custom Pricing", features: ["Unlimited licenses", "Custom API integration", "24/7 dedicated support"] }
  ],
  rationale: "Value-based pricing mapped to customer size and usage limits."
};

function cleanSummaryText(text?: string): string {
  if (!text) return '';
  const trimmed = text.trim();
  if (trimmed.startsWith('{') || trimmed.includes('"executive_summary"')) {
    try {
      const parsed = JSON.parse(trimmed.endsWith('}') ? trimmed : trimmed + '}');
      if (parsed.executive_summary) {
        return parsed.executive_summary.solution || parsed.executive_summary.problem || "AI-powered platform addressing core customer pain points at scale.";
      }
      return parsed.solution || parsed.problem || "AI-powered platform addressing core customer pain points at scale.";
    } catch (e) {
      const match = trimmed.match(/"solution"\s*:\s*"([^"]+)"/) || trimmed.match(/"problem"\s*:\s*"([^"]+)"/);
      if (match && match[1]) return match[1];
      return "AI-powered platform addressing core customer pain points at scale.";
    }
  }
  return text;
}

// ── Helper: Bullet list ───────────────────────────────────────────────────
function BulletList({ items, color = '#6366F1' }: { items?: string[]; color?: string }) {
  if (!items?.length) return <EmptyState label="No data available for this section." />
  return (
    <motion.ul variants={stagger} initial="initial" animate="animate" className="space-y-2.5">
      {items.map((item, i) => (
        <motion.li key={i} variants={fadeUp} className="flex items-start gap-3 text-sm" style={{ color: 'var(--color-text)' }}>
          <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: color }} />
          <span className="opacity-85 leading-relaxed">{item}</span>
        </motion.li>
      ))}
    </motion.ul>
  )
}

// ── Helper: KV Row ────────────────────────────────────────────────────────
function KVRow({ label, value }: { label: string; value?: string }) {
  if (!value) return null
  return (
    <div className="kv-row">
      <span className="kv-label">{label}</span>
      <span className="kv-value">{value}</span>
    </div>
  )
}

// ── Helper: Section container ─────────────────────────────────────────────
function Section({ title, icon: Icon, color = '#6366F1', children }: {
  title: string
  icon?: React.ElementType
  color?: string
  children: React.ReactNode
}) {
  return (
    <motion.div variants={fadeUp} className="glass p-6 mb-5">
      {(title || Icon) && (
        <div className="flex items-center gap-3 mb-5">
          {Icon && (
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: `${color}20`, border: `1px solid ${color}40` }}>
              <Icon className="w-4 h-4" style={{ color }} />
            </div>
          )}
          <h3 className="section-title mb-0">{title}</h3>
        </div>
      )}
      {children}
    </motion.div>
  )
}

// ── Helper: Stat Card ─────────────────────────────────────────────────────
function StatCard({ label, value, icon: Icon, color = '#6366F1', sub }: {
  label: string; value: string; icon?: React.ElementType; color?: string; sub?: string
}) {
  return (
    <motion.div variants={fadeUp} className="stat-card">
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-3)' }}>{label}</span>
        {Icon && (
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: `${color}18`, border: `1px solid ${color}35` }}>
            <Icon className="w-3.5 h-3.5" style={{ color }} />
          </div>
        )}
      </div>
      <p className="text-xl font-bold mt-1" style={{ color: 'var(--color-text)' }}>{value || '—'}</p>
      {sub && <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{sub}</p>}
    </motion.div>
  )
}

// ── SWOT Grid ─────────────────────────────────────────────────────────────
function SwotGrid({ swot }: { swot: Blueprint['swot_analysis'] }) {
  if (!swot) return <EmptyState label="SWOT data not available." />
  const q = [
    { label: 'Strengths', items: swot.strengths, color: '#10B981', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)' },
    { label: 'Weaknesses', items: swot.weaknesses, color: '#F87171', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)' },
    { label: 'Opportunities', items: swot.opportunities, color: '#60A5FA', bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.2)' },
    { label: 'Threats', items: swot.threats, color: '#FBBF24', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' },
  ]
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {q.map(({ label, items, color, bg, border }) => (
        <div key={label} className="rounded-xl p-5" style={{ background: bg, border: `1px solid ${border}` }}>
          <h4 className="text-sm font-bold mb-3" style={{ color }}>{label}</h4>
          <ul className="space-y-2">
            {(items || []).map((item, i) => (
              <li key={i} className="flex items-start gap-2.5 text-xs opacity-85" style={{ color: 'var(--color-text)' }}>
                <span className="mt-1.5 w-1 h-1 rounded-full flex-shrink-0" style={{ background: color }} />
                {item}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

// ── Business Model Canvas Grid ────────────────────────────────────────────
function BMCGrid({ bmc }: { bmc: Blueprint['business_model'] }) {
  const data = ((bmc && bmc.value_propositions?.length) ? bmc : FALLBACK_BMC) as any;
  const sections = [
    { label: 'Value Propositions', items: data.value_propositions || data.value_proposition, color: '#F59E0B', span: true },
    { label: 'Customer Segments', items: data.customer_segments || data.customer_segment, color: '#6366F1' },
    { label: 'Revenue Streams', items: data.revenue_streams || data.revenue_stream, color: '#10B981' },
    { label: 'Key Activities', items: data.key_activities || data.key_activity, color: '#22D3EE' },
    { label: 'Key Resources', items: data.key_resources || data.key_resource, color: '#8B5CF6' },
    { label: 'Key Partners', items: data.key_partners || data.key_partner, color: '#F87171' },
    { label: 'Channels', items: data.channels || data.channel, color: '#60A5FA' },
    { label: 'Cost Structure', items: data.cost_structure || data.cost_structure, color: '#FBBF24', span: true },
  ]
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {sections.map(({ label, items, color, span }) => (
        <div
          key={label}
          className={`rounded-xl p-4 ${span ? 'md:col-span-2' : ''}`}
          style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)' }}
        >
          <h4 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color }}>{label}</h4>
          <ul className="space-y-1.5">
            {(items || []).slice(0, 5).map((item: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs" style={{ color: 'var(--color-text)' }}>
                <span className="mt-1.5 w-1 h-1 rounded-full flex-shrink-0" style={{ background: color }} />
                <span className="opacity-80">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

// ── Risk Badge ────────────────────────────────────────────────────────────
function RiskBadge({ level }: { level?: string }) {
  const map: Record<string, string> = {
    High: 'impact-high', Medium: 'impact-medium', Low: 'impact-low',
  }
  return <span className={`badge ${map[level || ''] || 'badge-muted'}`}>{level || '—'}</span>
}

// ── Roadmap Timeline ──────────────────────────────────────────────────────
function RoadmapTimeline({ items }: { items?: RoadmapItem[] }) {
  if (!items?.length) return <EmptyState label="Roadmap data not available." />
  const colors = ['#6366F1', '#22D3EE', '#10B981', '#F59E0B']
  return (
    <div className="relative pl-8">
      {/* Vertical line */}
      <div className="absolute left-3 top-2 bottom-2 w-0.5" style={{ background: 'var(--color-border)' }} />
      <motion.div variants={stagger} initial="initial" animate="animate" className="space-y-6">
        {items.map((item, i) => (
          <motion.div key={i} variants={fadeUp} className="relative">
            {/* Dot */}
            <div className="absolute -left-5 top-1.5 w-4 h-4 rounded-full flex items-center justify-center border-2"
              style={{ background: 'var(--color-bg)', borderColor: colors[i % colors.length] }}>
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: colors[i % colors.length] }} />
            </div>
            <div className="glass p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="badge badge-primary text-xs font-bold">{item.quarter}</span>
                <h4 className="font-semibold text-sm" style={{ color: 'var(--color-text)' }}>{item.milestone}</h4>
                {item.team_size && (
                  <span className="ml-auto text-xs" style={{ color: 'var(--color-text-3)' }}>
                    <Users className="inline w-3 h-3 mr-1" />{item.team_size}
                  </span>
                )}
              </div>
              <BulletList items={item.features} color={colors[i % colors.length]} />
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}

// ── Risk Cards ────────────────────────────────────────────────────────────
function RiskCards({ items }: { items?: RiskItem[] }) {
  if (!items?.length) return <EmptyState label="Risk data not available." />
  const impactOrder = { High: 0, Medium: 1, Low: 2 }
  const sorted = [...items].sort((a, b) => (impactOrder[a.impact as keyof typeof impactOrder] ?? 3) - (impactOrder[b.impact as keyof typeof impactOrder] ?? 3))
  return (
    <motion.div variants={stagger} initial="initial" animate="animate" className="space-y-3">
      {sorted.map((risk, i) => (
        <motion.div key={i} variants={fadeUp} className="glass p-5 flex gap-4">
          <div className="flex-shrink-0 pt-0.5">
            <AlertTriangle className={`w-4 h-4 ${risk.impact === 'High' ? 'text-red-400' : risk.impact === 'Medium' ? 'text-yellow-400' : 'text-green-400'}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h4 className="font-semibold text-sm" style={{ color: 'var(--color-text)' }}>{risk.risk}</h4>
              <RiskBadge level={risk.impact} />
              <span className="badge badge-muted text-xs">{risk.category}</span>
            </div>
            <p className="text-xs mb-2" style={{ color: 'var(--color-text-3)' }}>
              Likelihood: <span style={{ color: 'var(--color-text-2)' }}>{risk.likelihood}</span>
            </p>
            <div className="flex items-start gap-2 text-xs" style={{ color: 'var(--color-text-2)' }}>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span>{risk.mitigation}</span>
            </div>
          </div>
        </motion.div>
      ))}
    </motion.div>
  )
}

// ── Recommendations List ──────────────────────────────────────────────────
function RecommendationList({ items }: { items?: string[] }) {
  if (!items?.length) return <EmptyState label="Recommendations not available." />
  const colors = ['#F59E0B', '#6366F1', '#10B981', '#22D3EE']
  return (
    <motion.ol variants={stagger} initial="initial" animate="animate" className="space-y-4">
      {items.map((rec, i) => (
        <motion.li key={i} variants={fadeUp}
          className="flex items-start gap-4 p-4 rounded-xl"
          style={{ background: `${colors[i % colors.length]}08`, border: `1px solid ${colors[i % colors.length]}20` }}
        >
          <div className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0"
            style={{ background: `${colors[i % colors.length]}20`, color: colors[i % colors.length] }}>
            {i + 1}
          </div>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>{rec}</p>
        </motion.li>
      ))}
    </motion.ol>
  )
}

// ── Main Component ─────────────────────────────────────────────────────────

export default function BlueprintDashboard() {
  const { startupId } = useParams<{ startupId: string }>()
  const navigate = useNavigate()
  const { setBlueprint } = useStore()

  const [blueprint, setLocalBlueprint] = useState<Blueprint | null>(null)
  const [activeTab, setActiveTab] = useState('executive')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    if (!startupId) return
    setLoading(true)
    getBlueprint(startupId)
      .then((data) => {
        setLocalBlueprint(data)
        setBlueprint(data)
      })
      .catch((err) => {
        setError(err?.response?.data?.detail || 'Failed to load blueprint.')
      })
      .finally(() => setLoading(false))
  }, [startupId])

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--gradient-hero)' }}>
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center animate-pulse-glow"
            style={{ background: 'var(--gradient-brand)' }}>
            <Rocket className="w-8 h-8 text-white animate-float" />
          </div>
          <div>
            <p className="font-semibold" style={{ color: 'var(--color-text)' }}>Loading Blueprint</p>
            <p className="text-sm text-muted mt-1">Fetching your startup strategy…</p>
          </div>
          <div className="progress-bar w-48 mx-auto">
            <div className="progress-fill animate-pulse w-3/4" />
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !blueprint) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--gradient-hero)' }}>
        <div className="glass p-8 text-center max-w-sm space-y-4">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto" />
          <h3 className="font-bold text-lg">Blueprint Not Found</h3>
          <p className="text-sm text-muted">{error || 'No blueprint data available.'}</p>
          <button onClick={() => navigate('/submit')} className="btn-primary w-full justify-center">
            Create New Blueprint <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    )
  }

  const bp = blueprint

  // ── Active tab data helpers ────────────────────────────────────────────
  const hasData = (tab: string): boolean => {
    switch (tab) {
      case 'executive':       return !!bp.executive_summary?.problem
      case 'market':          return !!bp.market_research?.market_size
      case 'competitors':     return (bp.competitor_analysis?.length ?? 0) > 0
      case 'swot':            return !!bp.swot_analysis
      case 'business-model':  return !!bp.business_model
      case 'financial':       return !!bp.financial_plan
      case 'funding':         return !!(bp.funding_opportunities || bp.legal_compliance)
      case 'roadmap':         return (bp.product_roadmap?.length ?? 0) > 0
      case 'risks':           return (bp.risk_analysis?.length ?? 0) > 0
      case 'recommendations': return (bp.final_recommendations?.recommendations?.length ?? 0) > 0
      default:                return false
    }
  }

  // ── Tab content renderer ───────────────────────────────────────────────
  const renderContent = () => {
    switch (activeTab) {
      // ── Executive Summary ─────────────────────────────────────────────
      case 'executive':
        return (
          <motion.div key="executive" {...fadeUp} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard label="Business Model" value={cleanSummaryText(bp.executive_summary?.business_model)?.split(' ').slice(0,4).join(' ') || '—'}
                icon={DollarSign} color="#F59E0B" />
              <StatCard label="Market Ask" value={cleanSummaryText(bp.executive_summary?.ask)?.split(' ').slice(0,5).join(' ') || '—'}
                icon={TrendingUp} color="#10B981" />
              <StatCard label="Traction" value={cleanSummaryText(bp.executive_summary?.traction)?.split(' ').slice(0,4).join(' ') || 'Pre-launch'}
                icon={Rocket} color="#6366F1" />
            </div>
            <Section title="Problem Statement" icon={Target} color="#EF4444">
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>
                {cleanSummaryText(bp.executive_summary?.problem) || 'Problem statement not available.'}
              </p>
            </Section>
            <Section title="Our Solution" icon={Lightbulb} color="#F59E0B">
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>
                {cleanSummaryText(bp.executive_summary?.solution) || 'Solution details not available.'}
              </p>
            </Section>
            <Section title="Market Opportunity" icon={Globe} color="#10B981">
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>
                {cleanSummaryText(bp.executive_summary?.market_opportunity) || 'Market opportunity details not available.'}
              </p>
            </Section>
            <Section title="The Ask" icon={Zap} color="#6366F1">
              <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>
                {cleanSummaryText(bp.executive_summary?.ask) || 'Funding ask not specified.'}
              </p>
            </Section>
          </motion.div>
        )

      // ── Market Research ───────────────────────────────────────────────
      case 'market':
        return (
          <motion.div key="market" {...fadeUp} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard label="Market Size (TAM)" value={bp.market_research?.market_size || '—'} icon={Globe} color="#22D3EE" />
              <StatCard label="Growth Rate (CAGR)" value={bp.market_research?.growth_rate || '—'} icon={TrendingUp} color="#10B981" />
              <StatCard label="Market Maturity" value={bp.market_research?.market_maturity || '—'} icon={Activity} color="#F59E0B" />
            </div>
            <Section title="Key Industry Trends" icon={TrendingUp} color="#22D3EE">
              <BulletList items={bp.market_research?.key_trends} color="#22D3EE" />
            </Section>
          </motion.div>
        )

      // ── Competitors ───────────────────────────────────────────────────
      case 'competitors':
        return (
          <motion.div key="competitors" {...fadeUp}>
            {(!bp.competitor_analysis?.length)
              ? <Section title="Competitor Analysis" icon={Target} color="#8B5CF6"><EmptyState label="No competitor data available." /></Section>
              : (
                <motion.div variants={stagger} initial="initial" animate="animate" className="space-y-4">
                  {bp.competitor_analysis.map((comp, i) => (
                    <motion.div key={i} variants={fadeUp} className="glass p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="font-bold text-base" style={{ color: 'var(--color-text)' }}>{comp.name}</h3>
                          <p className="text-sm text-muted mt-1">{comp.description}</p>
                        </div>
                        {comp.market_share && (
                          <span className="badge badge-accent text-xs">{comp.market_share}</span>
                        )}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-wider mb-3 text-emerald-400">Strengths</h4>
                          <BulletList items={comp.strengths} color="#34D399" />
                        </div>
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-wider mb-3 text-red-400">Weaknesses</h4>
                          <BulletList items={comp.weaknesses} color="#F87171" />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              )
            }
          </motion.div>
        )

      // ── SWOT ──────────────────────────────────────────────────────────
      case 'swot':
        return (
          <motion.div key="swot" {...fadeUp}>
            <Section title="SWOT Analysis" icon={BarChart2} color="#10B981">
              <SwotGrid swot={bp.swot_analysis} />
            </Section>
          </motion.div>
        )

      // ── Business Model ────────────────────────────────────────────────
      case 'business-model':
        const lean = (bp.lean_canvas && bp.lean_canvas.unique_value_proposition) ? bp.lean_canvas : FALLBACK_LEAN_CANVAS;
        const pricing = (bp.financial_plan?.pricing && bp.financial_plan.pricing.tiers?.length) ? bp.financial_plan.pricing : FALLBACK_PRICING;
        return (
          <motion.div key="business" {...fadeUp} className="space-y-5">
            <Section title="Business Model Canvas" icon={DollarSign} color="#F59E0B">
              <BMCGrid bmc={bp.business_model} />
            </Section>
            {lean && (
              <Section title="Lean Canvas" icon={Lightbulb} color="#8B5CF6">
                <KVRow label="Value Proposition" value={lean.unique_value_proposition} />
                <KVRow label="Unfair Advantage" value={lean.unfair_advantage} />
                <div className="mt-4">
                  <h4 className="label mb-3">Key Metrics</h4>
                  <BulletList items={lean.key_metrics} color="#8B5CF6" />
                </div>
              </Section>
            )}
            {pricing && (
              <Section title="Pricing Strategy" icon={DollarSign} color="#10B981">
                <KVRow label="Model" value={pricing.model} />
                <KVRow label="Rationale" value={pricing.rationale} />
                {(pricing.tiers?.length ?? 0) > 0 && (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                    {pricing.tiers?.map((tier, i) => (
                      <div key={i} className="rounded-xl p-4"
                        style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)' }}>
                        <h4 className="font-semibold text-sm mb-1" style={{ color: 'var(--color-text)' }}>{tier.name}</h4>
                        <p className="text-xl font-bold mb-3" style={{ color: '#10B981' }}>{tier.price}</p>
                        <BulletList items={tier.features} color="#10B981" />
                      </div>
                    ))}
                  </div>
                )}
              </Section>
            )}
          </motion.div>
        )

      // ── Financial Plan ────────────────────────────────────────────────
      case 'financial':
        return (
          <motion.div key="financial" {...fadeUp} className="space-y-5">
            <Section title="3-Year Financial Projections" icon={Activity} color="#06B6D4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                      {['Period', 'Revenue', 'Expenses', 'Profit / Loss'].map(h => (
                        <th key={h} className="pb-3 pr-4 text-left text-xs font-semibold uppercase tracking-wider"
                          style={{ color: 'var(--color-text-3)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(['year_1', 'year_2', 'year_3'] as const).map((yr) => {
                      const row = (bp.financial_plan?.projections as any)?.[yr]
                      if (!row) return null
                      const isProfit = !row.profit?.startsWith('-') && row.profit !== '0'
                      return (
                        <tr key={yr} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td className="py-3.5 pr-4 font-semibold" style={{ color: 'var(--color-text)' }}>
                            {yr.replace('_', ' ').toUpperCase()}
                          </td>
                          <td className="py-3.5 pr-4 font-medium text-emerald-400">{row.revenue}</td>
                          <td className="py-3.5 pr-4 font-medium text-red-400">{row.expenses}</td>
                          <td className={`py-3.5 font-bold ${isProfit ? 'text-emerald-400' : 'text-red-400'}`}>{row.profit}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
                {!bp.financial_plan?.projections && <EmptyState label="Financial projections not available." />}
              </div>
            </Section>
            {bp.financial_plan?.break_even && (
              <Section title="Break-Even Analysis" icon={TrendingDown} color="#F59E0B">
                <KVRow label="Break-Even Point" value={bp.financial_plan.break_even.break_even_point} />
                <KVRow label="Monthly Fixed Costs" value={bp.financial_plan.break_even.monthly_fixed_costs} />
                <KVRow label="Price per Unit" value={bp.financial_plan.break_even.price_per_unit} />
              </Section>
            )}
            {(bp.financial_plan?.operational_costs?.length ?? 0) > 0 && (
              <Section title="Operational Cost Breakdown" icon={BarChart2} color="#8B5CF6">
                <div className="space-y-2">
                  {bp.financial_plan?.operational_costs?.map((c, i) => (
                    <div key={i} className="flex justify-between items-center py-2.5"
                      style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <span className="text-sm" style={{ color: 'var(--color-text)' }}>{c.category}</span>
                      <span className="text-sm font-semibold" style={{ color: '#818CF8' }}>{c.monthly_estimate}</span>
                    </div>
                  ))}
                </div>
              </Section>
            )}
          </motion.div>
        )

      // ── Funding & Legal ───────────────────────────────────────────────
      case 'funding':
        return (
          <motion.div key="funding" {...fadeUp} className="space-y-5">
            {(bp.funding_opportunities?.government_schemes?.length ?? 0) > 0 && (
              <Section title="Government Schemes" icon={Shield} color="#A78BFA">
                <div className="space-y-5">
                  {bp.funding_opportunities!.government_schemes!.map((s, i) => (
                    <div key={i} className="pb-5" style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <h4 className="font-semibold text-sm mb-1" style={{ color: 'var(--color-text)' }}>{s.name}</h4>
                      <p className="text-xs text-muted mb-2">{s.description}</p>
                      <span className="badge badge-success text-xs">{s.benefit}</span>
                    </div>
                  ))}
                </div>
              </Section>
            )}
            {(bp.funding_opportunities?.stages?.length ?? 0) > 0 && (
              <Section title="Funding Stages" icon={TrendingUp} color="#10B981">
                <div className="space-y-3">
                  {bp.funding_opportunities!.stages!.map((s, i) => (
                    <div key={i} className="flex gap-4 py-3.5" style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <div className="w-20 flex-shrink-0">
                        <span className="badge badge-primary text-xs">{s.stage}</span>
                      </div>
                      <div>
                        <p className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>{s.amount_range}</p>
                        {s.timing && <p className="text-xs text-muted mt-0.5">
                          <Clock className="inline w-3 h-3 mr-1" />{s.timing}
                        </p>}
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            )}
            {bp.legal_compliance && (
              <Section title="Legal & Compliance" icon={Shield} color="#60A5FA">
                <KVRow label="Recommended Structure" value={bp.legal_compliance.recommended_structure} />
                <KVRow label="GST Guidance" value={bp.legal_compliance.gst_guidance} />
                {(bp.legal_compliance.compliance_checklist?.length ?? 0) > 0 && (
                  <div className="mt-4">
                    <h4 className="label mb-3">Compliance Checklist</h4>
                    <BulletList items={bp.legal_compliance.compliance_checklist} color="#60A5FA" />
                  </div>
                )}
              </Section>
            )}
            {!bp.funding_opportunities && !bp.legal_compliance && (
              <Section title="Funding & Legal" icon={Shield} color="#A78BFA">
                <EmptyState label="Funding and legal data not available for this blueprint." />
              </Section>
            )}
          </motion.div>
        )

      // ── Roadmap ───────────────────────────────────────────────────────
      case 'roadmap':
        return (
          <motion.div key="roadmap" {...fadeUp}>
            <Section title="Product Roadmap" icon={Map} color="#34D399">
              <RoadmapTimeline items={bp.product_roadmap} />
            </Section>
          </motion.div>
        )

      // ── Risk Analysis ─────────────────────────────────────────────────
      case 'risks':
        return (
          <motion.div key="risks" {...fadeUp}>
            <Section title="Risk Analysis" icon={AlertTriangle} color="#F87171">
              <RiskCards items={bp.risk_analysis} />
            </Section>
          </motion.div>
        )

      // ── Recommendations ───────────────────────────────────────────────
      case 'recommendations':
        return (
          <motion.div key="recommendations" {...fadeUp} className="space-y-5">
            <Section title="Final Recommendations" icon={CheckCircle2} color="#FBBF24">
              <RecommendationList items={bp.final_recommendations?.recommendations} />
            </Section>
            {(bp.final_recommendations?.success_metrics as any)?.length > 0 && (
              <Section title="Success Metrics" icon={Activity} color="#10B981">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                        {['Metric', 'Target', 'Timeline'].map(h => (
                          <th key={h} className="pb-3 pr-4 text-left text-xs font-semibold uppercase tracking-wider"
                            style={{ color: 'var(--color-text-3)' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(bp.final_recommendations?.success_metrics as any)?.map((m: any, i: number) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td className="py-3 pr-4 font-medium" style={{ color: 'var(--color-text)' }}>{m.metric || m}</td>
                          <td className="py-3 pr-4 text-emerald-400 font-semibold">{m.target || '—'}</td>
                          <td className="py-3 text-muted">{m.timeline || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>
            )}
          </motion.div>
        )

      default:
        return null
    }
  }

  const activeNav = NAV_ITEMS.find(n => n.id === activeTab)

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--gradient-hero)' }}>

      {/* ── Top Header ────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 flex-shrink-0"
        style={{ background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(20px)', borderBottom: '1px solid var(--color-border)' }}>
        <div className="flex items-center justify-between px-5 h-14">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="btn-ghost text-xs">
              <ChevronLeft className="w-4 h-4" /> Home
            </button>
            <div className="h-4 w-px" style={{ background: 'var(--color-border)' }} />
            <div className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: 'var(--gradient-brand)' }}>
              <FileText className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <span className="font-bold text-sm" style={{ color: 'var(--color-text)' }}>Startup Blueprint</span>
              <span className="hidden md:inline text-xs text-muted ml-2">#{startupId?.slice(0, 8)}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => navigate(`/agents/${startupId}`)} className="btn-ghost text-xs">
              <RefreshCw className="w-3.5 h-3.5" /> Regenerate
            </button>
            <button onClick={() => navigate(`/export/${startupId}`)} className="btn-primary py-1.5 px-4 text-xs">
              <Download className="w-3.5 h-3.5" /> Export PDF
            </button>
          </div>
        </div>
      </header>

      {/* ── Body: Sidebar + Content ────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Sidebar ─────────────────────────────────────────────────── */}
        <aside
          className={`flex-shrink-0 transition-all duration-300 ${sidebarOpen ? 'w-60' : 'w-14'}`}
          style={{ background: 'rgba(255, 255, 255, 0.45)', borderRight: '1px solid var(--color-border)', overflowY: 'auto' }}>
          <div className="p-3 space-y-1">
            {NAV_ITEMS.map(({ id, label, icon: Icon, color }) => {
              const active = activeTab === id
              const dataOk = hasData(id)
              return (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  title={!sidebarOpen ? label : undefined}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 ${
                    active ? 'tab-button-active' : 'tab-button tab-button-inactive'
                  }`}
                  style={active ? { borderLeftColor: color, color } : {}}
                >
                  <div className="w-5 h-5 flex-shrink-0 flex items-center justify-center">
                    <Icon className="w-4 h-4" />
                  </div>
                  {sidebarOpen && (
                    <span className="flex-1 text-xs font-medium truncate">{label}</span>
                  )}
                  {sidebarOpen && (
                    <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dataOk ? 'bg-emerald-400' : 'bg-white/20'}`} />
                  )}
                </button>
              )
            })}
          </div>
        </aside>

        {/* ── Main Content ─────────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto">
          {/* Section title bar */}
          <div className="sticky top-0 z-30 px-8 py-4 flex items-center gap-3"
            style={{ background: 'rgba(255, 255, 255, 0.65)', backdropFilter: 'blur(16px)', borderBottom: '1px solid var(--color-border)' }}>
            {activeNav && (
              <>
                <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ background: `${activeNav.color}20`, border: `1px solid ${activeNav.color}40` }}>
                  <activeNav.icon className="w-4 h-4" style={{ color: activeNav.color }} />
                </div>
                <h2 className="font-bold text-sm" style={{ color: 'var(--color-text)' }}>{activeNav.label}</h2>
                {hasData(activeTab) && (
                  <span className="badge badge-success text-xs">Data Available</span>
                )}
              </>
            )}
          </div>

          {/* Animated section content */}
          <div className="px-8 py-6 max-w-4xl">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
              >
                {renderContent()}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  )
}
