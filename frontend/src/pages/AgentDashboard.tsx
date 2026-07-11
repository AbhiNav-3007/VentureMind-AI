// VentureMind AI — Agent Execution Dashboard (v2)
// True Agentic AI display with:
// - Live tool indicator (IBM Granite / Watson Discovery / RAG / FinCalc)
// - Reasoning Timeline panel per agent
// - Validation gate display
// - Retry event indication
// - Real-time output summaries
import { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain, TrendingUp, DollarSign, Shield, Rocket,
  CheckCircle2, Loader2, Clock, XCircle, ChevronRight,
  Cpu, Network, Database, Search, Calculator, Zap,
  RefreshCw, AlertCircle, ChevronDown, ChevronUp, Info,
  ChevronLeft
} from 'lucide-react'
import { getStartupStatus, createProgressWebSocket, stopGeneration } from '@/services/api'
import { useStore } from '@/store'
import type { WsProgressEvent } from '@/types'

// ── Types ──────────────────────────────────────────────────────────────────────
interface ToolEvent {
  tool_name: string
  tool_type: string
  ibm_service: string | null
  started_at: string
  finished_at: string
  duration_seconds: number
  input_summary: string
  output_summary: string
  tokens_consumed: number | null
  status: string
}

interface ReasoningStep {
  step_number: number
  description: string
  completed: boolean
  result_summary: string
}

interface AgentTimeline {
  agent_key: string
  agent_name: string
  agent_role: string
  agent_identity: string
  status: string
  current_task: string
  current_tool: string
  progress: number
  tool_events: ToolEvent[]
  reasoning_steps: ReasoningStep[]
  output_summary: string
  output_keys: string[]
  passed_to_next: string
  granite_calls: number
  discovery_calls: number
  rag_calls: number
  total_tokens: number
  retry_count: number
  input_received: Record<string, any>
  started_at: string
  finished_at: string
  total_duration_seconds: number
}

// ── Constants ──────────────────────────────────────────────────────────────────
const AGENT_CONFIG = [
  {
    key: 'planner',
    name: 'Planner & Orchestrator',
    icon: Brain,
    color: 'text-primary',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    tools: ['IBM Granite', 'RAG Pipeline'],
  },
  {
    key: 'market',
    name: 'Market Intelligence',
    icon: TrendingUp,
    color: 'text-indigo-600',
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    tools: ['IBM Granite', 'Watson Discovery', 'RAG Pipeline'],
  },
  {
    key: 'business',
    name: 'Business & Finance',
    icon: DollarSign,
    color: 'text-secondary',
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    tools: ['IBM Granite', 'Financial Calculator'],
  },
  {
    key: 'funding',
    name: 'Funding & Legal',
    icon: Shield,
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
    tools: ['IBM Granite', 'Watson Discovery', 'RAG Pipeline'],
  },
  {
    key: 'strategy',
    name: 'Strategy & Report',
    icon: Rocket,
    color: 'text-orange-600',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    tools: ['IBM Granite'],
  },
]

const TOOL_ICONS: Record<string, any> = {
  'IBM Granite': Cpu,
  'Watson Discovery': Search,
  'RAG Pipeline': Database,
  'Financial Calculator': Calculator,
}

const TOOL_COLORS: Record<string, string> = {
  'IBM Granite': 'text-blue-600 bg-blue-50 border-blue-200',
  'Watson Discovery': 'text-indigo-600 bg-indigo-50 border-indigo-200',
  'RAG Pipeline': 'text-purple-600 bg-purple-50 border-purple-200',
  'Financial Calculator': 'text-green-600 bg-green-50 border-green-200',
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function ToolBadge({ toolName, active = false }: { toolName: string; active?: boolean }) {
  const Icon = TOOL_ICONS[toolName] || Zap
  const colorClass = TOOL_COLORS[toolName] || 'text-gray-600 bg-gray-50 border-gray-200'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-xs font-medium ${colorClass} ${active ? 'ring-1 ring-offset-1 ring-blue-300' : ''}`}>
      <Icon className="w-3 h-3" />
      {toolName}
      {active && <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />}
    </span>
  )
}

function ReasoningStepList({ steps }: { steps: ReasoningStep[] }) {
  if (!steps?.length) return null
  return (
    <div className="space-y-1.5 mt-3">
      {steps.map((step) => (
        <div key={step.step_number} className="flex items-start gap-2">
          <div className={`mt-0.5 w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 text-[9px] font-bold ${step.completed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
            {step.completed ? '✓' : step.step_number}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-dark">{step.description}</p>
            {step.completed && step.result_summary && (
              <p className="text-xs text-muted mt-0.5 truncate">{step.result_summary}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function ToolEventList({ events }: { events: ToolEvent[] }) {
  if (!events?.length) return null
  return (
    <div className="space-y-1.5 mt-3">
      {events.map((ev, i) => {
        const Icon = TOOL_ICONS[ev.tool_name] || Zap
        return (
          <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-surface border border-border text-xs">
            <Icon className="w-3.5 h-3.5 text-muted flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-dark">{ev.tool_name}</span>
                <div className="flex items-center gap-1.5">
                  {ev.ibm_service && (
                    <span className="text-primary text-[10px]">{ev.ibm_service}</span>
                  )}
                  <span className={`badge ${ev.status === 'done' ? 'status-done' : ev.status === 'failed' ? 'status-failed' : 'status-running'}`}>
                    {ev.status}
                  </span>
                </div>
              </div>
              <p className="text-muted truncate mt-0.5">{ev.output_summary || ev.input_summary}</p>
              {ev.duration_seconds > 0 && (
                <span className="text-muted">{ev.duration_seconds.toFixed(1)}s</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function AgentTimelinePanel({ timeline, agentKey }: { timeline: AgentTimeline | null; agentKey: string }) {
  const [expanded, setExpanded] = useState(false)
  const config = AGENT_CONFIG.find((a) => a.key === agentKey)
  if (!timeline || !config) return null
  const Icon = config.icon

  return (
    <div className="card border-l-4" style={{ borderLeftColor: agentKey === 'planner' ? '#3b82d4' : agentKey === 'market' ? '#6366f1' : agentKey === 'business' ? '#7c5cd8' : agentKey === 'funding' ? '#16a34a' : '#ea580c' }}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center`}>
            <Icon className={`w-4 h-4 ${config.color}`} />
          </div>
          <div>
            <h4 className="font-semibold text-dark text-sm">{timeline.agent_name}</h4>
            <p className="text-xs text-muted">{timeline.agent_identity?.slice(0, 80)}…</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={timeline.status === 'done' ? 'status-done' : timeline.status === 'running' ? 'status-running' : 'status-pending'}>
            {timeline.status}
          </span>
          {timeline.total_duration_seconds > 0 && (
            <span className="text-xs text-muted">{timeline.total_duration_seconds.toFixed(1)}s</span>
          )}
          <button onClick={() => setExpanded(!expanded)} className="text-muted hover:text-dark">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Tool badges */}
      <div className="flex flex-wrap gap-1.5 mt-2">
        {config.tools.map((tool) => (
          <ToolBadge
            key={tool}
            toolName={tool}
            active={timeline.current_tool === tool && timeline.status === 'running'}
          />
        ))}
      </div>

      {/* Stats row */}
      <div className="flex gap-4 mt-2 text-xs text-muted">
        {timeline.granite_calls > 0 && <span>Granite calls: {timeline.granite_calls}</span>}
        {timeline.discovery_calls > 0 && <span>Discovery calls: {timeline.discovery_calls}</span>}
        {timeline.rag_calls > 0 && <span>RAG calls: {timeline.rag_calls}</span>}
        {timeline.total_tokens > 0 && <span>~{timeline.total_tokens.toLocaleString()} tokens</span>}
      </div>

      {/* Current task */}
      {timeline.current_task && timeline.status === 'running' && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-primary">
          <Loader2 className="w-3 h-3 animate-spin" />
          {timeline.current_task}
        </div>
      )}

      {/* Output summary */}
      {timeline.output_summary && (
        <div className="mt-2 p-2 rounded-lg bg-green-50 border border-green-100 text-xs text-green-800">
          {timeline.output_summary}
        </div>
      )}

      {/* Passed to next */}
      {timeline.passed_to_next && (
        <div className="mt-1.5 text-xs text-muted flex items-center gap-1">
          <ChevronRight className="w-3 h-3" />
          {timeline.passed_to_next}
        </div>
      )}

      {/* Expanded: reasoning steps + tool events */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 border-t border-border pt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h5 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                  Reasoning Chain
                </h5>
                <ReasoningStepList steps={timeline.reasoning_steps} />
              </div>
              <div>
                <h5 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                  Tool Calls
                </h5>
                <ToolEventList events={timeline.tool_events} />
              </div>
            </div>
            {Object.keys(timeline.input_received || {}).length > 0 && (
              <div className="mt-3 border-t border-border pt-3">
                <h5 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                  Input Received
                </h5>
                <div className="grid grid-cols-2 gap-1.5">
                  {Object.entries(timeline.input_received).map(([k, v]) => (
                    <div key={k} className="text-xs">
                      <span className="text-muted">{k}: </span>
                      <span className="text-dark">{String(v).slice(0, 60)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function AgentDashboard() {
  const { startupId } = useParams<{ startupId: string }>()
  const navigate = useNavigate()
  const { workflowStatus, setWorkflowStatus, applyWsEvent } = useStore()

  const [overallProgress, setOverallProgress] = useState(0)
  const [currentAgent, setCurrentAgent] = useState('Planner & Orchestrator Agent')
  const [currentTool, setCurrentTool] = useState('')
  const [agentStatuses, setAgentStatuses] = useState<Record<string, string>>({})
  const [agentTimelines, setAgentTimelines] = useState<Record<string, AgentTimeline>>({})
  const [validation, setValidation] = useState<any>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [logs, setLogs] = useState<string[]>([
    '⟳ Initializing VentureMind AI Agentic System…',
    '⟳ Connecting to IBM Cloud services…',
  ])
  const [activeTimelineKey, setActiveTimelineKey] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [...prev.slice(-59), `[${new Date().toLocaleTimeString()}] ${msg}`])
  }, [])

  const handleStop = async () => {
    if (!startupId) return
    try {
      await stopGeneration(startupId)
      addLog('⚠ Stopping agents... Generation cancelled.')
      setWorkflowStatus('failed')
      if (wsRef.current) wsRef.current.close()
    } catch (err) {
      console.error('Failed to stop generation:', err)
    }
  }

  // Poll initial status
  useEffect(() => {
    if (!startupId) return
    getStartupStatus(startupId).then((data) => {
      setWorkflowStatus(data.status as any)
    }).catch(console.error)
  }, [startupId])

  // WebSocket connection
  useEffect(() => {
    if (!startupId) return
    const ws = createProgressWebSocket(startupId)
    wsRef.current = ws

    ws.onopen = () => addLog('✓ Connected to live agent execution stream')

    ws.onmessage = (ev) => {
      try {
        const event = JSON.parse(ev.data) as WsProgressEvent & {
          current_tool?: string
          active_timeline?: AgentTimeline
          validation?: any
          retry_count?: number
        }
        applyWsEvent(event)

        if (event.event === 'progress') {
          setOverallProgress(event.progress ?? 0)
          setCurrentAgent(event.current_agent ?? '')
          setCurrentTool((event as any).current_tool ?? '')
          setAgentStatuses(event.agent_statuses ?? {})
          if ((event as any).retry_count !== undefined) setRetryCount((event as any).retry_count)
          if ((event as any).validation) setValidation((event as any).validation)

          // Merge timeline for current agent
          const tl = (event as any).active_timeline
          if (tl?.agent_key) {
            setAgentTimelines((prev) => ({ ...prev, [tl.agent_key]: tl }))
            setActiveTimelineKey(tl.agent_key)
          }

          // Compose log message
          const toolMsg = (event as any).current_tool ? ` → ${(event as any).current_tool}` : ''
          addLog(`${event.current_agent}${toolMsg} (${Math.round(event.progress ?? 0)}%)`)
        }

        if (event.event === 'complete') {
          setOverallProgress(100)
          setWorkflowStatus('done')
          if ((event as any).validation) setValidation((event as any).validation)
          addLog(`✓ All agents complete! Quality score: ${(event as any).validation?.quality_score ?? 'N/A'}/10`)
        }

        if (event.event === 'error') {
          addLog(`✗ Error: ${event.error}`)
          setWorkflowStatus('failed')
        }
      } catch {}
    }

    ws.onerror = () => addLog('⚠ WebSocket error — retrying via polling…')
    ws.onclose = () => addLog('⊘ Stream disconnected')

    return () => ws.close()
  }, [startupId])

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])



  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Loader2 className="w-4 h-4 text-primary animate-spin" />
      case 'done':    return <CheckCircle2 className="w-4 h-4 text-green-600" />
      case 'failed':  return <XCircle className="w-4 h-4 text-red-500" />
      case 'skipped': return <Info className="w-4 h-4 text-gray-400" />
      default:        return <Clock className="w-4 h-4 text-gray-300" />
    }
  }

  return (
    <div className="min-h-screen pb-10" style={{ background: 'var(--gradient-hero)' }}>
      {/* Header */}
      <div className="sticky top-0 z-40" style={{ background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(20px)', borderBottom: '1px solid var(--color-border)' }}>
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (wsRef.current) wsRef.current.close()
                navigate('/')
              }}
              className="btn-secondary text-xs py-1.5 px-3"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Network className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-dark text-sm">Agent Execution Dashboard</h1>
              <p className="text-xs text-muted">Startup ID: {startupId?.slice(0, 8)}…</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {currentTool && (
              <div className="hidden md:flex items-center gap-1.5 text-xs text-muted">
                <span>Running tool:</span>
                <ToolBadge toolName={currentTool} active />
              </div>
            )}
            {retryCount > 0 && (
              <div className="flex items-center gap-1 text-xs text-orange-600">
                <RefreshCw className="w-3 h-3" />
                Retry pass {retryCount}
              </div>
            )}
            {(workflowStatus === 'running' || workflowStatus === 'pending') && (
              <button
                onClick={handleStop}
                className="bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-1.5 transition-all"
              >
                <XCircle className="w-3.5 h-3.5" />
                Stop Generation
              </button>
            )}
            {workflowStatus === 'done' && (
              <button onClick={() => navigate(`/blueprint/${startupId}`)} className="btn-primary text-sm py-1.5 px-4 flex items-center gap-1">
                View Blueprint <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* ── LEFT: Agent Cards + Progress ──────────────────────────────── */}
        <div className="xl:col-span-1 space-y-4">
          {/* Overall progress */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm font-semibold text-dark">Overall Progress</p>
                <p className="text-xs text-muted truncate max-w-[200px]">{currentAgent}</p>
              </div>
              <span className="text-2xl font-bold text-primary">{Math.round(overallProgress)}%</span>
            </div>
            <div className="progress-bar">
              <motion.div className="progress-fill" animate={{ width: `${overallProgress}%` }} transition={{ duration: 0.5 }} />
            </div>
            {workflowStatus === 'done' && (
              <div className="mt-4 space-y-2 animate-fade-in">
                <p className="text-xs text-green-600 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> All agents completed successfully!
                </p>
                <button
                  onClick={() => navigate(`/blueprint/${startupId}`)}
                  className="w-full btn-primary text-sm py-2 px-4 flex items-center justify-center gap-1 bg-green-600 hover:bg-green-700 text-white border-none"
                >
                  View Generated Blueprint <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Agent status cards */}
          {AGENT_CONFIG.map((agent, idx) => {
            const status = agentStatuses[agent.key] || 'pending'
            const tl = agentTimelines[agent.key]
            const Icon = agent.icon
            const isActive = currentAgent.toLowerCase().includes(agent.key) || status === 'running'

            return (
              <motion.div
                key={agent.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => setActiveTimelineKey(agent.key)}
                className={`card cursor-pointer transition-all duration-200 ${isActive ? 'border-primary/40 shadow-md' : ''} ${activeTimelineKey === agent.key ? 'border-primary bg-blue-50/30' : ''}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2.5">
                    <div className={`w-8 h-8 rounded-lg ${agent.bg} flex items-center justify-center`}>
                      <Icon className={`w-4 h-4 ${agent.color}`} />
                    </div>
                    <div>
                      <p className="font-semibold text-dark text-xs">{agent.name}</p>
                      <p className="text-[10px] text-muted">{agent.tools.join(' · ')}</p>
                    </div>
                  </div>
                  {getStatusIcon(status)}
                </div>

                {/* Tool indicators */}
                <div className="flex flex-wrap gap-1 mb-2">
                  {agent.tools.map((tool) => (
                    <ToolBadge
                      key={tool}
                      toolName={tool}
                      active={isActive && currentTool === tool}
                    />
                  ))}
                </div>

                {/* Current task */}
                {tl?.current_task && status === 'running' && (
                  <p className="text-[10px] text-primary truncate">{tl.current_task}</p>
                )}

                {/* Output summary */}
                {tl?.output_summary && status === 'done' && (
                  <p className="text-[10px] text-green-700 mt-1 line-clamp-2">{tl.output_summary}</p>
                )}

                <div className="flex items-center justify-between mt-2">
                  <span className={
                    status === 'done' ? 'status-done' :
                    status === 'running' ? 'status-running' :
                    status === 'failed' ? 'status-failed' :
                    status === 'skipped' ? 'badge bg-gray-100 text-gray-500' :
                    'status-pending'
                  }>
                    {status}
                  </span>
                  {tl?.total_duration_seconds > 0 && (
                    <span className="text-[10px] text-muted">{tl.total_duration_seconds.toFixed(1)}s</span>
                  )}
                </div>
              </motion.div>
            )
          })}

          {/* Validation card */}
          {validation && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`card ${validation.validation_passed ? 'border-green-200 bg-green-50/30' : 'border-orange-200 bg-orange-50/30'}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center">
                    <Brain className="w-3.5 h-3.5 text-muted" />
                  </div>
                  <span className="font-semibold text-dark text-xs">Planner Validation</span>
                </div>
                {validation.validation_passed
                  ? <CheckCircle2 className="w-4 h-4 text-green-600" />
                  : <AlertCircle className="w-4 h-4 text-orange-600" />}
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-muted">Quality Score:</span>
                <span className="font-bold text-dark">{validation.quality_score ?? '—'}/10</span>
              </div>
              {validation.validation_summary && (
                <p className="text-[10px] text-muted mt-1">{validation.validation_summary}</p>
              )}
              {(validation.issues_found ?? []).slice(0, 2).map((issue: string, i: number) => (
                <p key={i} className="text-[10px] text-orange-700 mt-1">⚠ {issue}</p>
              ))}
            </motion.div>
          )}
        </div>

        {/* ── RIGHT: Reasoning Timeline Panel ──────────────────────────────── */}
        <div className="xl:col-span-2 space-y-4">
          {/* Timeline header */}
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-dark">Agent Reasoning Timeline</h2>
            <p className="text-xs text-muted">Click an agent card to inspect its reasoning chain</p>
          </div>

          {/* Active timeline expanded view */}
          {activeTimelineKey && agentTimelines[activeTimelineKey] && (
            <AgentTimelinePanel
              timeline={agentTimelines[activeTimelineKey]}
              agentKey={activeTimelineKey}
            />
          )}

          {/* All completed timelines */}
          <div className="space-y-3">
            {AGENT_CONFIG.filter((a) => agentTimelines[a.key] && a.key !== activeTimelineKey).map((agent) => (
              <AgentTimelinePanel
                key={agent.key}
                timeline={agentTimelines[agent.key]}
                agentKey={agent.key}
              />
            ))}
          </div>

          {/* Live terminal log */}
          <div className="card">
            <h3 className="font-semibold text-dark text-sm mb-3 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-muted" />
              Live Execution Log
              <span className="ml-auto text-xs text-muted font-normal">{logs.length} events</span>
            </h3>
            <div className="bg-gray-950 rounded-xl p-4 h-52 overflow-y-auto font-mono text-xs">
              {logs.map((log, i) => (
                <div
                  key={i}
                  className={`leading-6 ${
                    log.includes('✓') ? 'text-green-400' :
                    log.includes('✗') || log.includes('Error') ? 'text-red-400' :
                    log.includes('⚠') ? 'text-yellow-400' :
                    'text-gray-300'
                  }`}
                >
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

          {/* IBM Services Used */}
          <div className="card">
            <h3 className="font-semibold text-dark text-sm mb-3">IBM Cloud Services Active</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { name: 'IBM Granite', service: 'watsonx.ai', icon: Cpu, active: true },
                { name: 'Watson Discovery', service: 'RAG Source', icon: Search, active: agentStatuses.market === 'running' || agentStatuses.funding === 'running' },
                { name: 'IBM COS', service: 'Object Storage', icon: Database, active: workflowStatus === 'done' },
                { name: 'LangGraph', service: 'Orchestration', icon: Network, active: workflowStatus === 'running' || workflowStatus === 'pending' },
              ].map(({ name, service, icon: Icon, active }) => (
                <div key={name} className={`rounded-xl border p-3 text-center transition-all ${active ? 'border-primary/30 bg-blue-50/50' : 'border-border bg-surface'}`}>
                  <Icon className={`w-5 h-5 mx-auto mb-1.5 ${active ? 'text-primary' : 'text-muted'}`} />
                  <p className={`text-xs font-semibold ${active ? 'text-dark' : 'text-muted'}`}>{name}</p>
                  <p className="text-[10px] text-muted">{service}</p>
                  {active && <div className="w-1.5 h-1.5 rounded-full bg-green-500 mx-auto mt-1" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
