// VentureMind AI — Axios API Service Layer
import axios from 'axios'
import type {
  Blueprint,
  GenerateRequest,
  GenerateResponse,
  StartupStatusResponse,
} from '@/types'

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || '') + '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Startup Generation ────────────────────────────────────────────────────────

export const generateBlueprint = async (
  payload: GenerateRequest
): Promise<GenerateResponse> => {
  const { data } = await api.post<GenerateResponse>('/startups/generate', payload)
  return data
}

export const getStartupStatus = async (
  startupId: string
): Promise<StartupStatusResponse> => {
  const { data } = await api.get<StartupStatusResponse>(
    `/startups/${startupId}/status`
  )
  return data
}

export const getBlueprint = async (startupId: string): Promise<Blueprint> => {
  const { data } = await api.get<Blueprint>(`/startups/${startupId}/blueprint`)
  return data
}

export const listBlueprints = async (
  limit = 20,
  offset = 0
): Promise<{ items: any[]; total: number }> => {
  const { data } = await api.get('/startups/', { params: { limit, offset } })
  return data
}

export const stopGeneration = async (startupId: string): Promise<any> => {
  const { data } = await api.post(`/startups/${startupId}/stop`)
  return data
}

// ── Export ────────────────────────────────────────────────────────────────────

export const downloadPdf = async (startupId: string): Promise<Blob> => {
  const response = await api.get(`/export/${startupId}/pdf`, {
    responseType: 'blob',
  })
  return response.data
}

// ── WebSocket ─────────────────────────────────────────────────────────────────

export const createProgressWebSocket = (startupId: string): WebSocket => {
  const wsBase = import.meta.env.VITE_WS_URL
  if (wsBase) {
    return new WebSocket(`${wsBase}/api/v1/ws/${startupId}`)
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.hostname
  const port = import.meta.env.DEV ? '8000' : window.location.port
  const url = `${protocol}//${host}:${port}/api/v1/ws/${startupId}`
  return new WebSocket(url)
}

export default api
