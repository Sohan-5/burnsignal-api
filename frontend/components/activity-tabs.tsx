import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { type TimeEntry, formatCurrency, formatDate } from "@/lib/burnsignal"

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-10 text-center">
      <p className="text-sm font-medium text-foreground">Nothing here yet</p>
      <p className="text-xs text-muted-foreground">{message}</p>
    </div>
  )
}

export function ActivityTabs({ timeEntries }: { timeEntries: TimeEntry[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="time">
          <TabsList>
            <TabsTrigger value="time">Time Entries</TabsTrigger>
            <TabsTrigger value="contractors">Contractors</TabsTrigger>
            <TabsTrigger value="tools">Tool Costs</TabsTrigger>
          </TabsList>

          <TabsContent value="time" className="mt-4">
            {timeEntries.length === 0 ? (
              <EmptyState message="Time entries logged against this project will appear here." />
            ) : (
              <ul className="flex flex-col divide-y divide-border">
                {timeEntries.map((entry) => (
                  <li key={entry.id} className="flex items-center justify-between gap-4 py-3">
                    <div className="flex flex-col gap-0.5">
                      <span className="text-sm font-medium text-foreground">{entry.notes || "Time entry"}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(entry.entry_date)} &middot; {entry.hours} hrs
                      </span>
                    </div>
                    <span className="text-sm font-semibold tabular-nums text-foreground">
                      {formatCurrency(entry.cost)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </TabsContent>

          <TabsContent value="contractors" className="mt-4">
            <EmptyState message="Contractor spend is not tracked yet." />
          </TabsContent>

          <TabsContent value="tools" className="mt-4">
            <EmptyState message="Tool and software costs are not tracked yet." />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
