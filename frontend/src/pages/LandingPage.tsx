// VentureMind AI — Landing Page (Redesigned v3)
// Stunning dark glassmorphism hero with animated elements

import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Brain, TrendingUp, FileText, DollarSign, Shield, Rocket,
  ChevronRight, Cpu, BarChart2, CheckCircle2, History,
  ArrowRight, Zap, Globe, Target,
  Activity, Users,
} from 'lucide-react'
import { listBlueprints } from '@/services/api'

// ── Data ────────────────────────────────────────────────────────────────────
const features = [
  { icon: Brain,     title: 'AI Orchestration',    desc: '5 autonomous agents powered by IBM Granite and LangGraph for end-to-end startup consulting.', color: '#6366F1' },
  { icon: TrendingUp,title: 'Market Intelligence', desc: 'Real-time market research, competitor analysis, SWOT, and customer persona mapping.', color: '#22D3EE' },
  { icon: DollarSign,title: 'Financial Planning',  desc: 'Business Model Canvas, revenue projections, break-even analysis, and pricing strategy.', color: '#F59E0B' },
  { icon: Shield,    title: 'Legal & Funding',     desc: 'Government schemes, Startup India programs, MSME grants, legal compliance checklists.', color: '#A78BFA' },
  { icon: Rocket,    title: 'GTM Strategy',        desc: 'Go-to-market strategy, product roadmap, launch timeline, and risk mitigation plan.', color: '#34D399' },
  { icon: FileText,  title: 'Investor Pitch',      desc: 'Professional executive summary and investor deck ready for seed/Series-A fundraising.', color: '#F87171' },
]

const workflow = [
  { step: '01', label: 'Submit Idea',      desc: 'Enter your startup concept in plain language — just one sentence.', color: '#6366F1' },
  { step: '02', label: 'Planner Agent',    desc: 'AI analyses domain, challenges, and creates an execution plan.', color: '#22D3EE' },
  { step: '03', label: 'Market Agent',     desc: 'Researches market size, competitors, and customer personas.', color: '#10B981' },
  { step: '04', label: 'Business Agent',   desc: 'Builds financial model, pricing, and revenue projections.', color: '#F59E0B' },
  { step: '05', label: 'Funding Agent',    desc: 'Finds grants, incubators, angel investors, and legal requirements.', color: '#A78BFA' },
  { step: '06', label: 'Strategy Agent',   desc: 'Compiles GTM, roadmap, investor pitch, and final blueprint.', color: '#F87171' },
]

const stats = [
  { value: '5',      label: 'AI Agents',       icon: Brain },
  { value: '10+',   label: 'Report Sections',  icon: FileText },
  { value: '< 5m',  label: 'Generation Time',  icon: Zap },
  { value: '100%',  label: 'IBM Cloud Native', icon: Globe },
]

const techStack = [
  { name: 'IBM Granite',    detail: 'watsonx.ai LLM' },
  { name: 'Watson Discovery', detail: 'RAG Knowledge Base' },
  { name: 'LangGraph',      detail: 'Agentic Workflow' },
  { name: 'FastAPI',        detail: 'Backend API' },
  { name: 'PostgreSQL',     detail: 'Data Persistence' },
  { name: 'ChromaDB',       detail: 'Vector Search' },
  { name: 'React + Vite',   detail: 'Frontend' },
  { name: 'IBM Orchestrate', detail: 'Agent Coordination' },
]

// ── Animation variants ─────────────────────────────────────────────────────
const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
}

// ── Main Component ──────────────────────────────────────────────────────────
export default function LandingPage() {
  const navigate = useNavigate()
  const [blueprints, setBlueprints] = useState<any[]>([])
  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listBlueprints(10, 0)
      .then((data) => setBlueprints(data.items ?? []))
      .catch(console.error)
  }, [])

  return (
    <div className="min-h-screen" style={{ background: 'var(--gradient-hero)' }}>

      {/* ── Ambient glow orbs ─────────────────────────────────────────── */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[10%] w-[600px] h-[600px] rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #6366F1 0%, transparent 70%)', filter: 'blur(80px)' }} />
        <div className="absolute top-[40%] right-[-5%] w-[500px] h-[500px] rounded-full opacity-08"
          style={{ background: 'radial-gradient(circle, #22D3EE 0%, transparent 70%)', filter: 'blur(80px)' }} />
        <div className="absolute bottom-[10%] left-[30%] w-[400px] h-[400px] rounded-full opacity-05"
          style={{ background: 'radial-gradient(circle, #A78BFA 0%, transparent 70%)', filter: 'blur(80px)' }} />
      </div>

      {/* ── Navbar ──────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50"
        style={{ background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(20px)', borderBottom: '1px solid var(--color-border)' }}>
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center animate-pulse-glow"
              style={{ background: 'var(--gradient-brand)' }}>
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-sm gradient-text">VentureMind AI</span>
          </div>
          <div className="flex items-center gap-2">
            <a href="#features" className="btn-ghost text-xs hidden md:flex">Features</a>
            <a href="#how-it-works" className="btn-ghost text-xs hidden md:flex">How It Works</a>
            <button onClick={() => navigate('/submit')} className="btn-primary py-2 px-4 text-xs">
              Generate Blueprint <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section ref={heroRef} className="relative z-10 pt-36 pb-24 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <motion.div {...fadeUp}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8 text-xs font-semibold"
              style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)', color: '#818CF8' }}>
              <Cpu className="w-3.5 h-3.5" />
              Powered by IBM Granite · watsonx.ai · LangGraph
              <span className="badge badge-success ml-2 text-xs">Live</span>
            </div>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold leading-tight mb-6"
            style={{ color: 'var(--color-text)' }}
          >
            Turn Your Idea Into a{' '}
            <span className="gradient-text">Complete Startup Blueprint</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg text-muted max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            5 autonomous AI agents perform market research, financial planning, legal compliance,
            funding discovery, and strategy generation — delivering a full investor-ready blueprint in minutes.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button
              onClick={() => navigate('/submit')}
              className="btn-primary text-base px-8 py-3.5"
            >
              Generate My Blueprint
              <ChevronRight className="w-4 h-4" />
            </button>
            <a href="#how-it-works" className="btn-secondary text-base px-8 py-3.5">
              See How It Works
            </a>
          </motion.div>
        </div>
      </section>

      {/* ── Stats ───────────────────────────────────────────────────────── */}
      <section className="relative z-10 py-10 px-6" style={{ borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6"
          >
            {stats.map(({ value, label, icon: Icon }, i) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="text-center"
              >
                <div className="text-4xl font-bold gradient-text mb-1">{value}</div>
                <div className="text-sm text-muted flex items-center justify-center gap-1.5">
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────────────── */}
      <section id="features" className="relative z-10 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="badge badge-primary mb-4 text-xs">Everything Included</div>
            <h2 className="text-4xl font-bold mb-4" style={{ color: 'var(--color-text)' }}>
              Everything Your Startup Needs
            </h2>
            <p className="text-muted max-w-xl mx-auto">One platform, five AI experts, zero manual research.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map(({ icon: Icon, title, desc, color }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
                whileHover={{ y: -4 }}
                className="glass-hover p-6 cursor-default"
              >
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4"
                  style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
                  <Icon className="w-5 h-5" style={{ color }} />
                </div>
                <h3 className="font-bold text-base mb-2" style={{ color: 'var(--color-text)' }}>{title}</h3>
                <p className="text-sm text-muted leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────────────────────────── */}
      <section id="how-it-works" className="relative z-10 py-24 px-6"
        style={{ background: 'rgba(255,255,255,0.02)', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}>
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="badge badge-accent mb-4 text-xs">6-Step Process</div>
            <h2 className="text-4xl font-bold mb-4" style={{ color: 'var(--color-text)' }}>How VentureMind AI Works</h2>
            <p className="text-muted">From idea to investor-ready blueprint in 6 autonomous steps.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {workflow.map(({ step, label, desc, color }, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
                className="glass p-6 relative overflow-hidden"
              >
                <div className="absolute top-4 right-4 text-5xl font-black opacity-[0.06]"
                  style={{ color, lineHeight: 1 }}>{step}</div>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-4 text-sm font-bold"
                  style={{ background: `${color}18`, border: `1px solid ${color}35`, color }}>
                  {step}
                </div>
                <h3 className="font-bold text-sm mb-2" style={{ color: 'var(--color-text)' }}>{label}</h3>
                <p className="text-xs text-muted leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Tech Stack ─────────────────────────────────────────────────── */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <div className="badge badge-muted mb-4 text-xs">Tech Stack</div>
            <h2 className="text-4xl font-bold mb-4" style={{ color: 'var(--color-text)' }}>
              Built on IBM Cloud Technologies
            </h2>
            <p className="text-muted mb-12">Enterprise-grade AI infrastructure for startup consulting.</p>
            <div className="flex flex-wrap justify-center gap-3">
              {techStack.map(({ name, detail }) => (
                <div
                  key={name}
                  className="glass-hover px-4 py-2.5 cursor-default"
                  style={{ borderRadius: '10px' }}
                >
                  <div className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>{name}</div>
                  <div className="text-xs text-dim mt-0.5">{detail}</div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Recent Blueprints ─────────────────────────────────────────── */}
      {blueprints.length > 0 && (
        <section className="relative z-10 py-20 px-6"
          style={{ background: 'rgba(255,255,255,0.02)', borderTop: '1px solid var(--color-border)' }}>
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex items-center gap-3 mb-8"
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)' }}>
                <History className="w-4 h-4 text-primary" />
              </div>
              <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>Recent Blueprints</h2>
            </motion.div>
            <div className="space-y-3">
              {blueprints.map((bp, i) => (
                <motion.div
                  key={bp.id}
                  initial={{ opacity: 0, x: -16 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => navigate(bp.status === 'done' ? `/blueprint/${bp.id}` : `/agents/${bp.id}`)}
                  className="glass-hover p-5 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="min-w-0 flex-1">
                    <h4 className="font-semibold text-sm truncate" style={{ color: 'var(--color-text)' }}>{bp.idea_text}</h4>
                    <p className="text-xs text-muted mt-1 flex items-center gap-2 flex-wrap">
                      {bp.industry && <span className="badge badge-primary text-xs">{bp.industry}</span>}
                      {bp.country && <span>{bp.country}</span>}
                      <span>· {new Date(bp.created_at).toLocaleDateString()}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-3 self-end sm:self-auto">
                    <span className={`status-${bp.status}`}>{bp.status}</span>
                    <ChevronRight className="w-4 h-4 text-dim" />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section className="relative z-10 py-28 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass p-14 relative overflow-hidden"
          >
            {/* Glow background */}
            <div className="absolute inset-0 opacity-20 pointer-events-none"
              style={{ background: 'radial-gradient(ellipse at 50% 100%, #6366F1 0%, transparent 60%)' }} />
            <div className="relative z-10">
              <Rocket className="w-10 h-10 mx-auto mb-5" style={{ color: '#F59E0B' }} />
              <h2 className="text-4xl font-bold mb-4" style={{ color: 'var(--color-text)' }}>
                Ready to Build Your Startup Blueprint?
              </h2>
              <p className="text-muted mb-8 max-w-xl mx-auto">
                Enter your idea in one sentence. Let 5 AI agents handle the rest. No sign-up required.
              </p>
              <button
                onClick={() => navigate('/submit')}
                className="btn-primary text-base px-10 py-4 mx-auto"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="relative z-10 py-8 px-6 text-center text-xs text-dim"
        style={{ borderTop: '1px solid var(--color-border)' }}>
        <p>VentureMind AI · IBM SkillsBuild Problem Statement No. 20 · Powered by IBM Granite & watsonx.ai</p>
      </footer>
    </div>
  )
}
