export type DurationType = 'sprint' | 'medium' | 'program'
export type ProjectStatus = 'active' | 'completed' | 'archived'
export type SignalSource = 'manual' | 'trello' | 'jira' | 'github' | 'linear'
export type ForecastTier = 1 | 2 | '3a' | '3b'

export interface Project {
  id: string
  name: string
  status: ProjectStatus
  duration_type: DurationType
  start_date: string
  end_date: string
  department_id: string
}

export interface Budget {
  id: string
  project_id: string
  total_amount: number
  currency: string
  headcount_pct: number
  tools_pct: number
  contractors_pct: number
  contingency_pct: number
}

export interface TimeEntry {
  id: string
  project_id: string
  user_id: string
  entry_date: string
  hours: number
  hourly_rate: number
  source: SignalSource
  notes?: string
}

export interface ForecastResult {
  tier: ForecastTier
  baseline_forecast: number
  pressure_multiplier: number
  final_forecast: number
  predicted_breach_date: string
  confidence_score: number
  signal_values: Record<string, number>
  snapshot_at: string
}

export interface PressureSignal {
  name: string
  value: number
  weight: number
  label: string
}
