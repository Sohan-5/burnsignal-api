"use client"

import {
  Area,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { type TimelinePoint, formatCurrency } from "@/lib/burnsignal"

interface ChartRow {
  date: string
  actual: number | null
  forecast: number | null
  bandLow: number | null
  bandRange: number | null
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const row: ChartRow = payload[0].payload
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-medium text-popover-foreground">
        {new Date(label).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
      </p>
      {row.actual != null && (
        <p className="text-muted-foreground">
          Actual: <span className="font-semibold text-foreground">{formatCurrency(row.actual)}</span>
        </p>
      )}
      {row.forecast != null && (
        <p className="text-muted-foreground">
          Forecast: <span className="font-semibold text-foreground">{formatCurrency(row.forecast)}</span>
        </p>
      )}
    </div>
  )
}

export function BurnTimelineChart({ timeline }: { timeline: TimelinePoint[] }) {
  const data: ChartRow[] = timeline.map((p) => ({
    date: p.date,
    actual: p.actual,
    forecast: p.forecast,
    bandLow: p.band ? p.band[0] : null,
    bandRange: p.band ? p.band[1] - p.band[0] : null,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Burn Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <defs>
                <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
                tickFormatter={(v) => new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                minTickGap={32}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={false}
                width={48}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<ChartTooltip />} />
              {/* Confidence band: invisible base + visible range stacked on top */}
              <Area
                dataKey="bandLow"
                stackId="band"
                stroke="none"
                fill="transparent"
                isAnimationActive={false}
                connectNulls
              />
              <Area
                dataKey="bandRange"
                stackId="band"
                stroke="none"
                fill="var(--muted)"
                fillOpacity={0.6}
                isAnimationActive={false}
                connectNulls
              />
              <Area
                dataKey="actual"
                stroke="var(--chart-1)"
                strokeWidth={2}
                fill="url(#actualFill)"
                connectNulls
                dot={false}
              />
              <Line
                dataKey="forecast"
                stroke="var(--chart-3)"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                connectNulls
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-3 rounded-sm bg-[var(--chart-1)]" /> Actual
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-3 rounded-sm bg-[var(--chart-3)]" /> Forecast
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-3 rounded-sm bg-muted" /> Confidence band
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
