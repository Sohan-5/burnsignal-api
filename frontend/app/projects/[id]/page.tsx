import { ProjectDetailClient } from "@/components/project-detail-client"

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return (
    <main className="min-h-screen bg-background">
      <ProjectDetailClient id={id} />
    </main>
  )
}
