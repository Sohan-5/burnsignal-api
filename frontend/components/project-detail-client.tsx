"use client"

import { useEffect, useState } from "react"
import { Loader2, SearchX } from "lucide-react"
import { type ProjectDetail, NotFoundError, fetchProjectDetail } from "@/lib/burnsignal"
import { ProjectHeader } from "@/components/project-header"
import { BurnTimelineChart } from "@/components/burn-timeline-chart"
import { ForecastCard } from "@/components/forecast-card"
import { BurnRatioGauge } from "@/components/burn-ratio-gauge"
import { PressureSignalsPanel } from "@/components/pressure-signals-panel"
import { PhaseProgress } from "@/components/phase-progress"
import { ActivityTabs } from "@/components/activity-tabs"

function LoadingState() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3" role="status" aria-live="polite">
      <Loader2 className="size-8 animate-spin text-muted-foreground" aria-hidden="true" />
      <span className="text-sm text-muted-foreground">Loading project…</span>
    </div>
  )
}

function NotFoundState() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <SearchX className="size-10 text-muted-foreground" aria-hidden="true" />
      <h1 className="text-xl font-semibold text-foreground">Project not found</h1>
      <p className="max-w-sm text-sm text-muted-foreground">
        We couldn&apos;t find a project with that ID. It may have been removed or the link is incorrect.
      </p>
    </div>
  )
}

export function ProjectDetailClient({ id }: { id: string }) {
  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [status, setStatus] = useState<"loading" | "loaded" | "notfound" | "error">("loading")

  useEffect(() => {
    let active = true
    setStatus("loading")

    fetchProjectDetail(id)
      .then((data) => {
        if (!active) return
        setProject(data)
        setStatus("loaded")
      })
      .catch((err) => {
        if (!active) return
        console.log("[v0] project detail fetch error:", err?.message)
        setStatus(err instanceof NotFoundError ? "notfound" : "error")
      })

    return () => {
      active = false
    }
  }, [id])

  if (status === "loading") return <LoadingState />
  if (status === "notfound") return <NotFoundState />
  if (status === "error" || !project) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-2 text-center">
        <h1 className="text-xl font-semibold text-foreground">Something went wrong</h1>
        <p className="text-sm text-muted-foreground">We couldn&apos;t load this project. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6">
      <ProjectHeader project={project} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <BurnTimelineChart timeline={project.timeline} />
        </div>
        <div className="flex flex-col gap-6">
          <ForecastCard forecast={project.forecast} />
          <BurnRatioGauge ratio={project.burn_ratio} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PressureSignalsPanel signals={project.pressure_signals} />
        <PhaseProgress phases={project.phases} />
      </div>

      <ActivityTabs timeEntries={project.time_entries} />
    </div>
  )
}
