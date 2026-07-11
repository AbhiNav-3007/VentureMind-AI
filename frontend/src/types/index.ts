// VentureMind AI — TypeScript type definitions

export interface GenerateRequest {
  idea: string
  industry?: string
  target_audience?: string
  country?: string
  budget?: string
}

export interface GenerateResponse {
  startup_id: string
  status: string
  message: string
}

export interface AgentStatus {
  agent_name: string
  agent_role: string
  status: 'pending' | 'running' | 'done' | 'failed'
  current_task: string | null
  progress: number
  execution_time_seconds: number | null
  output_summary: string | null
}

export interface StartupStatusResponse {
  id: string
  status: 'pending' | 'running' | 'done' | 'failed'
  idea_text: string
  created_at: string
  updated_at: string
  agents: AgentStatus[]
  industry?: string | null
  target_audience?: string | null
  country?: string | null
  budget?: string | null
}

export interface MarketOverview {
  market_size: string
  growth_rate: string
  key_trends: string[]
  market_maturity: string
}

export interface Competitor {
  name: string
  description: string
  strengths: string[]
  weaknesses: string[]
  market_share: string
}

export interface SwotAnalysis {
  strengths: string[]
  weaknesses: string[]
  opportunities: string[]
  threats: string[]
}

export interface CustomerPersona {
  name: string
  age_range: string
  occupation: string
  pain_points: string[]
  goals: string[]
  preferred_channels: string[]
}

export interface BusinessModelCanvas {
  key_partners: string[]
  key_activities: string[]
  key_resources: string[]
  value_propositions: string[]
  customer_relationships: string[]
  channels: string[]
  customer_segments: string[]
  cost_structure: string[]
  revenue_streams: string[]
}

export interface LeanCanvas {
  problem: string[]
  solution: string[]
  unique_value_proposition: string
  unfair_advantage: string
  customer_segments: string[]
  key_metrics: string[]
  channels: string[]
  cost_structure: string[]
  revenue_streams: string[]
}

export interface PricingTier {
  name: string
  price: string
  features: string[]
}

export interface PricingStrategy {
  model: string
  tiers: PricingTier[]
  rationale: string
}

export interface FinancialProjection {
  revenue: string
  expenses: string
  profit: string
}

export interface FinancialPlan {
  projections?: {
    year_1?: FinancialProjection
    year_2?: FinancialProjection
    year_3?: FinancialProjection
  }
  operational_costs?: Array<{ category: string; monthly_estimate: string }>
  break_even?: {
    break_even_point: string
    monthly_fixed_costs: string
    variable_cost_per_unit: string
    price_per_unit: string
  }
  pricing?: PricingStrategy
}

export interface FundingOpportunities {
  stages?: Array<{ stage: string; amount_range: string; investors: string[]; timing: string }>
  government_schemes?: Array<{
    name: string
    description: string
    eligibility: string
    benefit: string
    application_url: string
  }>
  incubators?: Array<{
    name: string
    focus_area: string
    location: string
    benefits: string
    application_info: string
  }>
}

export interface LegalCompliance {
  recommended_structure: string
  registrations: Array<{ name: string; description: string; timeline: string }>
  gst_guidance: string
  ip_recommendations: string[]
  compliance_checklist: string[]
}

export interface RoadmapItem {
  quarter: string
  milestone: string
  features: string[]
  team_size: string
}

export interface RiskItem {
  risk: string
  category: string
  impact: string
  likelihood: string
  mitigation: string
}

export interface ExecutiveSummary {
  problem: string
  solution: string
  market_opportunity: string
  business_model: string
  traction: string
  ask: string
}

export interface InvestorPitch {
  headline: string
  elevator_pitch: string
  value_proposition: string
  why_now: string
  why_us: string
  financials_snapshot: string
  call_to_action: string
}

export interface Blueprint {
  id: string
  startup_id: string
  executive_summary?: ExecutiveSummary
  market_research?: MarketOverview
  competitor_analysis?: Competitor[]
  swot_analysis?: SwotAnalysis
  customer_personas?: CustomerPersona[]
  business_model?: BusinessModelCanvas
  lean_canvas?: LeanCanvas
  financial_plan?: FinancialPlan
  funding_opportunities?: FundingOpportunities
  legal_compliance?: LegalCompliance
  marketing_strategy?: { launch_phases?: any[]; distribution_channels?: string[]; growth_hacks?: string[]; partnerships?: string[] }
  product_roadmap?: RoadmapItem[]
  risk_analysis?: RiskItem[]
  investor_pitch?: InvestorPitch
  final_recommendations?: { recommendations?: string[]; success_metrics?: string[] }
  pdf_url?: string
  created_at: string
}

export interface WsProgressEvent {
  event: 'progress' | 'complete' | 'error'
  startup_id: string
  current_agent?: string
  progress?: number
  agent_statuses?: Record<string, string>
  error?: string
}
