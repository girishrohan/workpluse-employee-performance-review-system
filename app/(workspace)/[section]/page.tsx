import { notFound } from "next/navigation";
import { WorkspaceView, type WorkspaceSection } from "@/components/workspace-view";

const sections = new Set<WorkspaceSection>(["employees", "cycles", "assessments"]);

export default async function SectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  if (!sections.has(section as WorkspaceSection)) notFound();
  return <WorkspaceView section={section as WorkspaceSection} />;
}
