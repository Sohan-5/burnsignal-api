// Forecast history + signal breakdown
// Endpoint: GET /api/orgs/{org_id}/projects/{project_id}/forecast/history
export default function ForecastHistory({ params }: { params: { project_id: string } }) {
  return <div>Forecast history for {params.project_id}</div>
}
