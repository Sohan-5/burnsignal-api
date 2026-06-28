"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function BurnRatioGauge({ ratio }: { ratio: number }) {
  const pct = Math.min(Math.max(ratio, 0), 1)
  const size = 160
  const stroke = 14
  const radius = (size - stroke) / 2
  const circumference = Math.PI * radius // semicircle
  const dash = circumference * pct

  let color = "var(--chart-1)"
  if (pct >= 0.9) color = "var(--destructive)"
  else if (pct >= 0.7) color = "var(--chart-3)"

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Burn Ratio</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div className="relative" style={{ width: size, height: size / 2 + 8 }}>
          <svg width={size} height={size / 2 + 8} viewBox={`0 0 ${size} ${size / 2 + 8}`}>
            <path
              d={`M ${stroke / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - stroke / 2} ${size / 2}`}
              fill="none"
              stroke="var(--muted)"
              strokeWidth={stroke}
              strokeLinecap="round"
            />
            <path
              d={`M ${stroke / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - stroke / 2} ${size / 2}`}
              fill="none"
              stroke={color}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circumference}`}
            />
          </svg>
          <div className="absolute inset-x-0 bottom-0 flex flex-col items-center">
            <span className="text-3xl font-bold tabular-nums text-foreground">{Math.round(pct * 100)}%</span>
            <span className="text-xs text-muted-foreground">of budget</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
