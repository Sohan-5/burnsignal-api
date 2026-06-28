import { Layers } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type { Phase } from "@/lib/burnsignal"

export function PhaseProgress({ phases }: { phases: Phase[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Phase Progress</CardTitle>
      </CardHeader>
      <CardContent>
        {phases.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
            <Layers className="size-8 text-muted-foreground" aria-hidden="true" />
            <p className="text-sm font-medium text-foreground">No phases defined</p>
            <p className="text-xs text-muted-foreground">Phases will appear here once the project plan is set up.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {phases.map((phase, i) => (
              <div key={phase.id ?? i} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-foreground">{phase.name ?? `Phase ${i + 1}`}</span>
                  <span className="text-xs text-muted-foreground tabular-nums">{phase.progress ?? 0}%</span>
                </div>
                <Progress value={phase.progress ?? 0} />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
