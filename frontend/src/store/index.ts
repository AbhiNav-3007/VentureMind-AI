// VentureMind AI — Zustand Global State Store
import { create } from 'zustand'
import type { AgentStatus, Blueprint, WsProgressEvent } from '@/types'

interface VentureMindStore {
  // Current workflow
  startupId: string | null
  workflowStatus: 'idle' | 'pending' | 'running' | 'done' | 'failed'
  agents: AgentStatus[]
  overallProgress: number
  currentAgent: string

  // Blueprint data
  blueprint: Blueprint | null

  // Actions
  setStartupId: (id: string) => void
  setWorkflowStatus: (status: VentureMindStore['workflowStatus']) => void
  setAgents: (agents: AgentStatus[]) => void
  setBlueprint: (blueprint: Blueprint) => void
  applyWsEvent: (event: WsProgressEvent) => void
  reset: () => void
}

export const useStore = create<VentureMindStore>((set) => ({
  startupId: null,
  workflowStatus: 'idle',
  agents: [],
  overallProgress: 0,
  currentAgent: '',
  blueprint: null,

  setStartupId: (id) => set({ startupId: id }),
  setWorkflowStatus: (status) => set({ workflowStatus: status }),
  setAgents: (agents) => set({ agents }),
  setBlueprint: (blueprint) => set({ blueprint }),

  applyWsEvent: (event) =>
    set((state) => {
      if (event.event === 'progress') {
        return {
          overallProgress: event.progress ?? state.overallProgress,
          currentAgent: event.current_agent ?? state.currentAgent,
          workflowStatus: 'running',
        }
      }
      if (event.event === 'complete') {
        return { workflowStatus: 'done', overallProgress: 100 }
      }
      if (event.event === 'error') {
        return { workflowStatus: 'failed' }
      }
      return {}
    }),

  reset: () =>
    set({
      startupId: null,
      workflowStatus: 'idle',
      agents: [],
      overallProgress: 0,
      currentAgent: '',
      blueprint: null,
    }),
}))
