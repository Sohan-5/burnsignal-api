import { AlertTriangle, CheckCircle2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { type Forecast, formatDate } from "@/lib/burnsignal"

export function ForecastCard({ forecast }: { forecast: Forecast }) {
  const hasBreach = forecast.predicted_breach != null
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Forecast</CardTitle>
          <Badge variant="outline">{forecast.tier}</Badge>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div
          className={`flex items-start gap-3 rounded-lg border p-3 ${
            hasBreach ? "border-destructive/40 bg-destructive/10" : "border-border bg-muted/50"
          }`}
        >
          {hasBreach ? (
            <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" aria-hidden="true" />
          ) : (
            <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-foreground" aria-hidden="true" />
          )}
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-semibold text-foreground">
              {hasBreach ? "Budget breach predicted" : "No breach predicted"}
            </span>
            <span className="text-xs text-muted-foreground">
              {hasBreach ? `Estimated breach on ${formatDate(forecast.predicted_breach as string)}` : "On track within budget"}
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Confidence</span>
          <span className="text-2xl font-bold tabular-nums text-foreground">{forecast.confidence}%</span>
        </div>
      </CardContent>
    </Card>
  )
}
