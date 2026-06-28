import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { PressureSignal } from "@/lib/burnsignal"

function intensityColor(intensity: number): string {
  if (intensity >= 70) return "var(--destructive)"
  if (intensity >= 40) return "var(--chart-3)"
  return "var(--chart-1)"
}

export function PressureSignalsPanel({ signals }: { signals: PressureSignal[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Pressure Signals</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {signals.map((signal) => (
          <div key={signal.name} className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-foreground">{signal.name}</span>
              <span className="text-sm font-semibold tabular-nums text-foreground">{signal.intensity}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${Math.min(signal.intensity, 100)}%`, backgroundColor: intensityColor(signal.intensity) }}
              />
            </div>
            <span className="text-xs text-muted-foreground">{signal.detail}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
