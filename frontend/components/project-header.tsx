import { Badge } from "@/components/ui/badge"
import { type ProjectDetail, formatCurrency, formatDate } from "@/lib/burnsignal"

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
      <span className="text-sm font-semibold text-foreground">{value}</span>
    </div>
  )
}

export function ProjectHeader({ project }: { project: ProjectDetail }) {
  const isActive = project.status === "active"
  return (
    <header className="flex flex-col gap-6 rounded-xl border border-border bg-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-balance text-foreground">{project.name}</h1>
            <Badge variant={isActive ? "default" : "secondary"} className="capitalize">
              {project.status}
            </Badge>
            <Badge variant="outline" className="capitalize">
              {project.duration_type}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {formatDate(project.start_date)} &ndash; {formatDate(project.end_date)}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-3xl font-bold tabular-nums text-foreground">{project.days_remaining}</span>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">days remaining</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 border-t border-border pt-6 sm:grid-cols-4">
        <StatItem label="Total Budget" value={formatCurrency(project.total_budget)} />
        <StatItem label="Total Spent" value={formatCurrency(project.total_spent)} />
        <StatItem label="Burn Ratio" value={`${Math.round(project.burn_ratio * 100)}%`} />
        <StatItem label="Forecast Tier" value={project.forecast.tier} />
      </div>
    </header>
  )
}
