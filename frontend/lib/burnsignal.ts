export const API = "https://burnsignal-api-production.up.railway.app"
export const ORG_ID = "fb82c0b3-2153-4393-8169-8169ea907d73"

export interface Forecast {
  predicted_breach: string | null
  confidence: number
  tier: string
}

export interface PressureSignal {
  name: string
  intensity: number
  detail: string
}

export interface TimelinePoint {
  date: string
  actual: number | null
  forecast: number | null
  band: [number, number] | null
}

export interface Phase {
  id?: string
  name?: string
  status?: string
  progress?: number
}

export interface TimeEntry {
  id: string
  hours: number
  cost: number
  entry_date: string
  notes: string
}

export interface ProjectDetail {
  id: string
  name: string
  status: string
  duration_type: string
  start_date: string
  end_date: string
  days_remaining: number
  total_budget: number
  total_spent: number
  burn_ratio: number
  forecast: Forecast
  pressure_signals: PressureSignal[]
  timeline: TimelinePoint[]
  phases: Phase[]
  time_entries: TimeEntry[]
}

export class NotFoundError extends Error {}

export async function fetchProjectDetail(id: string): Promise<ProjectDetail> {
  const res = await fetch(`${API}/api/orgs/${ORG_ID}/projects/${id}`, {
    cache: "no-store",
  })

  if (res.status === 404) {
    throw new NotFoundError("Project not found")
  }

  if (!res.ok) {
    throw new Error(`Failed to load project (${res.status})`)
  }

  return res.json()
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value))
}
